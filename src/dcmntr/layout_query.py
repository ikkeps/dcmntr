from dataclasses import dataclass

from dcmntr.core import Layout


@dataclass
class LayoutQuery:
    layout: Layout
    page_idx: int

    def get_layout_by_node_class(self, cls: type) -> Layout | None:

        def node_layout(layout: Layout) -> Layout | None:
            if isinstance(layout.node, cls):
                return layout
            for c in layout.layout.children:
                l = node_layout(c)
                if l is not None:
                    return l
            return None

        return node_layout(self.layout)
