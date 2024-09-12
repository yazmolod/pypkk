import asyncio
from typing import Optional
import time

import httpx
from shapely.geometry import mapping

from .requests import api_request, async_api_request, tile_request, async_tile_request, CLIENT_ARGS
from .models import Cn, PkkType, PkkAtPointResponse, PkkFeature, PkkFeatureResponse, PkkSearchFeature, PkkGeojson
from .tile_utils import generate_tile_extents
from .image import extract_geometry_from_tiles


tolerance = 4


class NoCoordsFeatureError(Exception):
    def __init__(self, feature: PkkSearchFeature):
        super().__init__(f"{feature.attrs.id} [{feature.type}] не имеет экстента")


class PKK:
    def __init__(self, use_cache: bool = True):
        self._client = httpx.Client(**CLIENT_ARGS)
        self._use_cache = use_cache

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self._client.close()

    def search_at_point(
        self,
        lng: float,
        lat: float,
        types: Optional[list[PkkType]] = None
    ) -> PkkAtPointResponse:
        params = {
            '_': round(time.time() * 1000),
            'tolerance': tolerance,
            'text': f'{lat} {lng}',
        }
        if types is not None:
            params['types'] = types
        r = api_request(self._client, 'get', '/features/', params=params)
        return PkkAtPointResponse.model_validate(r)

    def search(self, cn: Cn):
        ...

    def search_in_polygon(self, limit: int = 40):
        ...

    def get_attrs(self, cn: Cn) -> PkkFeatureResponse:
        params = {
            'date_format': r'%c',
            '_': round(time.time() * 1000),
        }
        r = api_request(
            self._client,
            'get',
            f'/features/{cn.kind}/{cn.clean_code}', params
        )
        return PkkFeatureResponse.model_validate(r)

    def get_geojson(self, feature: PkkSearchFeature) -> PkkGeojson:
        ...


class AsyncPKK:
    def __init__(self, use_cache: bool = True):
        self._client = httpx.AsyncClient(**CLIENT_ARGS)
        self._use_cache = use_cache

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self._client.aclose()

    async def search_at_point(
        self,
        lng: float,
        lat: float,
        types: Optional[list[PkkType]] = None
    ) -> PkkAtPointResponse:
        params = {
            '_': round(time.time() * 1000),
            'tolerance': tolerance,
            'text': f'{lat} {lng}',
        }
        if types is not None:
            params['types'] = types
        r = await async_api_request(self._client, 'get', '/features/', params=params)
        return PkkAtPointResponse.model_validate(r)

    async def search(self, cn: Cn):
        ...

    async def search_in_polygon(self, limit: int = 40):
        ...

    async def get_attrs(self, cn: Cn) -> PkkFeatureResponse:
        params = {
            'date_format': r'%c',
            '_': round(time.time() * 1000),
        }
        r = await async_api_request(
            self._client,
            'get',
            f'/features/{cn.kind}/{cn.clean_code}', params
        )
        return PkkFeatureResponse.model_validate(r)

    async def get_geojson(self, feature: PkkSearchFeature) -> PkkGeojson:
        if feature.extent is None:
            raise NoCoordsFeatureError(feature)
        extents = generate_tile_extents(feature.extent)
        tasks = [async_tile_request(self._client, feature, i) for i in extents]
        tiles_responses = await asyncio.gather(*tasks)
        geom = extract_geometry_from_tiles(tiles_responses)
        return PkkGeojson(geometry=mapping(geom), properties=feature.attrs)