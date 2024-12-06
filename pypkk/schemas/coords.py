from pydantic import BaseModel


class PkkCenter(BaseModel):
    x: float
    y: float


class PkkExtent(BaseModel):
    xmin: float
    xmax: float
    ymin: float
    ymax: float