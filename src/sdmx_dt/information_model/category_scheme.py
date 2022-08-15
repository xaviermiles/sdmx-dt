from __future__ import annotations

from typing import Optional

from sdmx_dt.information_model.base import IdentifiableArtefact, MaintainableArtefact
from sdmx_dt.information_model.item_scheme import Item, ItemScheme


class Category(Item):
    def __init__(self, parent: Optional[Category] = None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)


class CategoryScheme(ItemScheme):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class Categorisation(MaintainableArtefact):
    # TODO: is passing Category/IdentifiableArtefact to __init__ a one-way association?
    def __init__(
        self, categorised_artefact: IdentifiableArtefact, category: Category
    ) -> None:
        self.category = category
        self.categorised_artefact = categorised_artefact
