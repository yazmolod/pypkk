from typing import Literal, Optional

from pydantic import Base64Bytes, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from pypkk.schemas.coords import PkkExtent
from pypkk.schemas.features import OksFeature, PkkSearchFeature, ZuFeature


class PkkAtPointResponse(BaseModel):
    total: int
    results: list[PkkSearchFeature]


class PkkSearchResponse(BaseModel):
    total: int
    features: list[PkkSearchFeature]
    total_relation: Literal["eq", "gte"]


class PkkFeatureResponse(BaseModel):
    feature: Optional[ZuFeature | OksFeature] = None


class PkkTileResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
    )

    image_data: Base64Bytes
    content_type: str
    width: int
    height: int
    extent: PkkExtent
    scale: float
