from pathlib import Path
from typing import Callable

from dcmntr.core import *
from dcmntr.basic_layout import *
from dcmntr.text import *
from dcmntr.images import img_from_file
from dcmntr.paging import render_multipage

SNAPSHOTS_PATH = Path(__file__).parent / "images_snapshots"

fonts = Fonts()
p_font = fonts.load("arial", 14, bold=False)


def image_example() -> Node:

    def img_outline(title: str, node: Node) -> Node:
        return padding(right=3, left=3)(
            v_stack(
                simple_text(title, font=p_font, color="black"),
                outline()(padding(1, 1, 1, 1)(node)),
            )
        )

    img = img_from_file(SNAPSHOTS_PATH / "statue.jpg", expand=False, preserve_aspect_ratio=True)
    img_size = img.original_image_size()

    return h_stack(
        img_outline(
            f"Original size\n{img_size.width}x{img_size.height}",
            img,
        ),
        img_outline(
            "Fit to container\nbox(70, 70)",
            box(70, 70)(img_from_file(SNAPSHOTS_PATH / "statue.jpg")),
        ),
        img_outline(
            "Fit to container\nbox(300, 200), no aspect ration preservation",
            box(300, 200)(
                img_from_file(SNAPSHOTS_PATH / "statue.jpg", preserve_aspect_ratio=False)
            ),
        ),
        img_outline(
            "Stretch with ensure_size(150, 120)",
            ensure_size(150, 120)(img_from_file(SNAPSHOTS_PATH / "statue.jpg", expand=False)),
        ),
    )


def test_images(image_snapshot: Callable[..., None]) -> None:
    size = Size(800, 600)
    for idx, img in enumerate(render_multipage(size, image_example())):
        image_snapshot(img, SNAPSHOTS_PATH / f"images_{idx}.png")
