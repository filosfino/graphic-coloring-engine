from shapely.geometry import MultiPolygon

# from shapely.geometry.base import GEOMETRY_TYPES
# GEOMETRY_TYPES


class GeomTypeEnum:
    Point = "Point"
    LineString = "LineString"
    LinearRing = "LinearRing"
    Polygon = "Polygon"
    MultiPoint = "MultiPoint"
    MultiLineString = "MultiLineString"
    MultiPolygon = "MultiPolygon"
    GeometryCollection = "GeometryCollection"


def multi_polygon_difference(polygon_a: MultiPolygon, polygon_b: MultiPolygon) -> MultiPolygon:
    diff = polygon_a.difference(polygon_b)
    if diff.type == "Polygon":
        return MultiPolygon([diff])
    elif diff.type == "MultiPolygon":
        return diff
    else:
        raise Exception(f"bad polygon diff input: \n{polygon_a}\n{polygon_b}")
