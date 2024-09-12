import asyncio
from typing import Optional, Literal
import time

import httpx
import hishel
from shapely.geometry import mapping

from .requests import api_request, async_api_request, tile_request, async_tile_request, CLIENT_ARGS
from .models import Cn, PkkType, PkkAtPointResponse, PkkFeature, PkkFeatureResponse, PkkSearchFeature, PkkGeojson
from .tile_utils import generate_tile_extents
from .image import extract_geometry_from_tiles


tolerance = 4
_hishel_controller = hishel.Controller(
    allow_stale=True,
    force_cache=True,
    cacheable_status_codes=[200],
)

class NoCoordsFeatureError(Exception):
    def __init__(self, feature: PkkSearchFeature):
        super().__init__(f"{feature.attrs.id} [{feature.type}] не имеет экстента")


class PKK:
    def __init__(
        self,
        cache_type: Optional[Literal['sqlite']] = 'sqlite',
        cache_ttl: int = 24*60*60
    ):
        transport = None
        match cache_type:
            case 'sqlite':
                transport = hishel.CacheTransport(
                    transport=httpx.HTTPTransport(verify=False),
                    storage=hishel.SQLiteStorage(ttl=cache_ttl),
                    controller=_hishel_controller,
                )
        self._client = httpx.Client(**CLIENT_ARGS, transport=transport)

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
    def __init__(
        self,
        cache_type: Optional[Literal['sqlite']] = 'sqlite',
        cache_ttl: int = 24*60*60
    ):
        transport = None
        match cache_type:
            case 'sqlite':
                transport = hishel.AsyncCacheTransport(
                    transport=httpx.AsyncHTTPTransport(verify=False),
                    storage=hishel.AsyncSQLiteStorage(ttl=cache_ttl),
                    controller=_hishel_controller,
                )
        self._client = httpx.AsyncClient(**CLIENT_ARGS, transport=transport)

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