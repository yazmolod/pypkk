import re
from typing import Annotated, Iterable, Literal, Optional

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

    @staticmethod
    def zu(code: str) -> "ZuCn":
        return ZuCn(code=code)

    @staticmethod
    def kvartal(code: str) -> "KvartalCn":
        return KvartalCn(code=code)

    @staticmethod
    def oks(code: str) -> "OksCn":
        return OksCn(code=code)

    @staticmethod
    def iter_cns(cns_string: str) -> Iterable[str]:
        for i in re.findall(r"\d+:\d+:\d+:\d+", cns_string):
            yield i

    @classmethod
    def _cn_array(cls, cns_string: str, kind: PkkType) -> Optional[list[Self]]:
        cns = [cls(code=i, kind=kind) for i in cls.iter_cns(cns_string)]
        return cns if len(cns) > 0 else None

    @classmethod
    def zu_array(cls, cns_string: str) -> Optional[list["ZuCn"]]:
        return cls._cn_array(cns_string, kind=1)

    @classmethod
    def kvartal_array(cls, cns_string: str) -> Optional[list["KvartalCn"]]:
        return cls._cn_array(cns_string, kind=2)

    @classmethod
    def oks_array(cls, cns_string: str) -> Optional[list["OksCn"]]:
        return cls._cn_array(cns_string, kind=5)


class ZuCn(Cn):
    kind: Literal[1] = 1


class OksCn(Cn):
    kind: Literal[5] = 5


class KvartalCn(Cn):
    code: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern=r"\d+:\d+:\d+")
    ]
    kind: Literal[2] = 2
