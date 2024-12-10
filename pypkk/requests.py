import asyncio
import ssl
from time import sleep
from typing import Optional

import httpx

from pypkk.schemas.coords import PkkExtent
from pypkk.schemas.features import PkkSearchFeature, PkkType
from pypkk.schemas.responses import PkkTileResponse
from pypkk.tile_utils import DEFAULT_SCALE, PKK_MAX_TILE_SIZE

API_HOST = "https://pkk.rosreestr.ru/api"
SELECTED_TILE_HOST = "https://pkk.rosreestr.ru/arcgis/rest/services/PKK6/CadastreSelected/MapServer/export"

CLIENT_ARGS = {
    "headers": {
        "pragma": "no-cache",
        "origin": "https://pkk.rosreestr.ru/",
        "referer": "https://pkk.rosreestr.ru/",
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    },
    "timeout": 30,
}

SSL_CONTEXT = ssl._create_unverified_context()
SSL_CONTEXT.set_ciphers("ALL:@SECLEVEL=1")

TILE_LAYERS: dict[PkkType, list[int]] = {
    1: [6, 7, 8, 9],
    2: [10, 11, 12],
    5: [0, 1, 2, 3, 4, 5],
}


class TileServerNotResponsedError(Exception):
    pass


def time_to_sleep(r: httpx.Response):
    mcs = 1_000_000 - r.elapsed.microseconds
    if mcs <= 0:
        return 0
    return round(mcs / 10**6, 1)


def api_request(
    client: httpx.Client,
    req_method: str,
    api_method: str,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
):
    r = client.request(req_method, API_HOST + api_method, params=params, json=json)
    if not r.extensions["from_cache"]:
        sleep(time_to_sleep(r))
    if r.status_code == 502:
        return api_request(client, req_method, api_method, params, json)
    r.raise_for_status()
    return r.json()


async def async_api_request(
    client: httpx.AsyncClient,
    req_method: str,
    api_method: str,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    lock: Optional[asyncio.Lock] = None,
):
    if lock is not None:
        await lock.acquire()
    r = await client.request(
        req_method, API_HOST + api_method, params=params, json=json
    )
    if lock is not None:
        if not r.extensions["from_cache"]:
            await asyncio.sleep(time_to_sleep(r))
        lock.release()
    if r.status_code == 502:
        return await async_api_request(
            client, req_method, api_method, params, json, lock
        )
    r.raise_for_status()
    return r.json()


def _generate_tile_params(feature: PkkSearchFeature, tile_extent: PkkExtent):
    width = (tile_extent.xmax - tile_extent.xmin) * DEFAULT_SCALE
    height = (tile_extent.ymax - tile_extent.ymin) * DEFAULT_SCALE
    width = width if width < PKK_MAX_TILE_SIZE else PKK_MAX_TILE_SIZE
    height = height if height < PKK_MAX_TILE_SIZE else PKK_MAX_TILE_SIZE
    layers = TILE_LAYERS[feature.type]
    layer_defs = {k: f"ID = '{feature.attrs.id}'" for k in layers}
    params = {
        "bbox": f"{tile_extent.xmin},{tile_extent.ymin},{tile_extent.xmax},{tile_extent.ymax}",
        "bboxSR": "102100",
        "imageSR": "102100",
        "size": f"{width},{height}",
        "dpi": "96",
        "format": "png",
        "transparent": "false",
        "layers": "show:" + ",".join(map(str, layers)),
        "layerDefs": layer_defs,
        "f": "json",
    }
    return params


async def async_tile_request(
    client: httpx.AsyncClient,
    feature: PkkSearchFeature,
    tile_extent: PkkExtent,
    tries_left: int = 10,
):
    if tries_left <= 0:
        raise TileServerNotResponsedError
    params = _generate_tile_params(feature, tile_extent)
    try:
        r = await client.get(SELECTED_TILE_HOST, params=params)
        r.raise_for_status()
    except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError) as e:
        if isinstance(e, httpx.HTTPStatusError):
            # если 400 - ошибка layerDefs от ПКК, но это неправда. Лечится незначительным изменением bbox
            if e.response.status_code == 400:
                tile_extent.xmin -= 0.001
                tile_extent.xmax += 0.001
                tile_extent.ymin -= 0.001
                tile_extent.ymax += 0.001
                return await async_tile_request(
                    client, feature, tile_extent, tries_left=tries_left
                )
            elif e.response.status_code < 500:
                raise e
        await asyncio.sleep(1)
        tries_left -= 1
        return await async_tile_request(
            client, feature, tile_extent, tries_left=tries_left
        )
    return PkkTileResponse.model_validate(r.json())


def tile_request(
    client: httpx.Client,
    feature: PkkSearchFeature,
    tile_extent: PkkExtent,
    tries_left: int = 10,
):
    if tries_left <= 0:
        raise TileServerNotResponsedError
    params = _generate_tile_params(feature, tile_extent)
    try:
        r = client.get(SELECTED_TILE_HOST, params=params)
        r.raise_for_status()
    except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError) as e:
        if isinstance(e, httpx.HTTPStatusError):
            # если 400 - ошибка layerDefs от ПКК, но это неправда. Лечится незначительным изменением bbox
            if e.response.status_code == 400:
                tile_extent.xmin -= 0.001
                tile_extent.xmax += 0.001
                tile_extent.ymin -= 0.001
                tile_extent.ymax += 0.001
                return tile_request(client, feature, tile_extent, tries_left=tries_left)
            elif e.response.status_code < 500:
                raise e
        sleep(1)
        tries_left -= 1
        return tile_request(client, feature, tile_extent, tries_left=tries_left)
    return PkkTileResponse.model_validate(r.json())
