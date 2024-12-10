from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchAttrs(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    cn: str

    def model_dump_extra(self):
        return {**self.model_extra, **self.model_dump()}


class CommonAttrs(SearchAttrs):
    cad_cost: Optional[float] = Field(description="Кадастровая стоимость")
    area_value: Optional[float] = Field(description="Площадь общая")
    address: Optional[str] = Field(description="Адрес")
    fp: Optional[int] = Field(description="Форма собственности (код)")


class ZuAttrs(CommonAttrs):
    util_by_doc: Optional[str] = Field(description="Разрешенное использование")


class OksAttrs(CommonAttrs):
    floors: Optional[int] = Field(
        description="Количество этажей (в том числе подземных)"
    )
    underground_floors: Optional[int] = Field(description="Количество подземных этажей")
    name: Optional[str] = Field(description="Наименование")
    year_built: Optional[int] = Field(description="Завершение строительства")
    year_used: Optional[int] = Field(description="Ввод в эксплуатацию")
