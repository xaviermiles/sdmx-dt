from __future__ import annotations  # for Item self-reference

from abc import ABC
from typing import Optional

from sdmx_dt.information_model.base import MaintainableArtefact, NameableArtefact


class Item(NameableArtefact, ABC):
    def __init__(self, parent: Optional[Item] = None, num_children: int = 0) -> None:
        self.parent = parent
        self.children = [Item() for _ in range(num_children)]  # 0..*


class ItemScheme(MaintainableArtefact, ABC):
    def __init__(self, is_partial: bool, num_items: int = 0, **kwargs) -> None:
        self.is_partial = is_partial
        # TODO: how to inherit self.items but use different class (eg Category rather than Item)
        self.items = [Item() for _ in range(num_items)]  # 0..*
        super().__init__(**kwargs)
