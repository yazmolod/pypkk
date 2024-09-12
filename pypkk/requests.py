from contextlib import contextmanager, asynccontextmanager
from typing import Optional
import asyncio

import httpx

from .models import PkkExtent, PkkType, PkkSearchFeature, PkkTileResponse
from .utils import DEFAULT_SCALE, PKK_MAX_TILE_SIZE

API_HOST = 'https://pkk.rosreestr.ru/api'
SELECTED_TILE_HOST = 'https://pkk.rosreestr.ru/arcgis/rest/services/PKK6/CadastreSelected/MapServer/export'


HEADERS = {
    'pragma': 'no-cache',
    'referer': 'https://pkk.rosreestr.ru/',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

TILE_LAYERS: dict[PkkType, list[int]] = {
    1: [6, 7, 8, 9],
    5: [0, 1, 2, 3, 4, 5],
}


class TileServerNotResponsedError(Exception):
    pass


@contextmanager
def httpx_client():
    client = httpx.Client(headers=HEADERS, timeout=5, verify=False)
    try:
        yield client
    finally:
        client.close()


@asynccontextmanager
async def async_httpx_client():
    client = httpx.AsyncClient(headers=HEADERS, timeout=10, verify=False)
    try:
        yield client
    finally:
        await client.aclose()


def api_request(req_method: str, api_method: str, params: Optional[dict] = None, json: Optional[dict] = None):
    with httpx_client() as client:
        r = client.request(req_method, API_HOST + api_method,
                           params=params, json=json).raise_for_status()
        return r.json()


async def async_api_request(req_method: str, api_method: str, params: Optional[dict] = None, json: Optional[dict] = None):
    async with async_httpx_client() as client:
        try:
            r = await client.request(req_method, API_HOST + api_method,
                            params=params, json=json)
        except httpx.TimeoutException:
            await asyncio.sleep(1)
            return await async_api_request(req_method, api_method, params, json)
        if r.status_code == 502:
            await asyncio.sleep(1)
            return await async_api_request(req_method, api_method, params, json)
        r.raise_for_status()
        return r.json()


def generate_tile_params(feature: PkkSearchFeature, tile_extent: PkkExtent):
    width = (tile_extent.xmax - tile_extent.xmin) * DEFAULT_SCALE
    height = (tile_extent.ymax - tile_extent.ymin) * DEFAULT_SCALE
    width = width if width < PKK_MAX_TILE_SIZE else PKK_MAX_TILE_SIZE
    height = height if height < PKK_MAX_TILE_SIZE else PKK_MAX_TILE_SIZE
    layers = TILE_LAYERS[feature.type]
    layer_defs = {k: f"ID = '{feature.attrs.id}'" for k in layers}
    params = {
        "bbox": f'{tile_extent.xmin},{tile_extent.ymin},{tile_extent.xmax},{tile_extent.ymax}',
        "bboxSR": '102100',
        "imageSR": '102100',
        "size": f'{width},{height}',
        "dpi": '96',
        "format": 'png',
        "transparent": 'false',
        "layers": 'show:' + ','.join(map(str, layers)),
        "layerDefs": layer_defs,
        "f": 'json',
    }
    return params


async def tile_request(client: httpx.AsyncClient, feature: PkkSearchFeature, tile_extent: PkkExtent, tries_left: int = 10):
    if tries_left <= 0:
        raise TileServerNotResponsedError
    params = generate_tile_params(feature, tile_extent)
    try:
        r = await client.get(SELECTED_TILE_HOST, params=params)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        tries_left -= 1
        # если 503 (varnish cache error) - при повторных попытках пройдет
        if e.response.status_code >= 500:
            return await tile_request(client, feature, tile_extent, tries_left=tries_left)
        # если 400 - ошибка layerDefs от ПКК, но это неправда. Лечится незначительным изменением bbox
        elif e.response.status_code == 400:
            tile_extent.xmin -= 0.001
            tile_extent.xmax += 0.001
            tile_extent.ymin -= 0.001
            tile_extent.ymax += 0.001
            return await tile_request(client, feature, tile_extent, tries_left=tries_left)
        else:
            raise e
    except httpx.TimeoutException:
        tries_left -= 1
        return await tile_request(client, feature, tile_extent, tries_left=tries_left)
    except httpx.NetworkError:
        tries_left -= 1
        return await tile_request(client, feature, tile_extent, tries_left=tries_left)
    return PkkTileResponse.model_validate(r.json())
