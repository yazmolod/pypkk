import pytest
import geopandas as gpd
import json

from pypkk import geocoder
from pypkk import models as m


@pytest.fixture
def complex_cn():
    return m.Cn(code='77:05:0001016:22', kind=1)


@pytest.fixture
def simple_cn():
    return m.Cn(code='77:06:0002012:3', kind=1)


@pytest.fixture
def small_cn():
    return m.Cn(code='77:02:0002003:70', kind=1)


@pytest.fixture
def large_cn():
    return m.Cn(code='77:22:0000000:625', kind=1)


def test_existing_cn(simple_cn):
    data = geocoder.get_attrs(simple_cn)
    assert data is not None
    return data


def test_search_at_point():
    data = geocoder.search_at_point(37.58525569633632, 55.74811840108685, [1, 5])
    assert data is not None


@pytest.mark.asyncio
async def test_get_geojson(large_cn):
    data = geocoder.get_attrs(large_cn)
    geo = await geocoder.async_get_geojson(data.feature)
    assert geo is not None
    geojson = geo.model_dump_json()
    with open('test.geojson', 'w') as file:
        file.write(geojson)
    gpd.read_file(geojson).set_crs(4326).to_file('test.gpkg', driver='GPKG')