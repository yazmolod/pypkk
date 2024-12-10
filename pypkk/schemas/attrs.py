from pydantic import BaseModel, ConfigDict, Field


class SearchAttrs(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    cn: str

    def model_dump_extra(self):
        return {**self.model_extra, **self.model_dump()}


class CommonAttrs(SearchAttrs):
    cad_cost: float = Field(description="Кадастровая стоимость")
    area_value: float = Field(description="Площадь общая")
    address: str = Field(description="Адрес")
    fp: int = Field(description="Форма собственности (код)")


class ZuAttrs(CommonAttrs):
    util_by_doc: str = Field(description="Разрешенное использование")


class OksAttrs(CommonAttrs):
    floors: int = Field(description="Количество этажей (в том числе подземных)")
    undeground_floors: int = Field(description="Количество подземных этажей")
    name: str = Field(description="Наименование")
    year_built: int = Field(description="Завершение строительства")
    year_used: int = Field(description="Ввод в эксплуатацию")
