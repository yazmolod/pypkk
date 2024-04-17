from typing import Generator, Any
import re
import asyncio
from shapely import MultiPolygon, Polygon
from shapely import wkt


def iter_cns(cns: str) -> Generator[str, None, None]:
    assert isinstance(cns, str)
    for i in re.findall(r'[\d:]+', cns):
        yield i.strip(':')


async def pkk_polygon(cn: str) -> tuple[MultiPolygon, dict[str, Any]]:
    """Получить геометрию и атрибуты по кадастровому номеру

    Args:
        cn (str): кадастровый номер

    Returns:
        tuple[MultiPolygon, dict[str, Any]]: геометрия участка; атрибуты участка
    """
    # TODO: async geocoding
    await asyncio.sleep(1)
    return MultiPolygon([wkt.loads("Polygon ((37.615 55.756, 37.604 55.750, 37.618 55.744, 37.626 55.749, 37.615 55.756))")]), {"cn": cn}


async def pkk_multipolygon(cns: str) -> MultiPolygon:
    """Получить объединенную геометрию списка кадастровых номеров 

    Args:
        cns (str): строка со списоком кадастрвых номеров

    Returns:
        MultiPolygon: геометрия участков
    """
    polys = []
    results = await asyncio.gather(*[pkk_polygon(cn) for cn in iter_cns(cns)])
    for r in results:
        geom = r[0]
        if isinstance(geom, Polygon):
            polys.append(geom)
        elif isinstance(geom, MultiPolygon):
            for g in geom.geoms:
                polys.append(g)
    return MultiPolygon(polys)