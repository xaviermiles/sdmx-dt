from typing import List

from sdmx_dt.information_model.item_scheme import Item, ItemScheme
from sdmx_dt.information_model.structure import Structure, StructureUsage


class ReportingCategory(Item):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # TODO: fill in self.flows and self.structures
        self.flows: List[StructureUsage] = []  # 0..*
        self.structures: List[Structure] = []  # 0..*


class ReportingTaxonomy(ItemScheme):
    pass
