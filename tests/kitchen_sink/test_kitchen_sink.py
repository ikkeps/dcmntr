import itertools
from pathlib import Path
from typing import Callable

from dcmntr.layout_query import LayoutQuery
from dcmntr.paging import (
    render_multipage_document,
    layout_multipage_document,
    render_multipage,
    page_break,
)

from tests.kitchen_sink.style import *

SNAPSHOTS_PATH = Path(__file__).parent / "kitchen_sink_snapshots"


def page_structure(content: Node, page_content_lookup_cache: LayoutQuery | None = None) -> Node:
    background = right(
        padding(top=12, right=44)(
            layers(
                outline(fill=(230, 230, 240), border_color=None)(box(width=80, height=INFINITY)),
                padding(left=2, right=2)(simple_text("dcmntr", font=h2_font, color="white")),
            ),
        ),
    )

    first_h2 = "FIXME use page_content_lookup_cache.get_layout_by_node_class()"
    header = right(
        bottom(padding(bottom=10, right=20)(simple_text(first_h2, font=p_font, color="black")))
    )

    page_number = (
        page_content_lookup_cache.page_idx + 1 if page_content_lookup_cache is not None else 999999
    )

    footer = h_center(simple_text(f"Page {page_number}", font=p_font, color="black"))

    return layers(
        background,
        v_divide([100, INFINITY, 50])(
            box()(header),
            h_divide([100, INFINITY, 100])(box(), content, box()),
            box()(footer),
        ),
    )


def table_like(*rows: list[Node]) -> Node:
    return v_divide([80] * len(rows))(
        *(
            h_divide([INFINITY] * len(row))(
                *(
                    padding(left=1, top=1)(
                        outline(border_color="gray")(box()(padding(4, 4, 4, 4)(n)))
                    )
                    for n in row
                )
            )
            for row in rows
        )
    )


highlight_size = outline(border_color="lightblue", border_width=1, fill=None)


def kitchen_sink() -> Node:
    ctx = Ctx()

    def figure(ctx: Ctx, name: str, caption: str | Node) -> Node:
        return padding(top=10, bottom=2)(
            txt(
                p_bold(f"Figure {ctx.anchors.add(name, len(ctx.anchors)+1) }. "),
                caption,
            )
        )

    def figure_ref(name: str) -> Node:
        return underline(color="blue")(
            deferred(materialize=lambda ctx: p_bold(f"Figure {ctx.anchors.get(name)}"))
        )

    doc = v_stack(
        h1("dcmntr"),
        right(p(""""Kitchen sink" example""")),
        h2("Basics"),
        txt(
            "Every node in ",
            code("basic_layout"),
            " usually shrinks to the smallest size",
            "that can fit all the children, except ",
            code("expand()"),
            " node, which will expand as much as it's",
            "parent allows. ",
            br,
            "Boundaries of elements are highlighted ",
            highlight_size(p("like this")),
            " for understanding",
        ),
        h2("Alignment"),
        p("There are various node wrapper that aligns node within parent."),
        p("This is done purely by moving the wrapped node layout to appropriate location"),
        p("Helpers are composable so vertical and horizontal can be combined."),
        br,
        padding(left=100, right=100)(
            v_stack(
                table_like(
                    [
                        highlight_size(code("n")),
                        h_center(highlight_size(code("h_center(n)"))),
                        right(highlight_size(code("right(n)"))),
                    ],
                    [
                        v_center(highlight_size((code("v_center(n)")))),
                        center(highlight_size(code("center(n)"))),
                        v_center(highlight_size(right(highlight_size(code("v_center(right(n))"))))),
                    ],
                    [
                        bottom(highlight_size(code("bottom(n)"))),
                        h_center(
                            highlight_size(bottom(highlight_size(code("h_center(bottom(n))"))))
                        ),
                        bottom(highlight_size(right(highlight_size(code("bottom(right(n))"))))),
                    ],
                ),
                figure(ctx, "alignments", "Child alignment options"),
            )
        ),
        h2("Stacking"),
        h3("Vertical v_stack(h_center(...))"),
        highlight_size(
            v_stack(
                *map(
                    h_center,
                    itertools.islice(
                        itertools.cycle(
                            [
                                outline(fill="yellow")(box(200, 40)(p("1"))),
                                outline(fill="lightblue")(
                                    box(INFINITY, 20)(p("width=INFINITY  will expand whole stack"))
                                ),
                                outline(fill="red")(box(30, 33)(p("2"))),
                                outline(fill="cyan")(box(90, 21)(p("3"))),
                            ]
                        ),
                        3,
                    ),
                )
            )
        ),
        h3("Horizontal h_stack(v_center(..))"),
        box(height=200)(
            highlight_size(
                h_stack(
                    *map(
                        v_center,
                        [
                            outline(fill="yellow")(box(40, 70)(p("1"))),
                            outline(fill="red")(box(30, 32)(p("2"))),
                            outline(fill="cyan")(box(50, 50)(p("3"))),
                        ],
                    )
                ),
            )
        ),
        h2("Regular flow(...)"),
        p('''Places element after element, wrapping to the next "new line"'''),
        highlight_size(
            flow(
                *itertools.islice(
                    itertools.cycle(
                        [
                            outline(fill="lightgreen")(box(123, 15)),
                            outline(fill="yellow")(box(80, 33)),
                            outline(fill="lightblue")(box(200, 24)),
                            outline(fill="pink")(box(123, 27)),
                            outline(fill="cyan")(box(140, 5)),
                        ]
                    ),
                    15,
                )
            )
        ),
        h2("Layers"),
        txt(
            code("layers"),
            " can be rendered on top of one another. ",
            "The size of ",
            code("layers(...)"),
            "is the biggest size that can fit all the children",
        ),
        figure(ctx, "layers", "Simple layering example"),
        highlight_size(
            layers(
                outline(fill="lightgreen")(box(200, 100)(p("first layer"))),
                padding(top=10, left=10)(
                    outline(fill="pink")(box(130, 100)(p("second layer"))),
                ),
            )
        ),
        page_break,
        h2("Divisions"),
        txt(
            "With ",
            code("h_divide"),
            " or ",
            code("v_divide"),
            " you can divide free space like this:",
            code("h_divide([INFINITY, 100, INFINITY, 200])("),
            "children",
            code(")"),
            ". Infinite elements will be given the same size, ",
            "to fill the whole space. ",
            "You can nest division elements like this: ",
            code("v_divide([30,60,20])(h_divide(...)(...), h_divide(...)(...), ...)"),
            " here is the example:\n ",
        ),
        highlight_size(
            v_divide([30, 60, 20])(
                h_divide([INFINITY, 100, INFINITY, 200])(
                    outline()(box()(center(code("INFINITY")))),
                    outline()(box()(center(p("100")))),
                    outline()(box()(center(code("INFINITY")))),
                    outline()(box()(center(p("200")))),
                ),
                h_divide([100, 200])(
                    outline()(box()(center(p("100")))),
                    outline()(box()(center(p("200")))),
                ),
                h_divide([INFINITY])(
                    outline()(box()(center(code("INFINITY")))),
                ),
            )
        ),
        h2("Document is code"),
        p("With python code you can generate anything in any way you want, but there are helpers"),
        h3("Deferred layout with deferred(...)"),
        txt(
            "Place ",
            code("deferred(lambda ctx: ...)"),
            "in the layout to defer some calculations",
            "You can materialize all of the deferred in the layout by using ",
            code("materialize_deferred(ctx, layout)"),
        ),
        br,
        p("Use cases are:"),
        h4("Automatic headers numbering"),
        txt(
            "You don't need deferred for that, but, ",
            "by using ",
            code("helpers.SectionNumbering"),
            " helper ",
            "and deferred you can avoid typing ",
            code('h2(ctx, "A header")'),
            "instead of just ",
            code('h2("A header")'),
        ),
        h4("Automatic figure numbering and referencing"),
        txt(
            "For example, alignment options are on ",
            figure_ref("alignments"),
            " and simple layers example is ",
            figure_ref("layers"),
        ),
        page_break,
        h2("Paging"),
        txt(
            "There is a paging support with",
            " page structure ",
            "(content that is present on every page). ",
            "The content window size is calculated",
            "automatically based on the page structure. ",
            code("layout_multipage_document(...)"),
            " gets ",
            code("page_structure_f"),
            " callable that gets Node ",
            "(page content)",
            " and return Node. ",
            "(full page layout). ",
            "Each page's content being laid out",
            " and passed to ",
            code("page_structure_f"),
            " which can use page content to e.g.",
            "insert header that changes depending ",
            "on captions presented on the current page. ",
        ),
    )
    return materialize_deferred(ctx, doc)


def test_kitchen_sink(image_snapshot: Callable[..., None]) -> None:
    page_size = Size(210 * 5, 297 * 5)
    pages = layout_multipage_document(
        page_size,
        page_structure_f=page_structure,
        content=kitchen_sink(),
        debug=True,
    )
    for idx, img in enumerate(render_multipage_document(pages)):
        image_snapshot(img, SNAPSHOTS_PATH / f"kitchen_sink_{idx}.png")
