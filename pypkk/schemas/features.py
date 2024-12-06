from typing import Any, Literal, Optional

from pydantic import BaseModel
from pydantic_geojson import FeatureModel, MultiPolygonModel
from shapely.geometry import MultiPolygon, Point, shape

from pypkk.schemas.attrs import SearchAttrs, OksAttrs, ZuAttrs, CommonAttrs
from pypkk.schemas.coords import PkkCenter, PkkExtent

from pypkk.geom_utils import to_4326

PkkType = Literal[1, 5]


class PkkSearchFeature(BaseModel):
    attrs: SearchAttrs
    sort: Optional[int] = None
    type: PkkType
    center: Optional[PkkCenter] = None
    extent: Optional[PkkExtent] = None

    @property
    def shapely_geometry(self):
        if self.center is None:
            return Point()
        return to_4326(Point(self.center.x, self.center.y))


class PkkFeature(PkkSearchFeature):
    type_parent: Optional[Any] = None
    stat: Optional[dict] = {}
    extent_parent: Optional[PkkExtent] = None

class ZuFeature(PkkFeature):
    type: Literal[1]
    attrs: ZuAttrs
    
class OksFeature(PkkFeature):
    type: Literal[5]
    attrs: OksAttrs


class PkkGeojson(FeatureModel):
    geometry: MultiPolygonModel
    properties: CommonAttrs

    @property
    def shapely_geometry(self) -> MultiPolygon:
        return shape(self.geometry.model_dump())

class ZuGeojson(PkkGeojson):
    properties: ZuAttrs
    
class OksGeojson(PkkGeojson):
    properties: OksAttrs