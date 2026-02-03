from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Generator, Callable, Iterable
from weakref import WeakKeyDictionary

from PIL import Image
from PIL.ImageDraw import ImageDraw

__all__ = [
    "INFINITY",
    "Constraints",
    "Size",
    "Layout",
    "NodeLayout",
    "Node",
    "LeafNode",
    "deferred",
    "materialize_deferred",
    "walk_layout",
    "LayoutCtx",
    "NodeLayoutCtx",
    "LayoutAxisOverflowException",
    "LayoutCrossAxisOverflowException",
    "ImageDrawCtx",
]


INFINITY = math.inf


@dataclass(frozen=True)
class Constraints:

    # min and max are inclusive
    min_width: float
    max_width: float
    min_height: float
    max_height: float

    def __str__(self) -> str:
        return f"[{self.min_width}-{self.max_width}]x[{self.min_height}-{self.max_height}]"

    def can_fit(self, size: Size) -> bool:
        return (
            (size.width >= self.min_width)
            and (size.width <= self.max_width)
            and (size.height >= self.min_height)
            and (size.height <= self.max_height)
        )

    def is_size_too_small(self, size: Size) -> bool:
        return (size.width < self.min_width) or (size.height < self.min_height)

    def is_size_too_big(self, size: Size) -> bool:
        return (size.width > self.max_width) or (size.height > self.max_height)

    def constrained_size(self, size: Size) -> Size:
        return Size(
            min(max(size.width, self.min_width), self.max_width),
            min(max(size.height, self.min_height), self.max_height),
        )

    def set_min_size(self, size: Size) -> Constraints:
        return Constraints(
            size.width,
            self.max_width,
            size.height,
            self.max_height,
        )

    def is_overflows(self, size: Size) -> tuple[bool, bool]:
        right = size.width > self.max_width
        down = size.height > self.max_height
        return right, down

    def shrink_by(self, width: float, height: float) -> Constraints:
        return Constraints(
            self.min_width,
            self.max_width - width,
            self.min_height,
            self.max_height - height,
        )

    def is_valid(self) -> bool:
        return (self.min_width <= self.max_width and self.min_height <= self.max_height) and (
            self.min_width >= 0 and self.min_height >= 0
        )

    def is_infinite(self) -> bool:
        return self.max_width == INFINITY or self.max_height == INFINITY

    def min_size(self) -> Size:
        return Size(self.min_width, self.min_height)

    def max_size(self) -> Size:
        return Size(self.max_width, self.max_height)

    def extend_size_right(self, size: Size) -> Size:
        return Size(self.max_width, size.height)

    def extend_size_down(self, size: Size) -> Size:
        return Size(size.width, self.max_height)


@dataclass(frozen=True)
class Size:
    width: float
    height: float

    def add(self, width: float, height: float) -> Size:
        return Size(self.width + width, self.height + height)

    def max(self, other: Size) -> Size:
        return Size(max(self.width, other.width), max(self.height, other.height))

    def mul(self, other: Size) -> Size:
        return Size(self.width * other.width, self.height * other.height)

    def to_strict_constraints(self) -> Constraints:
        return Constraints(self.width, self.width, self.height, self.height)

    def to_constraints_max(self) -> Constraints:
        return Constraints(0, self.width, 0, self.height)

    def is_infinite(self) -> bool:
        return self.width == INFINITY or self.height == INFINITY

    @classmethod
    def that_fit_layouts(cls, iterable: Iterable[Layout]) -> Size:
        width = 0.0
        height = 0.0
        for l in iterable:
            width = max(width, l.layout.size.width)
            height = max(height, l.layout.size.height)

        return Size(width, height)


@dataclass(frozen=True)
class NodeLayout:
    size: Size
    children: tuple[Layout, ...]
    cached: Any = None
    node_override: Node | None = None
    leftover: Node | None = None
    tags: WeakKeyDictionary[Node, Any] = field(default_factory=WeakKeyDictionary)

    def update_size_inplace(self, size: Size) -> None:
        object.__setattr__(self, "size", size)

    def set_node_override(self, node_override: Node) -> NodeLayout:
        return replace(self, node_override=node_override)

    def strip_leftover(self) -> NodeLayout:
        return replace(
            self,
            leftover=None,
            children=tuple(l.strip_leftover() for l in self.children),
        )


@dataclass(frozen=True, init=False)
class Node:
    children: tuple[Node, ...] = field(
        default=(),
        init=False,
        repr=False,
    )

    def clone_without_children(self, **values: Any) -> Node:
        children = values.pop("children", ())
        clone = replace(self, **values)
        object.__setattr__(clone, "children", children)
        return clone

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        # Default implementation for single children or empty node
        assert len(self.children) <= 1
        layouts = tuple(ctx.layout_node(node, constraints) for node in self.children)
        return NodeLayout(layouts[0].layout.size if layouts else constraints.min_size(), layouts)

    def draw_image(self, x: float, y: float, layout: Layout, draw_ctx: ImageDrawCtx) -> None:
        # Called before children draw_* functions
        pass

    def __call__(self, *children: Node) -> Node:
        # Replaces children of Node in a functional way
        return self.clone_without_children(children=children)


@dataclass(frozen=True)
class LeafNode(Node):

    def __call__(self, *children: Node) -> Node:
        if children:
            raise ValueError(f"Can not add children nodes to the leaf node {self}")
        return super().__call__(*children)


@dataclass(frozen=True)
class DeferredNode(LeafNode):
    materialize: Callable[[Any], Node]

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        raise ValueError("DeferredNode can not do layout, materialize it first")

    def draw_image(self, x: float, y: float, layout: Layout, draw_ctx: ImageDrawCtx) -> None:
        raise ValueError("DeferredNode can not be rendered, materialize it first")


deferred = DeferredNode


def materialize_deferred(context: Any, node: Node) -> Node:
    if isinstance(node, DeferredNode):
        node = node.materialize(context)
    return node(*(materialize_deferred(context, child) for child in node.children))


@dataclass(frozen=True)
class Layout:
    node: Node
    layout: NodeLayout
    x: float
    y: float

    def get_node(self) -> Node:
        return self.node if self.layout.node_override is None else self.layout.node_override

    def strip_leftover(self) -> Layout:
        return replace(self, layout=self.layout.strip_leftover())


@dataclass
class LayoutCtx:

    debug: bool = False
    page_index: int = 0

    def page_ctx(self) -> NodeLayoutCtx:
        return NodeLayoutCtx(
            ctx=self,
            can_split=True,
        )

    def container_ctx(self) -> NodeLayoutCtx:
        return NodeLayoutCtx(
            ctx=self,
            can_split=False,
        )


@dataclass
class NodeLayoutCtx:
    ctx: LayoutCtx
    can_split: bool
    x: float = 0
    y: float = 0

    # Debug only
    node: Node | None = None
    parent: NodeLayoutCtx | None = None

    def get_current_path_readable(self) -> str:
        return " > ".join(
            (type(c.node).__name__ if c.node is not None else f"Page #{self.ctx.page_index}")
            for c in self.get_current_path()
        )

    def layout_node(
        self,
        node: Node,
        constraints: Constraints,
        x: float = 0,
        y: float = 0,
    ) -> Layout:

        node_ctx = self.clone_for_child(node, x, y)
        if self.ctx.debug:
            print(
                f"{node_ctx.get_current_path_readable()} <{node_ctx.x},{node_ctx.y}> {constraints} "
            )
        layout = node.layout(node_ctx, constraints)

        if self.ctx.debug:
            print(
                f"{node_ctx.get_current_path_readable()} ({layout.node_override}) <{node_ctx.x},{node_ctx.y}> can_split={node_ctx.can_split} {constraints} "
                + f" --> {layout.size}"
            )

        if constraints.is_size_too_small(layout.size):
            layout.update_size_inplace(
                Size(
                    max(layout.size.width, constraints.min_width),
                    max(layout.size.height, constraints.min_height),
                )
            )

        if constraints.is_size_too_big(layout.size):
            overflow_right, overflow_down = constraints.is_overflows(layout.size)
            if overflow_down and not overflow_right:
                raise LayoutAxisOverflowException(
                    node=node,
                    size=layout.size,
                    constraints=constraints,
                )
            elif overflow_right:
                raise LayoutCrossAxisOverflowException(
                    node=node,
                    size=layout.size,
                    constraints=constraints,
                )

        if layout.leftover is None:
            if any(c.layout.leftover is not None for c in layout.children):
                raise RuntimeError(
                    f"{node_ctx.get_current_path_readable()} does not handle children .leftover"
                )
        elif not self.can_split:
            raise RuntimeError(
                f"{node_ctx.get_current_path_readable()} asked to not split, splits anyway"
            )

        l = Layout(
            node=node,
            x=node_ctx.x,
            y=node_ctx.y,
            layout=layout,
        )
        return l

    def clone_for_child(self, node: Node, x: float, y: float) -> NodeLayoutCtx:
        return replace(
            self,
            parent=self,
            node=node,
            x=self.x + x,
            y=self.y + y,
        )

    def get_current_path(self) -> list[NodeLayoutCtx]:
        ctx: NodeLayoutCtx | None = self
        chain = []
        while ctx is not None:
            chain.append(ctx)
            ctx = ctx.parent
        chain.reverse()
        return chain


@dataclass
class LayoutAxisOverflowException(Exception):
    node: Node
    size: Size
    constraints: Constraints

    def __str__(self) -> str:
        return repr(self)


@dataclass
class LayoutCrossAxisOverflowException(Exception):
    node: Node
    size: Size
    constraints: Constraints

    def __str__(self) -> str:
        return repr(self)


@dataclass(frozen=True)
class ImageDrawCtx:
    image: Image.Image
    draw: ImageDraw


def walk_layout(layout: Layout) -> Generator[tuple[float, float, Layout], None, None]:
    yield layout.x, layout.y, layout
    for child_layout in layout.layout.children:
        yield from walk_layout(child_layout)
