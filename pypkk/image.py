from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from shapely.geometry import LineString, Polygon, MultiPolygon

from shapely.ops import unary_union
from shapely.validation import make_valid

from .models import PkkTileResponse
from .geom_utils import to_4326


class NoContoursError(Exception):
    pass


def _get_image_xy_corner(stream: BytesIO):
    """get сartesian coordinates from raster"""
    image_xy_corners = []
    bytes = bytearray(stream.read())
    numpyarray = np.asarray(bytes, dtype=np.uint8)
    img = cv2.imdecode(numpyarray, cv2.IMREAD_GRAYSCALE)
    imagem = 255 - img
    ret, thresh = cv2.threshold(imagem, 10, 128, cv2.THRESH_BINARY)
    try:
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
    except Exception:
        im2, contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )
    if hierarchy is None:
        return None
    hierarchy = hierarchy[0]
    hierarchy_contours = [[] for _ in range(len(hierarchy))]
    for fry, current_contour in enumerate(contours):
        current_hierarchy = hierarchy[fry]
        cc = []
        # perimeter = cv2.arcLength(current_contour, True)
        # epsilon = 0.001 * cv2.arcLength(currentContour, True)
        # epsilon = epsilon * self.epsilon
        epsilon = 5
        approx = cv2.approxPolyDP(current_contour, epsilon, True)
        if len(approx) > 2:
            for c in approx:
                cc.append([c[0][0], c[0][1]])
            parent_index = current_hierarchy[3]
            index = fry if parent_index < 0 else parent_index
            hierarchy_contours[index].append(cc)
    image_xy_corners = [c for c in hierarchy_contours if len(c) > 0]
    if len(image_xy_corners)  == 0:
        return None
    return image_xy_corners


def get_image_geometry(tile_data: PkkTileResponse) -> Optional[MultiPolygon]:
    image_xy_corner = _get_image_xy_corner(BytesIO(tile_data.image_data))
    if image_xy_corner is None:
        return None
    dx = (tile_data.extent.xmax - tile_data.extent.xmin) / tile_data.width
    dy = (tile_data.extent.ymax - tile_data.extent.ymin) / tile_data.height
    for ig, geom in enumerate(image_xy_corner):
        for icnt, contours in enumerate(geom):
            for ic, coord in enumerate(contours):
                im_x, im_y = coord
                x = tile_data.extent.xmin + (im_x * dx)
                y = tile_data.extent.ymax - (im_y * dy)
                image_xy_corner[ig][icnt][ic] = [x, y]
    return to_geom(image_xy_corner)


def extract_geometry_from_tiles(tiles_data: list[PkkTileResponse]) -> MultiPolygon:
    geoms = []
    for i in tiles_data:
        geom = get_image_geometry(i)
        if geom is not None:
            geoms.append(geom)
    if len(geoms) == 0:
        raise NoContoursError
    merged = unary_union(geoms)
    assert isinstance(merged, (Polygon, MultiPolygon))
    if isinstance(merged, Polygon):
        return MultiPolygon([merged])
    return merged


def to_geom(xy) -> MultiPolygon:
    polys = []
    for g in xy:
        shell = LineString(g[0])
        holes = [LineString(i) for i in g[1:]] or None
        polys.append(Polygon(shell, holes))
    return make_valid(to_4326(MultiPolygon(polys)))
