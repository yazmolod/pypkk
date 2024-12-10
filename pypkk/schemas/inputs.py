import re
from typing import Annotated, Iterable, Optional

from pydantic import BaseModel, StringConstraints
from typing_extensions import Self

from pypkk.schemas.features import PkkType


class Cn(BaseModel):
    code: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=r"\d+:\d+:\d+:\d+")
    ]
    kind: PkkType

    @property
    def clean_code(self) -> str:
        return ":".join(map(str, map(int, self.code.split(":"))))

    @classmethod
    def zu(cls, code: str) -> Self:
        return cls(code=code, kind=1)

    @classmethod
    def oks(cls, code: str) -> Self:
        return cls(code=code, kind=5)

    @staticmethod
    def iter_cns(cns_string: str) -> Iterable[str]:
        for i in re.findall(r"\d+:\d+:\d+:\d+", cns_string):
            yield i

    @classmethod
    def zu_array(cls, cns_string: str) -> Optional[list[Self]]:
        cns = [cls(code=i, kind=1) for i in cls.iter_cns(cns_string)]
        return cns if len(cns) > 0 else None

    @classmethod
    def oks_array(cls, cns_string: str) -> Optional[list[Self]]:
        cns = [cls(code=i, kind=5) for i in cls.iter_cns(cns_string)]
        return cns if len(cns) > 0 else None
