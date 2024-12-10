import asyncio
from pathlib import Path
from time import time

import pytest

# import geopandas as gpd
from pypkk import PKK, AsyncPKK
from pypkk.schemas.features import OksGeojson, ZuGeojson
from pypkk.schemas.inputs import Cn


@pytest.fixture(scope="session", autouse=True)
def delete_cache():
    file = Path(__file__).parent.parent / ".hishel.sqlite"
    if file.exists():
        file.unlink()


@pytest.fixture
def complex_cn():
    return Cn(code="77:05:0001016:22", kind=1)


@pytest.fixture
def simple_cn():
    return Cn(code="77:10:0005006:1977", kind=1)


@pytest.fixture
def small_cn():
    return Cn(code="77:02:0002003:70", kind=1)


@pytest.fixture
def large_cn():
    return Cn(code="77:22:0000000:625", kind=1)


def test_get_attrs(simple_cn):
    with PKK() as api:
        data = api.get_attrs(simple_cn)
        assert data is not None
        assert data.feature is not None
        assert not data.feature.shapely_geometry.is_empty


@pytest.mark.asyncio
async def test_async_get_attrs(simple_cn):
    async with AsyncPKK() as api:
        data = await api.get_attrs(simple_cn)
        assert data is not None
        assert data.feature is not None
        assert not data.feature.shapely_geometry.is_empty


def test_search_at_point():
    with PKK() as api:
        data = api.search_at_point(37.255265, 55.9766957, [1, 5])
        assert data is not None


@pytest.mark.asyncio
async def test_async_search_at_point():
    async with AsyncPKK() as api:
        data = await api.search_at_point(37.255265, 55.9766957, [1, 5])
        assert data is not None


@pytest.mark.asyncio
async def test_async_get_geojson(simple_cn):
    async with AsyncPKK() as api:
        data = await api.get_attrs(simple_cn)
        geo = await api.get_geojson(data.feature)
        assert geo is not None
        # geojson = geo.model_dump_json()
        # with open('test.geojson', 'w') as file:
        #     file.write(geojson)
        # gpd.read_file(geojson).set_crs(4326).to_file('test.gpkg', driver='GPKG')


@pytest.mark.asyncio
async def test_async_get_zu_geojson():
    async with AsyncPKK() as api:
        feat = await api.find_zu_geojson("77:01:0001078:3271")
        assert isinstance(feat, ZuGeojson)
        assert not feat.shapely_geometry.is_empty


@pytest.mark.asyncio
async def test_async_get_oks_geojson():
    async with AsyncPKK() as api:
        feat = await api.find_oks_geojson("77:01:0001078:1086")
        assert isinstance(feat, OksGeojson)
        assert not feat.shapely_geometry.is_empty


@pytest.mark.asyncio
async def test_async_gather_requests():
    cns_string = "77:03:0001007:28, 77:03:0001007:36, 77:03:0001007:32"
    cns = Cn.zu_array(cns_string)
    async with AsyncPKK(use_lock=True) as api:
        start_time = time()
        res = await asyncio.gather(*map(api.get_attrs, cns))
        assert all([i.feature is not None for i in res])
        non_cache_time = time()
        res = await asyncio.gather(*map(api.get_attrs, cns))
        assert all([i.feature is not None for i in res])
        cache_time = time()
        assert non_cache_time - start_time > 3
        assert cache_time - non_cache_time < 1
