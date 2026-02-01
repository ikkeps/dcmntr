from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Callable, Generator, Protocol, Iterable

from PIL import Image

from dcmntr.basic_layout import Color
from dcmntr.core import *
from dcmntr.core import NodeLayoutCtx, Node, Constraints, NodeLayout, Size, LayoutCtx
from dcmntr.layout_query import LayoutQuery
from dcmntr.render import draw_document_pil


class PageStructureCallable(Protocol):
    def __call__(self, content: Node, page_content_lookup_cache: LayoutQuery | None = None) -> Node:
        pass


def layout_multipage_document(
    page_size: Size, page_structure_f: PageStructureCallable, content: Node
) -> Iterable[tuple[Size, Layout]]:
    content_x, content_y, content_size = measure_content_size(page_size, page_structure_f)

    page_index = 0
    page_content: Node | None = content
    while page_content is not None:
        ctx = LayoutCtx(page_index=page_index)
        content_layout = ctx.page_ctx().layout_node(
            page_content, constraints=content_size.to_constraints_max(), x=content_x, y=content_y
        )

        # XXX stip leftover so we can fit anything (weird)
        page = page_structure_f(
            PreLaidOutNode(content_layout.strip_leftover()),
            LayoutQuery(content_layout, page_index),
        )
        page_layout = ctx.page_ctx().layout_node(page, constraints=page_size.to_constraints_max())
        yield page_size, page_layout
        page_content = content_layout.layout.leftover
        page_index += 1


def render_multipage_document(
    pages_generator: Iterable[tuple[Size, Layout]],
    background_color: Color = "white",
) -> Generator[Image.Image, None, None]:

    for page_size, page_layout in pages_generator:
        img = Image.new("RGBA", (ceil(page_size.width), ceil(page_size.height)), background_color)
        draw_document_pil(page_layout, img)
        yield img


def measure_content_size(
    page_size: Size, page_f: PageStructureCallable
) -> tuple[float, float, Size]:
    page_constraints = page_size.to_constraints_max()
    ctx = LayoutCtx()
    page_ctx = ctx.container_ctx()  # Disallow split

    content_x: float | None = None
    content_y: float | None = None
    size: Size | None = None

    def save_measurements(x: float, y: float, content_size: Size) -> None:
        nonlocal content_x, content_y, size
        content_x = x
        content_y = y
        size = content_size

    measure = ContentMeasurement(save_measurements)

    page_ctx.layout_node(page_f(measure), page_constraints)

    assert (
        (content_x is not None) and (content_y is not None) and (size is not None)
    ), "page function does not seems to place argument into the layout"

    return content_x, content_y, size


@dataclass(frozen=True)
class PreLaidOutNode(Node):
    layout_to_return: Layout

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert not self.children

        node_layout = self.layout_to_return.layout
        if node_layout.node_override is None:
            node_layout = node_layout.set_node_override(self.layout_to_return.node)
        return node_layout


@dataclass(frozen=True)
class ContentMeasurement(Node):

    report_measurements_f: Callable[[float, float, Size], None]

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert not self.children
        size = constraints.max_size()
        x, y = ctx.x, ctx.y
        self.report_measurements_f(x, y, size)

        return NodeLayout(size, children=())


@dataclass(frozen=True)
class NoBrake(Node):
    """Essentially disables splitting children by page break."""

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        ctx.can_split = False
        return super().layout(ctx, constraints)


no_break = NoBrake()


def render_multipage(
    page_size: Size,
    document: Node | None,
    background_color: Color = "white",
) -> Generator[Image.Image, None, None]:

    page_constraints = page_size.to_constraints_max()

    while document is not None:
        ctx = LayoutCtx()
        layout = ctx.page_ctx().layout_node(document, page_constraints)
        img = Image.new("RGBA", (ceil(page_size.width), ceil(page_size.height)), background_color)
        draw_document_pil(layout, img)
        yield img
        document = layout.layout.leftover


def document_to_pages(doc: Node, page_size: Size) -> Generator[Node, None, None]:
    page_constraints = page_size.to_constraints_max()

    page: Node | None = doc

    page_index: int = 0
    while page is not None:
        ctx = LayoutCtx(page_index=page_index)
        node_ctx = ctx.page_ctx()

        layout = node_ctx.layout_node(page, page_constraints)
        yield Page(page_size=page_size)(page)
        page = layout.layout.leftover
        page_index += 1


@dataclass(frozen=True)
class Page(Node):
    page_size: Size

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        assert len(self.children) == 1
        page = self.children[0]
        ctx.can_split = True
        layout = ctx.layout_node(
            page,
            self.page_size.to_constraints_max(),
        )
        layout = layout.strip_leftover()
        return NodeLayout(self.page_size, (layout,))
