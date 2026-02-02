from PIL.ImageFont import FreeTypeFont
from PIL import features as PIL_features

from dcmntr.core import *
from dataclasses import dataclass

from dcmntr.core import (
    LayoutAxisOverflowException,
    NodeLayout,
    NodeLayoutCtx,
    LayoutCrossAxisOverflowException,
)

__all__ = [
    "Color",
    "layers",
    "h_stack",
    "v_stack",
    "padding",
    "box",
    "simple_text",
    "outline",
    "box",
    "right",
    "bottom",
    "h_center",
    "v_center",
    "center",
    "flow",
    "ensure_size",
    "h_divide",
    "v_divide",
]

from dcmntr.font import Font

type Color = str | tuple[int, int, int] | tuple[int, int, int, int]


@dataclass(frozen=True)
class Layers(Node):

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        layouts = tuple(ctx.layout_node(node, constraints) for node in self.children)
        leftovers = [l.layout.leftover for l in layouts if l.layout.leftover is not None]
        leftover = None
        if leftovers:
            leftover = self(*leftovers)

        return NodeLayout(Size.that_fit_layouts(layouts), layouts, leftover=leftover)


layers = Layers()


@dataclass(frozen=True)
class Stack(Node):
    direction: Size

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        x: float = 0
        y: float = 0
        max_size: Size = Size(0, 0)
        layouts: list[Layout] = []
        leftover: Node | None = None
        if self.direction.width:
            # Horizontal container can not split, only move to the next page
            ctx.can_split = False
        constraints_left = constraints
        for idx, node in enumerate(self.children):
            try:
                layout = ctx.layout_node(
                    node,
                    constraints_left,
                    x=x,
                    y=y,
                )
            except LayoutAxisOverflowException:
                if not ctx.can_split:
                    raise
                leftover = self(*self.children[idx:])
                break
            layouts.append(layout)

            if layout.layout.leftover is not None:
                leftover = self(layout.layout.leftover, *self.children[idx + 1 :])
                break

            step = layout.layout.size.mul(self.direction)
            max_size = layout.layout.size.max(max_size)
            x += step.width
            y += step.height
            constraints_left = constraints_left.shrink_by(step.width, step.height)

        if self.direction.height:
            size = Size(max_size.width, y)
        else:
            size = Size(x, max_size.height)

        if leftover is not None:
            size = constraints.extend_size_down(size)

        return NodeLayout(size, tuple(layouts), leftover=leftover)


v_stack = Stack(direction=Size(0, 1))
h_stack = Stack(direction=Size(1, 0))


@dataclass(frozen=True)
class Box(Node):
    """Supports infinite width and/or height. In this case it will fill maximum space in width or height."""

    width: float = INFINITY
    height: float = INFINITY

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert len(self.children) <= 1

        size = Size(
            self.width if self.width != INFINITY else constraints.max_width,
            self.height if self.height != INFINITY else constraints.max_height,
        )
        child_constraints = Constraints(
            constraints.min_width,
            size.width,
            constraints.min_height,
            size.height,
        )

        child_layouts = tuple(ctx.layout_node(node, child_constraints) for node in self.children)
        return NodeLayout(size, tuple(child_layouts))


box: type[Box] = Box
expand = box(width=INFINITY, height=INFINITY)


@dataclass(frozen=True)
class SimpleText(LeafNode):
    """Simple non-word wrapping text"""

    text: str
    font: Font
    color: Color = "black"
    spacing: float = 2
    antialiasing: bool = True

    LIGA_AND_KERN_SUPPORTED = PIL_features.check("raqm")

    def draw_image(self, x: float, y: float, layout: Layout, draw_ctx: ImageDrawCtx) -> None:
        draw_ctx.draw.fontmode = "L" if self.antialiasing else "1"
        draw_ctx.draw.text(
            (x, y),
            self.text,
            fill=self.color,
            font=self.font.pil_font,
            spacing=self.spacing,
            features=["liga", "kern"] if self.LIGA_AND_KERN_SUPPORTED else None,
        )

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        width, height = self.multiline_text_size(self.text, self.font.pil_font, self.spacing)
        return NodeLayout(Size(width, height), ())

    # FIXME not accurate :(
    @staticmethod
    def multiline_text_size(
        text: str, font: FreeTypeFont, spacing: float, align: str = "left"
    ) -> tuple[float, float]:

        lines = text.splitlines() or [""]

        ascent, descent = font.getmetrics()
        line_height = ascent + descent

        widths = []
        for line in lines:
            bbox = font.getbbox(line)
            widths.append(bbox[2] - bbox[0])

        max_width = max(widths)
        total_height = line_height * len(lines) + spacing * (len(lines) - 1)

        return max_width, total_height


simple_text = SimpleText


@dataclass(frozen=True)
class Outline(Node):
    fill: Color | None = None
    border_width: int | None = 1
    border_color: Color | None = "gray"

    border_top: bool = True
    border_right: bool = True
    border_bottom: bool = True
    border_left: bool = True

    def draw_image(self, x: float, y: float, layout: Layout, draw_ctx: ImageDrawCtx) -> None:
        if layout.layout.size.width > 0 and layout.layout.size.height > 0:
            draw_ctx.draw.rectangle(
                [
                    (x, y),
                    (
                        x + layout.layout.size.width - 1,
                        y + layout.layout.size.height - 1,
                    ),
                ],
                fill=self.fill,
                width=0,
            )

            for should_draw, coords in (
                (
                    self.border_top,
                    [
                        (x, y),
                        (
                            x + layout.layout.size.width - 1,
                            y,
                        ),
                    ],
                ),
                (
                    self.border_right,
                    [
                        (x + layout.layout.size.width - 1, y),
                        (
                            x + layout.layout.size.width - 1,
                            y + layout.layout.size.height - 1,
                        ),
                    ],
                ),
                (
                    self.border_left,
                    [
                        (x, y),
                        (
                            x,
                            y + layout.layout.size.height - 1,
                        ),
                    ],
                ),
                (
                    self.border_bottom,
                    [
                        (x, y + layout.layout.size.height - 1),
                        (
                            x + layout.layout.size.width - 1,
                            y + layout.layout.size.height - 1,
                        ),
                    ],
                ),
            ):
                if should_draw:
                    draw_ctx.draw.line(
                        coords,
                        fill=self.border_color,
                        width=self.border_width or 0,
                    )

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert len(self.children) <= 1
        layouts = tuple(ctx.layout_node(node, constraints) for node in self.children)

        leftover: Node | None = None
        node_override: Node | None = None
        if len(layouts) == 1 and layouts[0].layout.leftover is not None:
            node_override = self.clone_without_children(border_bottom=False)(layouts[0].get_node())
            leftover = self.clone_without_children(border_top=False)(layouts[0].layout.leftover)

        return NodeLayout(
            layouts[0].layout.size if layouts else constraints.min_size(),
            layouts,
            node_override=node_override,
            leftover=leftover,
        )


outline: type[Outline] = Outline


@dataclass(frozen=True)
class PositionOffset(Node):

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert len(self.children) == 1
        layout = ctx.layout_node(self.children[0], constraints)
        leftover: Node | None = None
        if layout.layout.leftover is not None:
            if self.can_split() and ctx.can_split:
                leftover = self(layout.layout.leftover)
            else:
                raise LayoutAxisOverflowException(
                    node=self,
                    size=layout.layout.size,
                    constraints=constraints,
                )

        x, y, size = self.get_offset(constraints.max_size(), layout.layout.size)
        # TODO double layout :(
        child_constraints = Constraints(
            constraints.min_width,
            size.width,
            constraints.min_height,
            size.height,
        )
        layout = ctx.layout_node(self.children[0], child_constraints, x=x, y=y)
        return NodeLayout(size, (layout,), leftover=leftover)

    def get_offset(self, max_size: Size, child_size: Size) -> tuple[float, float, Size]:
        raise NotImplementedError("get_offset must be implemented by a subclass")

    def can_split(self) -> bool:
        return False


@dataclass(frozen=True)
class Right(PositionOffset):
    def get_offset(self, max_size: Size, child_size: Size) -> tuple[float, float, Size]:
        return max_size.width - child_size.width, 0, Size(max_size.width, child_size.height)

    def can_split(self) -> bool:
        return True


right = Right()


@dataclass(frozen=True)
class HCenter(PositionOffset):
    def get_offset(self, max_size: Size, child_size: Size) -> tuple[float, float, Size]:
        return (max_size.width - child_size.width) / 2, 0, Size(max_size.width, child_size.height)

    def can_split(self) -> bool:
        return True


h_center = HCenter()


class Center(PositionOffset):
    def get_offset(self, max_size: Size, child_size: Size) -> tuple[float, float, Size]:
        return (
            (max_size.width - child_size.width) / 2,
            (max_size.height - child_size.height) / 2,
            max_size,
        )


center = Center()


class Bottom(PositionOffset):
    def get_offset(self, max_size: Size, child_size: Size) -> tuple[float, float, Size]:
        return 0, max_size.height - child_size.height, Size(child_size.width, max_size.height)


bottom = Bottom()


class VCenter(PositionOffset):
    def get_offset(self, max_size: Size, child_size: Size) -> tuple[float, float, Size]:
        return 0, (max_size.height - child_size.height) / 2, Size(child_size.width, max_size.height)


v_center = VCenter()


@dataclass(frozen=True)
class Padding(Node):
    left: float = 0
    top: float = 0
    right: float = 0
    bottom: float = 0

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        if len(self.children) == 0:
            return NodeLayout(constraints.min_size(), ())
        assert len(self.children) == 1
        if constraints.max_width < self.left + self.right:
            raise LayoutCrossAxisOverflowException(
                node=self,
                constraints=constraints,
                size=Size(self.left + self.right, 0),
            )
        if constraints.max_height < self.top:
            raise LayoutAxisOverflowException(
                node=self,
                constraints=constraints,
                size=Size(self.left + self.right, self.top),
            )
        new_constraints = constraints.shrink_by(self.left + self.right, self.top + self.bottom)

        layout = ctx.layout_node(
            self.children[0],
            new_constraints,
            x=self.left,
            y=self.top,
        )

        leftover = None
        if layout.layout.leftover is not None:
            size = Size(
                layout.layout.size.width + self.left + self.right,
                constraints.max_height,
            )
            leftover = self.clone_without_children(top=0)(layout.layout.leftover)
        else:
            size = Size(
                layout.layout.size.width + self.left + self.right,
                layout.layout.size.height + self.top + self.bottom,
            )

        return NodeLayout(
            size,
            (layout,),
            leftover=leftover,
        )


padding = Padding


@dataclass(frozen=True)
class Flow(Node):
    """Simple flow, node by node with node-wrapping to the next 'line'."""

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:

        max_row_width = 0.0

        children = list(self.children)
        children.reverse()  # For speed?

        leftover_constraints = constraints
        row_constraints = leftover_constraints
        children_layouts = []

        row_y = 0.0
        while children:
            row_height = 0.0
            row_width = 0.0
            while children:
                node = children[-1]
                try:
                    child_layout = ctx.layout_node(
                        node,
                        row_constraints,
                        x=row_width,
                        y=row_y,
                    )
                except LayoutAxisOverflowException as e:
                    # Can not split yet, just raise full
                    raise LayoutAxisOverflowException(
                        node=self,
                        constraints=e.constraints,
                        size=e.size,
                    )
                except LayoutCrossAxisOverflowException:
                    break

                children_layouts.append(child_layout)
                row_constraints = row_constraints.shrink_by(child_layout.layout.size.width, 0)
                row_height = max(row_height, child_layout.layout.size.height)
                row_width += child_layout.layout.size.width
                children.pop()

            leftover_constraints.shrink_by(0, row_height)
            row_constraints = leftover_constraints
            max_row_width = max(max_row_width, row_width)
            row_y += row_height

        children_layouts.reverse()

        return NodeLayout(Size(max_row_width, row_y), tuple(children_layouts))


flow = Flow()


@dataclass(frozen=True)
class MinSize(Node):
    width: float
    height: float

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert len(self.children) == 1
        return super().layout(ctx, constraints.set_min_size(Size(self.width, self.height)))


ensure_size: type[MinSize] = MinSize


@dataclass(frozen=True)
class HDivide(Node):
    divisions: list[float]
    direction = Size(1, 0)
    can_split = False

    def __post_init__(self) -> None:
        assert self.divisions

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert len(self.children) == len(
            self.divisions
        ), f"Number of children {len(self.children)} does not match divisions: {self.divisions}"
        ctx.can_split = self.can_split

        infinite_divisions = sum(1 for c in self.divisions if c == INFINITY)
        divisions_total_width = sum(c for c in self.divisions if c != INFINITY)

        infinite_column_width = (
            (
                (constraints.max_width if self.direction.width else constraints.max_height)
                - divisions_total_width
            )
            / infinite_divisions
            if infinite_divisions
            else 0
        )

        layouts = []
        axis_position = 0.0
        for division, node in zip(self.divisions, self.children):
            axis_size = division if division != INFINITY else infinite_column_width
            pos = self.direction.mul(Size(axis_position, axis_position))
            size = Size(
                axis_size if self.direction.width else constraints.max_width,
                axis_size if self.direction.height else constraints.max_height,
            )

            layout = ctx.layout_node(node, size.to_constraints_max(), x=pos.width, y=pos.height)
            layouts.append(layout)
            axis_position += axis_size
        return NodeLayout(
            Size(
                axis_position if self.direction.width else constraints.max_width,
                axis_position if self.direction.height else constraints.max_height,
            ),
            tuple(layouts),
        )


@dataclass(frozen=True)
class VDivide(HDivide):
    direction = Size(0, 1)
    can_split = False  # TODO implement split for VDivide


h_divide: type[HDivide] = HDivide
v_divide: type[VDivide] = VDivide
