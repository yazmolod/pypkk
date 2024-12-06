from pydantic import BaseModel, StringConstraints
from pypkk.schemas.features import PkkType

from typing import Annotated


class Cn(BaseModel):
    code: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=r"\d+:\d+:\d+:\d+")
    ]
    kind: PkkType

    @property
    def clean_code(self):
        return ":".join(map(str, map(int, self.code.split(":"))))

    @classmethod
    def zu(cls, code: str):
        return cls(code=code, kind=1)

    @classmethod
    def oks(cls, code: str):
        return cls(code=code, kind=5)