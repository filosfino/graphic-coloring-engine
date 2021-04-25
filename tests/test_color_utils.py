from colormath.color_objects import ColorBase
from graphic_coloring_engine.core import Color
from snapshottest import TestCase


class TestColorUtils(TestCase):
    def test_contrast_impl(self):
        c1 = ColorBase.from_hex_color_string("#0000FF")
        c2 = ColorBase.from_hex_color_string("#FFFFFF")
        assert (c1.contrast(c2) - 8.59) < 0.01

    def test_color(self):
        assert Color("#F00").rgb.rgb_r == 1.0
