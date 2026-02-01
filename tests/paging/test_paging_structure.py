from pathlib import Path
from typing import Callable

from dcmntr.core import *
from dcmntr.basic_layout import *
from dcmntr.font import Fonts
from dcmntr.layout_query import LayoutQuery
from dcmntr.paging import layout_multipage_document, render_multipage_document

SNAPSHOTS_PATH = Path(__file__).parent / "paging_snapshots"

text_font = Fonts().load_builtin(14)


def simple_page_structure(
    content: Node, page_content_lookup_cache: LayoutQuery | None = None
) -> Node:
    page_number = (
        page_content_lookup_cache.page_idx if page_content_lookup_cache is not None else 9999
    )
    return v_divide([35, INFINITY, 30])(
        outline(border_color="black", border_top=False, border_left=False, border_right=False)(
            box()(
                center(
                    simple_text("Simple page layout example", color="black", font=text_font),
                )
            )
        ),
        padding(left=50)(
            box(width=200)(content),
        ),
        outline(border_color="black", border_right=False, border_left=False, border_bottom=False)(
            box()(simple_text(f"Page {page_number}", color="black", font=text_font))
        ),
    )


def simple_page_content() -> Node:
    return v_stack(
        *(
            padding(1, 1, 1, 1)(outline(border_color="blue", border_width=2)(box(150, 73)))
            for _ in range(11)
        )
    )


def test_paging_with_structure(image_snapshot: Callable[..., None]) -> None:

    page_size = Size(300, 450)
    pages = layout_multipage_document(
        page_size, page_structure_f=simple_page_structure, content=simple_page_content()
    )
    for idx, img in enumerate(render_multipage_document(pages)):
        image_snapshot(img, SNAPSHOTS_PATH / f"simple_paging_{idx}.png")
