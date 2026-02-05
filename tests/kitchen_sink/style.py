from dataclasses import dataclass, field
from dcmntr.helpers import SectionNumbering, Anchors
from dcmntr.core import *
from dcmntr.basic_layout import *
from dcmntr.text import *

text_color = "black"
fonts = Fonts()

p_font = fonts.load("arial", 14, bold=False)
p_font_bold = p_font.same_but(bold=True)
i_font = p_font.same_but(italic=True)
mono_font = fonts.load("mono", 14, bold=True)
h1_font = p_font.same_but(size=24)
h2_font = p_font.same_but(size=18)


@dataclass
class Ctx:
    h: SectionNumbering = field(
        default_factory=lambda: SectionNumbering(
            (SectionNumbering.N, SectionNumbering.az, SectionNumbering.iv)
        )
    )
    anchors: Anchors = field(default_factory=Anchors)


def p(text: str) -> Node:
    return simple_text(text, p_font, color=text_color)


def p_bold(text: str) -> Node:
    return simple_text(text, p_font_bold, color=text_color)


def code(text: str) -> Node:
    return simple_text(text, mono_font, color=text_color)


br = box(height=1)


def underline(color: Color, width: int = 1) -> Node:
    return outline(
        border_left=False,
        border_top=False,
        border_right=False,
        border_color=color,
        border_width=width,
    )


def h1(text: str) -> Node:
    return simple_text(text, font=h1_font, color=text_color, spacing=5)


@with_tag("h2")
def h2(text: str) -> Node:
    return padding(top=16, bottom=4)(
        underline("gray", width=1)(
            deferred(
                lambda ctx: simple_text(
                    f"{ctx.h.next(2)}. " + text,
                    font=h2_font,
                    color=text_color,
                    spacing=2,
                )
            )
        ),
    )


def h3(text: str) -> Node:
    return padding(top=10, bottom=4)(
        underline(color="gray", width=2)(
            deferred(
                lambda ctx: txt(
                    f"{ctx.h.next(3)}. " + text,
                )
            )
        )
    )


def h4(text: str) -> Node:
    return padding(top=8, bottom=2)(
        underline(color="gray")(
            deferred(
                lambda ctx: italic_word(
                    f"{ctx.h.next(4)}. " + text,
                )
            )
        )
    )


def txt(*elements: Node | str) -> Node:
    """Pretty ugly poor's man rich text formatting."""
    nodes: list[Node] = []
    for e in elements:
        if isinstance(e, Node):
            node = e
        elif isinstance(e, str):
            node = p(e)
        else:
            raise RuntimeError("Unknown element")
        nodes.append(node)

    return flow(*nodes)


def italic_word(t: str) -> Node:
    return simple_text(t, font=i_font, color=text_color)
