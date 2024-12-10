import asyncio
from typing import Literal, Optional

import hishel
import httpx
from shapely.geometry import mapping

from pypkk.image import extract_geometry_from_tiles
from pypkk.requests import (
    CLIENT_ARGS,
    SSL_CONTEXT,
    api_request,
    async_api_request,
    async_tile_request,
    tile_request,
)
from pypkk.schemas.features import (
    OksGeojson,
    PkkGeojson,
    PkkSearchFeature,
    PkkType,
    ZuGeojson,
)
from pypkk.schemas.inputs import Cn
from pypkk.schemas.responses import PkkAtPointResponse, PkkFeatureResponse
from pypkk.tile_utils import generate_tile_extents

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
        cache_type: Optional[Literal["sqlite"]] = "sqlite",
        cache_ttl: int = 24 * 60 * 60,
    ):
        transport = None
        match cache_type:
            case "sqlite":
                transport = hishel.CacheTransport(
                    transport=httpx.HTTPTransport(verify=SSL_CONTEXT),
                    storage=hishel.SQLiteStorage(ttl=cache_ttl),
                    controller=_hishel_controller,
                )
        self._client = httpx.Client(**CLIENT_ARGS, transport=transport)

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        try:
            self._client.close()
        except AssertionError:
            pass

    def search_at_point(
        self, lng: float, lat: float, types: Optional[list[PkkType]] = None
    ) -> PkkAtPointResponse:
        params = {
            "tolerance": tolerance,
            "text": f"{lat} {lng}",
        }
        if types is not None:
            params["types"] = types
        r = api_request(self._client, "get", "/features/", params=params)
        return PkkAtPointResponse.model_validate(r)

    def search(self, cn: Cn): ...

    def search_in_polygon(self, limit: int = 40): ...

    def get_attrs(self, cn: Cn) -> PkkFeatureResponse:
        params = {
            "date_format": r"%c",
        }
        r = api_request(
            self._client, "get", f"/features/{cn.kind}/{cn.clean_code}", params
        )
        return PkkFeatureResponse.model_validate(r)

    def get_geojson(self, feature: PkkSearchFeature) -> PkkGeojson:
        if feature.extent is None:
            raise NoCoordsFeatureError(feature)
        extents = generate_tile_extents(feature.extent)
        tiles_responses = []
        for i in extents:
            tile_response = tile_request(self._client, feature, i)
            tiles_responses.append(tile_response)
        geom = extract_geometry_from_tiles(tiles_responses)
        return PkkGeojson(geometry=mapping(geom), properties=feature.attrs)


class AsyncPKK:
    def __init__(
        self,
        cache_type: Optional[Literal["sqlite"]] = "sqlite",
        cache_ttl: int = 24 * 60 * 60,
        use_lock: bool = True,
    ):
        transport = None
        match cache_type:
            case "sqlite":
                transport = hishel.AsyncCacheTransport(
                    transport=httpx.AsyncHTTPTransport(verify=SSL_CONTEXT),
                    storage=hishel.AsyncSQLiteStorage(ttl=cache_ttl),
                    controller=_hishel_controller,
                )
        self._client = httpx.AsyncClient(**CLIENT_ARGS, transport=transport)
        self.lock = asyncio.Lock() if use_lock else None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        try:
            await self._client.aclose()
        except AssertionError:
            pass

    async def search_at_point(
        self, lng: float, lat: float, types: Optional[list[PkkType]] = None
    ) -> PkkAtPointResponse:
        params = {
            "tolerance": tolerance,
            "text": f"{lat} {lng}",
        }
        if types is not None:
            params["types"] = types
        r = await async_api_request(
            self._client, "get", "/features/", params=params, lock=self.lock
        )
        return PkkAtPointResponse.model_validate(r)

    async def search(self, cn: Cn): ...

    async def search_in_polygon(self, limit: int = 40): ...

    async def get_attrs(self, cn: Cn) -> PkkFeatureResponse:
        params = {
            "date_format": r"%c",
        }
        r = await async_api_request(
            self._client,
            "get",
            f"/features/{cn.kind}/{cn.clean_code}",
            params=params,
            lock=self.lock,
        )
        return PkkFeatureResponse.model_validate(r)

    async def get_geojson(self, feature: PkkSearchFeature) -> PkkGeojson:
        if feature.extent is None:
            raise NoCoordsFeatureError(feature)
        extents = generate_tile_extents(feature.extent)
        tiles_responses = []
        for i in extents:
            tile_response = await async_tile_request(self._client, feature, i)
            tiles_responses.append(tile_response)
        geom = extract_geometry_from_tiles(tiles_responses)
        return PkkGeojson(
            geometry=mapping(geom), properties=feature.attrs.model_dump_extra()
        )

    async def find_geojson(self, cn: Cn) -> Optional[PkkGeojson]:
        resp = await self.get_attrs(cn)
        feature = resp.feature
        if feature is None:
            return None
        if feature.extent is None:
            return None
        geojson = await self.get_geojson(feature)
        return geojson

    async def find_zu_geojson(self, code: str) -> Optional[ZuGeojson]:
        geojson = await self.find_geojson(Cn.zu(code))
        if geojson is None:
            return None
        return ZuGeojson(
            geometry=geojson.geometry, properties=geojson.properties.model_dump_extra()
        )

    async def find_oks_geojson(self, code: str) -> Optional[OksGeojson]:
        geojson = await self.find_geojson(Cn.oks(code))
        if geojson is None:
            return None
        return OksGeojson(
            geometry=geojson.geometry, properties=geojson.properties.model_dump_extra()
        )
