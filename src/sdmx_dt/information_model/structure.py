from abc import ABC
from typing import Optional

from sdmx_dt.information_model.base import MaintainableArtefact
from sdmx_dt.information_model.codelist import CodeList


class Representation:
    def placeholder(self, enumerated: Optional[CodeList]) -> None:
        # Component has one-way association "enumerated" to CodeList
        pass


class Component:
    def __init__(self, has_local_repr: bool = True) -> None:
        self.local_representation = Representation(None) if has_local_repr else None

    def placeholder(self, concept_identity: Optional[CodeList]) -> None:
        # Component has one-way association "concept_identity" to CodeList
        pass


class ComponentList:
    def __init__(self) -> None:
        self.components = [Component()]


class Structure(MaintainableArtefact, ABC):
    def __init__(self) -> None:
        self.grouping = [ComponentList()]


class StructureUsage(MaintainableArtefact, ABC):
    # StructureUsage can call Structure's properties/methods, but not vice versa.
    pass


# Concrete Structure subclasses
class DataStructure(Structure):
    pass


class Definition(Structure):
    pass


class MetadataStructure(Structure):
    pass
