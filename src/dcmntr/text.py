from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

from PIL import ImageFont, features as PIL_features
from PIL.ImageFont import FreeTypeFont

from dcmntr.basic_layout import Color
from dcmntr.core import LeafNode, Layout, ImageDrawCtx, NodeLayoutCtx, Constraints, NodeLayout, Size

__all__ = [
    "Fonts",
    "Font",
    "simple_text",
    "SimpleText",
]


@dataclass(frozen=True)
class Font:
    cache: Fonts
    pil_font: FreeTypeFont
    name: str
    size: int
    bold: bool
    italic: bool

    def same_but(self, **kwargs: Any) -> Font:
        return self.cache.load(
            **{
                "name": self.name,
                "size": self.size,
                "bold": self.bold,
                "italic": self.italic,
                **kwargs,
            }
        )


@dataclass
class Fonts:
    cache: dict[tuple[str, int, bool, bool], Font] = field(default_factory=dict)

    def load(self, name: str, size: int, bold: bool = False, italic: bool = False) -> Font:
        key = (name, size, bold, italic)
        font = self.cache.get(key)
        if font is not None:
            return font

        pil_font = self.load_from_fonttools(name, size, bold, italic)

        font = Font(
            self,
            pil_font=pil_font,
            name=name,
            size=size,
            bold=bold,
            italic=italic,
        )

        self.cache[key] = font
        return font

    def load_from_fonttools(self, name: str, size: int, bold: bool, italic: bool) -> FreeTypeFont:
        style = []
        if bold:
            style.append("Bold")
        if italic:
            style.append("Italic")

        pattern = name + (":" + ":".join(style) if style else "")
        path = subprocess.check_output(
            ["fc-match", "-f", "%{file}", pattern],
            text=True,
        ).strip()
        # FIXME handle not found?
        return ImageFont.truetype(
            path,
            size,
            layout_engine=ImageFont.Layout.RAQM,
        )


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
