from __future__ import annotations
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from typing import cast, Any

from PIL import ImageFont
from PIL.ImageFont import FreeTypeFont


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
