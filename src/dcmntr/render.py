from math import ceil

from PIL import Image, ImageDraw

from dcmntr.basic_layout import Color
from dcmntr.core import *


def render_into_image(
    filename: str,
    width: int,
    height: int,
    document: Node,
    background_color: Color = "white",
) -> Image.Image:
    constraints = Size(width, height).to_constraints_max()
    ctx = LayoutCtx()
    layout = ctx.container_ctx().layout_node(document, constraints)
    img = Image.new("RGBA", (ceil(width), ceil(height)), background_color)
    draw_document_pil(layout, img)
    img.save(filename)
    return img


def draw_document_pil(layout: Layout, image: Image.Image) -> None:
    draw_ctx = ImageDrawCtx(
        image=image,
        draw=ImageDraw.Draw(image),
    )
    for x, y, node_layout in walk_layout(layout):
        node_layout.get_node().draw_image(x, y, node_layout, draw_ctx)
