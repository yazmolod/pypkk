import asyncio
from typing import Optional
import time
from shapely.geometry import mapping

from .requests import api_request, tile_request, async_httpx_client, async_api_request
from .models import Cn, PkkType, PkkAtPointResponse, PkkFeature, PkkFeatureResponse, PkkSearchFeature, PkkExtent, PkkTileResponse, PkkGeojson
from .utils import generate_tile_extents
from .image import get_geometry


tolerance = 4


class NoCoordsFeatureError(Exception):
    def __init__(self, feature: PkkSearchFeature):            
        super().__init__(f"{feature.attrs.id} [{feature.type}] не имеет экстента")


def search_at_point(lng: float, lat: float, types: Optional[list[PkkType]] = None) -> PkkAtPointResponse:
    params = {
        '_': round(time.time() * 1000),
        'tolerance': tolerance,
        'text': f'{lat} {lng}',
    }
    if types is not None:
        params['types'] = types
    r = api_request('get', '/features/', params=params)
    return PkkAtPointResponse.model_validate(r)


def search(cn: Cn):
    
    ...


def search_in_polygon(limit: int = 40):
    ...


def get_attrs(cn: Cn) -> PkkFeatureResponse:
    params = {
        'date_format': r'%c',
        '_': round(time.time() * 1000),
    }
    r = api_request('get', f'/features/{cn.kind}/{cn.clean_code}', params=params)
    return PkkFeatureResponse.model_validate(r)


async def async_get_attrs(cn: Cn) -> PkkFeatureResponse:
    params = {
        'date_format': r'%c',
        '_': round(time.time() * 1000),
    }
    r = await async_api_request('get', f'/features/{cn.kind}/{cn.clean_code}', params=params)
    return PkkFeatureResponse.model_validate(r)


async def async_get_geojson(feature: PkkSearchFeature) -> PkkGeojson:
    if feature.extent is None:
        raise NoCoordsFeatureError(feature)
    extents = generate_tile_extents(feature.extent)
    async with async_httpx_client() as client:
        tasks = [tile_request(client, feature, i) for i in extents]
        tiles_responses = await asyncio.gather(*tasks)
    geom = get_geometry(tiles_responses)
    return PkkGeojson(geometry=mapping(geom), properties=feature.attrs)