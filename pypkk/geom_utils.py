from typing import TypeVar

import pyproj
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

T = TypeVar("T", bound=BaseGeometry)


EPSG_3857 = pyproj.CRS("epsg:3857")
EPSG_4326 = pyproj.CRS("epsg:4326")
TRANSFORM_3857_4326 = pyproj.Transformer.from_crs(
    EPSG_3857, EPSG_4326, always_xy=True
).transform


def to_4326(geom: T) -> T:
    """Перевод геометрии из epsg:3857 в epsg:4326"""
    return transform(TRANSFORM_3857_4326, geom)
