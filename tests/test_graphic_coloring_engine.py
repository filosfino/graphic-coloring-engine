import logging
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon
from graphic_coloring_engine.core import (
    Color,
    ColorChoice,
    ColoringEngine,
    ColoringEngineConstants,
    Coordinate,
    DominantColor,
    Layer,
    Layout,
)
from graphic_coloring_engine import __version__
from snapshottest import TestCase

logger = logging.getLogger(__name__)


def test_version():
    assert __version__ == "0.1.0"


class TestLayout(TestCase):
    seed = 42
    constants = ColoringEngineConstants()
    default_allowed_color_set = set([ColorChoice("#000"), ColorChoice("#fff")])
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
    # 左上
    text_coord = Coordinate(
        xmin=0,
        xmax=50,
        ymin=0,
        ymax=50,
    )
    # 右下
    text_coord_2 = Coordinate(
        xmin=50,
        xmax=100,
        ymin=150,
        ymax=200,
    )

    def build_layout(self):
        return Layout(
            width=100,
            height=200,
            layers=[
                # 背景
                Layer(
                    order=0,
                    bbox_coordinate=self.bg_coord,
                    dominant_colors=[DominantColor("#1f1f1f", ratio=0.8)],
                    type="image",
                ),
                # 图片
                Layer(
                    order=1,
                    bbox_coordinate=self.img_coord,
                    dominant_colors=[DominantColor("#88F", ratio=0.8)],
                    type="image",
                ),
                # 文字
                Layer(
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
                ),
                # 文字
                Layer(
                    order=3,
                    bbox_coordinate=self.text_coord_2,
                    color_mutable=True,
                    type="text",
                ),
            ],
        )

    def test_coloring_engine_init(self):
        # 没有设置额外的约束
        layout = self.build_layout()
        engine = ColoringEngine(layout, seed=self.seed, constants=self.constants)
        assert engine.get_layer_color_filters(0) is None
        assert engine.get_layer_color_constraint(0) is None

        color_schemes = engine.colorize()
        assert len(color_schemes) == 0

    def test_coloring_engine_init_with_extra_color(self):
        layout = self.build_layout()
        engine = ColoringEngine(
            layout, seed=self.seed, constants=self.constants, extra_usable_colors=self.default_allowed_color_set
        )
        assert engine.get_layer_color_filters(0) is None
        assert engine.get_layer_color_constraint(0) is None

        color_schemes = engine.colorize()
        assert len(color_schemes) > 0

        # 预期文字颜色与相交的元素都有足够对比度
        for color_scheme in color_schemes:
            for layer_order in [layer.order for layer in layout.layers if layer.type == "text"]:
                new_text_color = color_scheme[layer_order]
                for bg_order in layout.layer_collision_map[layer_order]:
                    bg_layer = layout.layer_map[bg_order]
                    assert bg_layer.color.contrast(new_text_color) > engine.constants.文字与背景的最小对比度

    def test_coloring_engine_init_with_filter(self):
        layout = self.build_layout()
        engine = ColoringEngine(
            layout,
            seed=self.seed,
            constants=self.constants,
            extra_usable_colors=self.default_allowed_color_set,
            layer_color_filter_map={2: [lambda color, layout: False]},
        )
        assert engine.get_layer_color_filters(2) is not None

        color_schemes = engine.colorize()
        assert len(color_schemes) == 0

    def test_coloring_engine_init_with_constraint(self):
        layout = self.build_layout()
        engine = ColoringEngine(
            layout,
            seed=self.seed,
            constants=self.constants,
            extra_usable_colors=self.default_allowed_color_set,
            layer_color_constraint_map={2: [lambda color, layout: False]},
            # global_color_constraint=[],
        )
        assert engine.get_layer_color_constraint(2) is not None

        color_schemes = engine.colorize()
        assert len(color_schemes) == 0

    def test_coloring_engine_init_with_global_constraint(self):
        layout = self.build_layout()
        engine = ColoringEngine(
            layout,
            seed=self.seed,
            constants=self.constants,
            extra_usable_colors=self.default_allowed_color_set,
            global_color_constraint=[lambda layout: Color("#000") == layout.layers[2].color],
        )
        color_schemes = engine.colorize()
        assert len(color_schemes) != 0
