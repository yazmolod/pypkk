import pytest
import geopandas as gpd
import json

from pypkk import Cn, PKK, AsyncPKK


@pytest.fixture
def complex_cn():
    return Cn(code='77:05:0001016:22', kind=1)


@pytest.fixture
def simple_cn():
    return Cn(code='77:10:0005006:1977', kind=1)


@pytest.fixture
def small_cn():
    return Cn(code='77:02:0002003:70', kind=1)


@pytest.fixture
def large_cn():
    return Cn(code='77:22:0000000:625', kind=1)


def test_get_attrs(simple_cn):
    with PKK() as api:
        data = api.get_attrs(simple_cn)
        assert data is not None


@pytest.mark.asyncio
async def test_async_get_attrs(simple_cn):
    async with AsyncPKK() as api:
        data = await api.get_attrs(simple_cn)
        assert data is not None


def test_search_at_point():
    with PKK() as api:
        data = api.search_at_point(37.58525569633632, 55.74811840108685, [1, 5])
        assert data is not None


@pytest.mark.asyncio
async def test_async_search_at_point():
    async with AsyncPKK() as api:
        data = await api.search_at_point(37.58525569633632, 55.74811840108685, [1, 5])
        assert data is not None


@pytest.mark.asyncio
async def test_async_get_geojson(simple_cn):
    async with AsyncPKK() as api:
        data = await api.get_attrs(simple_cn)
        geo = await api.get_geojson(data.feature)
        assert geo is not None
        geojson = geo.model_dump_json()
        with open('test.geojson', 'w') as file:
            file.write(geojson)
        gpd.read_file(geojson).set_crs(4326).to_file('test.gpkg', driver='GPKG')