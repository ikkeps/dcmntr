from dataclasses import dataclass, field
from typing import Any

from dcmntr.core import Layout, Tag


@dataclass
class LayoutQuery:
    layout: Layout
    page_idx: int
    _tag_cache: dict[str, list[Any]] = field(default_factory=dict, init=False, repr=False)
    _tag_cache_built: bool = field(default=False, init=False, repr=False)

    def _build_tag_cache(self) -> None:
        if self._tag_cache_built:
            return

        cache: dict[str, list[Any]] = {}

        def visit(layout: Layout) -> None:
            node = layout.get_node()
            if isinstance(node, Tag):
                cache.setdefault(node.key, []).append(node.value)
            for child in layout.layout.children:
                visit(child)

        visit(self.layout)
        self._tag_cache = cache
        self._tag_cache_built = True

    def get_values_by_tag(self, key: str) -> list[Any]:
        self._build_tag_cache()
        return self._tag_cache.get(key, [])
