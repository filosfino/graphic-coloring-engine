from graphic_coloring_engine.core import Color, Coordinate, DominantColor, Layer, Layout
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from snapshottest import TestCase


class TestLayout(TestCase):
    bg_coord = Coordinate(
        xmin=0,
        xmax=100,
        ymin=0,
        ymax=200,
    )
    img_coord = Coordinate(
        xmin=0,
        xmax=30,
        ymin=0,
        ymax=30,
    )
    text_coord = Coordinate(
        xmin=0,
        xmax=50,
        ymin=0,
        ymax=50,
    )

    def test_layer_init_polygon_without_polygon(self):
        layer = Layer(
            order=0,
            bbox_coordinate=self.bg_coord,
            dominant_colors=[DominantColor(rgb_string="#FFF", ratio=0.8)],
            color_mutable=False,
            type="image",
        )
        # 默认使用 bbox
        assert layer.polygon.equals(self.bg_coord.polygon)
        self.assert_match_snapshot(layer.polygon.svg())

    def test_layer_init_polygon_with_polygon(self):
        polygon = Polygon([(0, 0), (30, 30), (0, 30)])
        layer = Layer(
            order=0,
            bbox_coordinate=self.bg_coord,
            polygon=MultiPolygon([polygon]),
            dominant_colors=[DominantColor(rgb_string="#FFF", ratio=0.8)],
            color_mutable=False,
            type="image",
        )
        assert layer.polygon.equals(polygon)
        self.assert_match_snapshot(layer.polygon.svg())

    def test_layout_init(self):
        背景 = Layer(
            order=0,
            bbox_coordinate=self.bg_coord,
            dominant_colors=[
                DominantColor(rgb_string="#340", ratio=0.6),
                DominantColor(rgb_string="#404", ratio=0.3),
            ],
            type="image",
        )
        图片 = Layer(
            order=1,
            bbox_coordinate=self.img_coord,
            dominant_colors=[
                DominantColor(rgb_string="#efF", ratio=0.4),
                DominantColor(rgb_string="#a8a", ratio=0.2),
                DominantColor(rgb_string="#803", ratio=0.1),
            ],
            type="image",
        )
        文字 = Layer(
            order=2,
            bbox_coordinate=self.text_coord,
            polygon=MultiPolygon(
                [
                    Polygon(
                        [
                            (10, 20),
                            (40, 20),
                            (40, 30),
                            (10, 30),
                        ]
                    )
                ]
            ),
            color_mutable=True,
            type="text",
        )
        layout = Layout(
            width=100,
            height=200,
            layers=[
                背景,
                图片,
                文字,
            ],
        )
        self.assert_match_snapshot(layout.layer_collision_map)
        self.assert_match_snapshot([x.polygon.svg() for x in layout.layers])
        assert 背景.color == Color(rgb_string="#340")
        assert 图片.color == Color(rgb_string="#efF")
        assert 文字.color is None
