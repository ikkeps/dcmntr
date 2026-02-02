from pathlib import Path
from typing import Callable
import itertools

from dcmntr.basic_layout import *
from dcmntr.paging import *
from dcmntr.text import *
from dcmntr.paging import render_multipage, document_to_pages

SNAPSHOTS_PATH = Path(__file__).parent / "paging_snapshots"

text_font = Fonts().load("arial", 14, bold=False)


def stack_item(color: str) -> Node:
    return padding(1, 1, 1, 1)(outline(border_color=color, border_width=2)(box(120, 30)))


def outline_page_break() -> tuple[Node, Size, str]:
    return (
        outline(border_width=3, border_color="black")(
            v_stack(
                *itertools.repeat(
                    padding(left=4, right=4, top=2, bottom=2)(stack_item("gray")),
                    7,
                ),
            )
        ),
        Size(150, 170),
        "outline()",
    )


def page_break_single_stack() -> tuple[Node, Size, str]:
    return (
        v_stack(
            *itertools.repeat(
                stack_item("blue"),
                8,
            ),
        ),
        Size(150, 170),
        "v_stack",
    )


def page_break_nested_stacks() -> tuple[Node, Size, str]:
    return (
        v_stack(
            v_stack(
                *itertools.repeat(
                    stack_item("blue"),
                    3,
                ),
            ),
            v_stack(
                *itertools.repeat(
                    stack_item("green"),
                    3,
                ),
            ),
        ),
        Size(150, 170),
        "v_stack_nested",
    )


def page_break_nested_stacks_no_break() -> tuple[Node, Size, str]:
    return (
        v_stack(
            v_stack(
                *itertools.repeat(stack_item("blue"), 3),
            ),
            no_break(
                padding(2, 2, 2, 2)(
                    v_stack(
                        *itertools.repeat(stack_item("green"), 3),
                    )
                )
            ),
        ),
        Size(150, 170),
        "v_stack nested no_break()",
    )


def nice_page(page: Node) -> Node:
    return padding(2, 2, 2, 2)(
        outline(border_top=False, border_left=False, border_color="black")(
            padding(1, 1, 1, 1)(
                outline(border_width=1, border_color="darkgray", fill="white")(
                    padding(2, 2, 2, 2)(page)
                )
            )
        )
    )


def split_examples() -> Node:
    examples = [
        page_break_single_stack(),
        page_break_nested_stacks(),
        page_break_nested_stacks_no_break(),
        outline_page_break(),
    ]

    return flow(
        *(
            padding(5, 5, 5, 5)(
                v_stack(
                    simple_text(name, font=text_font, color="black"),
                    outline(fill="lightgray", border_color=None)(
                        padding(6, 6, 6, 6)(
                            v_stack(
                                *(
                                    padding(5, 5, 5, 5)(nice_page(page))
                                    for page in document_to_pages(h_center(doc), page_size=size)
                                )
                            )
                        )
                    ),
                )
            )
            for doc, size, name in examples
        )
    )


def test_basic_layout_paging(image_snapshot: Callable[..., None]) -> None:
    size = Size(800, 1200)
    for idx, img in enumerate(render_multipage(size, split_examples())):
        image_snapshot(img, SNAPSHOTS_PATH / f"basic_layout_paging_{idx}.png")
