from typing import Optional
from .models import PkkExtent


# ~scale=375 в ответе с пкк; достаточный масштаб для определение выступа контура меньше метра
DEFAULT_SCALE = 10
# константа подобранная опытным путем, НЕ МЕНЯТЬ
# при запросе шириной/высотой больше этого значения будет ошибка
PKK_MAX_TILE_SIZE = 4000
# для больших кн ограничиванием количество разбиений на сабтайлы
# иначе количество запросов пойдет на сотни тысяч
MAX_SUBTILES_PER_CN = 100

TILE_BUFFER = 10
TILE_TRIES = 20
API_TRIES = 5
TILE_TIMEOUT = 1000
API_TIMEOUT = 1000


def generate_tile_extents(
    extent: PkkExtent,
    custom_extent: Optional[PkkExtent] = None,
    scale: Optional[int] = None) -> list[PkkExtent]:
    # if custom_extent is not None:
    #     input_extent.xmin = max([input_extent.xmin, custom_extent.xmin])
    #     input_extent.ymin = max([input_extent.ymin, custom_extent.ymin])
    #     input_extent.xmax = min([input_extent.xmax, custom_extent.xmax])
    #     input_extent.ymax = min([input_extent.ymax, custom_extent.ymax])
    scale = scale or DEFAULT_SCALE
    max_tile_size = PKK_MAX_TILE_SIZE / scale - TILE_BUFFER * 2
    extents: list[PkkExtent] = []
    cymin = extent.ymin
    while cymin < extent.ymax:
        yoffset = extent.ymax - cymin if cymin + \
            max_tile_size > extent.ymax else max_tile_size
        cymax = cymin + yoffset
        cxmin = extent.xmin
        while cxmin < extent.xmax:
            xoffset = extent.xmax - cxmin if cxmin + \
                max_tile_size > extent.xmax else max_tile_size
            cxmax = cxmin + xoffset
            extents.append(PkkExtent(
                xmin=cxmin - TILE_BUFFER,
                xmax=cxmax + TILE_BUFFER,
                ymin=cymin - TILE_BUFFER,
                ymax=cymax + TILE_BUFFER,
            ))
            cxmin += xoffset
        cymin += max_tile_size
    # если экстентов слишком много при таком масштабе - уменьшаем
    # но страдает качество контуров
    if len(extents) > MAX_SUBTILES_PER_CN and scale > 1:
        return generate_tile_extents(extent, custom_extent, scale - 1)
    return extents
