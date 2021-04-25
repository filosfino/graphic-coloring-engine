from collections import defaultdict
import logging
from copy import deepcopy

import random
from graphic_coloring_engine.errors import ColoringEngineError

from cached_property import cached_property
from shapely.geometry.polygon import Polygon
from graphic_coloring_engine.monkey_patching.colormath_contrast import contrast
from graphic_coloring_engine.polygon import GeomTypeEnum, multi_polygon_difference
from typing import Callable, DefaultDict, Dict, List, Optional, Set, Union
from colormath.color_objects import ColorBase
from typing_extensions import Literal
import pydash as _
from shapely.geometry import MultiPolygon
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SIMPLIFY_RATIO = 0.05


@dataclass(frozen=True)
class Color:
    rgb_string: str

    def __eq__(self, o: "Color") -> bool:
        return self.rgb_string == o.rgb_string

    @cached_property
    def rgb(self):
        return ColorBase.from_hex_color_string(self.rgb_string)

    def contrast(self, color2: "Color") -> float:
        return contrast(self.rgb, color2.rgb)


@dataclass(frozen=True)
class ColorChoice(Color):
    from_layer_order: int = field(default=-1)  # -1 表示不来自于画布图层, 而来自于人工指定


@dataclass(frozen=True)
class DominantColor(Color):
    ratio: float  # 0-1


@dataclass(frozen=True)
class Coordinate:
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @cached_property
    def polygon(self) -> Polygon:
        return Polygon(
            [
                (self.xmin, self.ymin),
                (self.xmax, self.ymin),
                (self.xmax, self.ymax),
                (self.xmin, self.ymax),
            ]
        )


@dataclass
class Layer:
    order: int  # 值越小越底层
    bbox_coordinate: Coordinate
    type: Literal["image", "text"]
    polygon: MultiPolygon = field(default=None)
    dominant_colors: List[DominantColor] = field(default_factory=list)  # 图片才有
    color_mutable: bool = field(default=False)  # 是否需要进行配色
    color: Optional[Union[Color, ColorChoice]] = None

    def __post_init__(self):
        if self.type == "image":
            self.color_mutable = False
        if not self.polygon:
            self.polygon = MultiPolygon([self.bbox_coordinate.polygon])
        if not self.color and self.dominant_color_with_highest_ratio:
            self.color = self.dominant_color_with_highest_ratio

    @staticmethod
    def from_dict() -> "Layer":
        # TODO
        return

    @cached_property
    def dominant_color_with_highest_ratio(self) -> Optional[Color]:
        if not self.dominant_colors:
            return None
        dominant_color_with_highest_ratio: Union[DominantColor] = _.max_by(self.dominant_colors, lambda c: c.ratio)
        return dominant_color_with_highest_ratio

    @property
    def visible_on_canvas(self) -> bool:
        return not self.polygon.is_empty


@dataclass
class Layout:
    width: float
    height: float
    layers: List[Layer]

    # layer 碰撞矩阵
    layer_collision_map: Dict[int, List[int]] = field(default_factory=lambda: defaultdict(list), init=False)

    def __post_init__(self):
        self.layers = sorted(self.layers, key=lambda l: l.order)  # 从底往顶排序
        self.layer_collision_map = self._collision_detection()

    @cached_property
    def layer_map(self) -> Dict[int, Layer]:
        return _.key_by(self.layers, lambda l: l.order)

    def _collision_detection(self) -> Dict[int, Set[int]]:
        """图层碰撞计算"""
        logger.debug("开始图层碰撞计算, 初始 polygon:")
        for _layer in self.layers:
            logger.debug(f"{_layer.order} {_layer.polygon}")

        layer_collision_map = DefaultDict(set)
        # 按绘制顺序更新每层的 polygon
        logger.debug("开始更新图层的展示区域 polygon")
        for i, layer in enumerate(self.layers):
            if not layer.polygon or layer.polygon.is_empty:
                continue
            logger.debug(f"[layer-{i}]:\tpolygon: {layer.polygon}")
            for j, prev_layer in enumerate(self.layers[:i]):
                if not prev_layer.polygon or prev_layer.polygon.is_empty:
                    logger.debug(f"[layer-{i}]:\tpolygon: {layer.polygon}")
                    continue
                intersection = layer.polygon.intersection(prev_layer.polygon)
                if intersection.is_empty:
                    continue

                logger.debug(
                    f"\t[layer-{j}] intersection\t\tpolygon: {prev_layer.polygon}\t\tintersection type: {intersection.geom_type} result: {intersection}"
                )
                if intersection.geom_type == GeomTypeEnum.Point:
                    # 点相交不处理
                    continue
                elif intersection.geom_type in (GeomTypeEnum.LineString):
                    # 线相交不处理
                    continue
                else:
                    # 面相交
                    intersection = intersection.simplify(SIMPLIFY_RATIO, preserve_topology=False)
                    # 更新 prev_layer 的 polygon
                    prev_layer.polygon = multi_polygon_difference(prev_layer.polygon, intersection)
                    logger.debug(f"\t\t-> {prev_layer.polygon}")
                    # 更新碰撞矩阵
                    layer_collision_map[layer.order].add(prev_layer.order)
                    layer_collision_map[prev_layer.order].add(layer.order)
        logger.debug(f"初步碰撞计算结果")
        for _layer in self.layers:
            logger.debug(f"{_layer.order} {_layer.polygon}")
        # 不显示在画布上的元素
        logger.debug("开始清理画布上不出现的元素")
        layer_orders_not_visible_on_canvas = set(
            [order for order in layer_collision_map if not self.layer_map[order].visible_on_canvas]
        )
        logger.debug(f"清理元素: {layer_orders_not_visible_on_canvas}")
        # 去除
        for order in layer_orders_not_visible_on_canvas:
            del layer_collision_map[order]
        for order, collision_set in layer_collision_map.items():
            collision_set -= layer_orders_not_visible_on_canvas
        logger.debug("碰撞计算完毕")
        return layer_collision_map

    @property
    def layers_in_coloring_order(self) -> List[Layer]:
        """按配色顺序为 layer 排序"""
        return _.filter_(
            [
                self.layer_map[x[0]]
                for x in sorted(
                    _.map_values(self.layer_collision_map, lambda s: len(s)).items(),
                    key=lambda pair: pair[1],
                    reverse=True,
                )
            ],
            lambda layer: layer and not layer.color,
        )


@dataclass
class ColoringEngineConstants:
    文字与背景的最小对比度: float = 2.2


@dataclass
class ColoringEngine:
    """配色优先级: 设计师意图 > 业务规则(外部传入)
    基础规则必须应用, 包括
    - 文字和背景的对比度
    """

    layout: Layout
    seed: int
    constants: ColoringEngineConstants

    # 除了画布上的颜色以外还可以用哪些颜色
    extra_usable_colors: Set[ColorChoice] = field(default_factory=set)
    # 用于每个 layer 可用颜色过滤
    layer_color_filter_map: Dict[int, List[Callable[[ColorChoice, Layout], bool]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # 用于每个 layer 配色过程的校验
    layer_color_constraint_map: Dict[int, List[Callable[[Color, Layout], bool]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # 用于配色后的全局校验
    global_color_constraint: List[Callable[[Layout], bool]] = field(default_factory=list)
    # usable colors
    usable_colors: Set[ColorChoice] = field(default_factory=set, init=False)
    # 随机数生成器
    rng: random.Random = field(init=False)

    def __post_init__(self):
        self.usable_colors = self._collect_color_choices() | self.extra_usable_colors
        self.rng = random.Random(self.seed)

    def _collect_color_choices(self) -> Set[ColorChoice]:
        """采集画布上的颜色"""
        color_choices: Set[ColorChoice] = set()
        for layer in self.layout.layers:
            if not layer.visible_on_canvas:
                continue
            for dominant_color in layer.dominant_colors:
                color_choices.add(ColorChoice(dominant_color.rgb_string, layer.order))
        return color_choices

    def find_next_layer_to_colorize(self, layout: Optional[Layout]) -> Optional[Layer]:
        """下一个待配色的节点"""
        if not layout:
            layout = self.layout
        for layer in layout.layers_in_coloring_order:
            if layer.color:
                continue
            return layer
        return None

    @staticmethod
    def extract_color_scheme(colorized_layout: Layout) -> Dict[int, Union[Color, ColorChoice]]:
        return {layer.order: layer.color for layer in colorized_layout.layers if layer.color_mutable}

    def _colorize(self, layout: Optional[Layout] = None) -> Layout:
        """生成器"""
        if layout is None:
            layout = self.layout
        next_layer = self.find_next_layer_to_colorize(layout)
        if not next_layer:
            logger.info("all layers are colorized")
            return layout

        layer_logger = logger.getChild(f"layer-{next_layer.order}")
        # 确定可用颜色列表
        layer_usable_colors = self.usable_colors
        layer_logger.info(f"layer_usable_colors: {self.usable_colors}")
        color_filter_fn = self.get_layer_color_filters(next_layer.order)
        if color_filter_fn:
            new_layer_usable_colors = []
            for candidate_color in layer_usable_colors:
                try:
                    color_filter_fn(candidate_color)
                    new_layer_usable_colors.append(candidate_color)
                except ColoringEngineError as e:
                    logger.info(e.msg)
            layer_usable_colors = new_layer_usable_colors
        layer_logger.info(f"layer_usable_colors: filtered {self.usable_colors}")

        # 验证函数
        def color_validation_fn(color_choice: ColorChoice) -> bool:
            # 来自外部的约束
            color_validation_fn = self.get_layer_color_constraint(next_layer.order)
            if color_validation_fn:
                try:
                    color_validation_fn(color_choice)
                except ColoringEngineError as e:
                    logger.info(e.msg)
                    return False
            # 来自 collision 的约束
            return all(
                (
                    layer.color.contrast(color_choice) > self.constants.文字与背景的最小对比度
                    for layer in _.filter_(
                        [
                            layout.layer_map[collision_layer_order]
                            for collision_layer_order in layout.layer_collision_map[next_layer.order]
                        ],
                        lambda layer: layer.color,
                    )
                )
            )

        for color_choice in layer_usable_colors:
            if not color_validation_fn(color_choice):
                logger.debug(f"颜色校验失败, {next_layer}, {color_choice}")
                continue
            next_layer.color = color_choice
            # 是否已结束
            if not self.find_next_layer_to_colorize(layout=layout):
                should_yield = True
                if should_yield and self.global_color_constraint:
                    should_yield = all([constraint_fn(self.layout) for constraint_fn in self.global_color_constraint])
                    if not should_yield:
                        logger.info(f"全局校验失败, {layout}")
                if should_yield:
                    logger.debug("输出结果")
                    yield deepcopy(layout)
            else:
                for layout in self._colorize(deepcopy(layout)):
                    yield layout

    def colorize(self, count: int = 100):
        """
        原地改颜色
        :args count: 生成多少个配色方案
        """
        color_schemes = []
        logger.info("开始配色")
        for colorized_layout in self._colorize():
            color_scheme = self.extract_color_scheme(colorized_layout)
            color_schemes.append(color_scheme)
            logger.info(f"抽取出的 color_scheme {color_scheme}")
            if len(color_schemes) >= count:
                break
        return color_schemes

    def get_layer_color_filters(self, order: int) -> Optional[Callable[[ColorChoice], bool]]:
        filters = self.layer_color_filter_map.get(order)
        if not filters:
            return

        def filter_color(color_choice: ColorChoice) -> bool:
            for filter_fn in filters:
                if not filter_fn(color_choice, self):
                    raise ColoringEngineError(f"业务校验不通过: 颜色过滤, layer-{order}, {color_choice}")

        return filter_color

    def get_layer_color_constraint(self, order: int) -> Optional[Callable[[ColorChoice], bool]]:
        filters = self.layer_color_constraint_map.get(order)
        if not filters:
            return

        def validate_color(color_choice: ColorChoice) -> bool:
            for filter_fn in filters:
                if not filter_fn(color_choice, self):
                    raise ColoringEngineError(f"业务校验不通过: 颜色规则, layer-{order}, {color_choice}")

        return validate_color

    def validate_color_scheme(self):
        """业务校验 + 对比度校验, 不通过会抛错"""
        self._validate_colorized()
        self._validate_color_contrast()
        self._validate_color_constraint()

    def _validate_colorized(self):
        """是否已全部配色"""
        uncolorized_layers = [layer for layer in self.layout.layers if layer.color_mutable and layer.color]
        if uncolorized_layers:
            raise ColoringEngineError(f"以下节点尚未配色: {uncolorized_layers}")

    def _validate_color_contrast(self) -> None:
        """基本的对比度校验"""
        for order, collision_orders in self.layout.layer_collision_map.items():
            for collision_order in collision_orders:
                src_layer = self.layout.layer_map[order]
                collision_layer = self.layout.layer_map[collision_order]
                if not all([src_layer.color, collision_layer.color]):
                    continue
                if not any([src_layer.color_mutable, collision_layer.color_mutable]):
                    continue
                if "text" in set([src_layer.type, collision_layer.type]):
                    # 至少一层文字, 需要满足文字的对比度要求
                    if src_layer.color.contrast(collision_layer.color) < self.constants.文字与背景的最小对比度:
                        raise ColoringEngineError(f"文字与背景对比度不满足: {src_layer}, {collision_layer}")

    def _validate_color_constraint(self):
        """业务校验"""
        for layer in self.layout.layers:
            if not layer.color_mutable:
                continue
            if not layer.color:
                raise ColoringEngineError(f"以下图层尚未配色: {layer}")
            validate_color_fn = self.get_layer_color_constraint(layer.order)
            validate_color_fn(layer.color)
