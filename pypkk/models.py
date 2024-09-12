from typing import Literal, Annotated, Optional, Any

from pydantic import BaseModel, StringConstraints, ConfigDict, Base64Bytes
from pydantic.alias_generators import to_camel
from pydantic_geojson import FeatureModel, MultiPolygonModel
from shapely.geometry import shape

PkkType = Literal[1, 5]


class Cn(BaseModel):
    code: Annotated[str, StringConstraints(
        strip_whitespace=True, pattern=r'\d+:\d+:\d+:\d+')]
    kind: PkkType

    @property
    def clean_code(self):
        return ':'.join(map(str, map(int, self.code.split(':'))))


class PkkCenter(BaseModel):
    x: float
    y: float


class PkkExtent(BaseModel):
    xmin: float
    xmax: float
    ymin: float
    ymax: float


class PkkAttrs(BaseModel):
    id: str

    model_config = ConfigDict(
        extra='allow'
    )


class PkkSearchFeature(BaseModel):
    attrs: PkkAttrs
    sort: Optional[int] = None
    type: PkkType
    center: Optional[PkkCenter] = None
    extent: Optional[PkkExtent] = None


class PkkFeature(PkkSearchFeature):
    type_parent: Optional[Any] = None
    stat: Optional[dict] = {}
    extent_parent: Optional[PkkExtent] = None


class PkkAtPointResponse(BaseModel):
    total: int
    results: list[PkkSearchFeature]


class PkkSearchResponse(BaseModel):
    total: int
    features: list[PkkSearchFeature]
    total_relation: Literal['eq', 'gte']


class PkkFeatureResponse(BaseModel):
    feature: Optional[PkkFeature] = None

class PkkTileResponse(BaseModel):
    image_data: Base64Bytes
    content_type: str
    width: int
    height: int
    extent: PkkExtent
    scale: float

    model_config = ConfigDict(
        alias_generator=to_camel,
    )

class PkkGeojson(FeatureModel):
    geometry: MultiPolygonModel
    properties: PkkAttrs

    @property
    def shapely_geometry(self):
        return shape(self.geometry.model_dump())