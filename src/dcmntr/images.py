from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from dcmntr.core import *


@dataclass(frozen=True)
class SimpleImage(LeafNode):
    # FIXME better way of scaling the image

    filename: str | Path
    expand: bool = True
    preserve_aspect_ratio: bool = True
    image: Image.Image = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "image", self.load_image())

    def draw_image(self, x: float, y: float, layout: Layout, draw_ctx: ImageDrawCtx) -> None:
        scaled_img = layout.layout.cached
        draw_ctx.image.paste(scaled_img, (int(x), int(y)))

    def layout(self, ctx: NodeLayoutCtx, constraints: Constraints) -> NodeLayout:
        img_size = self.original_image_size()
        if img_size.width <= 0 or img_size.height <= 0:
            raise ValueError("Size must be positive")
        if self.expand:
            if self.preserve_aspect_ratio:
                size = self.expand_size_preserve_aspect_ratio(img_size, constraints)
            else:
                size = constraints.max_size()
        else:
            size = self.ensure_min_size_preserve_aspect_ratio(img_size, constraints)

        img = self.image.resize((int(size.width), int(size.height)))
        return NodeLayout(size, (), cached=img)

    def expand_size_preserve_aspect_ratio(self, size: Size, constraints: Constraints) -> Size:
        if size.width <= 0 or size.height <= 0:
            raise ValueError("Size must be positive")

        scale = min(
            constraints.max_width / size.width,
            constraints.max_height / size.height,
        )

        return Size(
            width=size.width * scale,
            height=size.height * scale,
        )

    def ensure_min_size_preserve_aspect_ratio(self, size: Size, constraints: Constraints) -> Size:
        scale = max(
            constraints.min_width / size.width,
            constraints.min_height / size.height,
            1.0,
        )

        return Size(
            width=size.width * scale,
            height=size.height * scale,
        )

    def original_image_size(self) -> Size:
        return Size(self.image.size[0], self.image.size[1])

    def load_image(self) -> Image.Image:
        return Image.open(self.filename)


img_from_file = SimpleImage
