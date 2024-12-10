from pydantic import BaseModel, ConfigDict


class SearchAttrs(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    cn: str
    address: str

    def model_dump_extra(self):
        return {**self.model_extra, **self.model_dump()}


class CommonAttrs(SearchAttrs):
    cad_cost: float
    area_value: float


class ZuAttrs(CommonAttrs):
    util_by_doc: str


class OksAttrs(CommonAttrs):
    floors: int
