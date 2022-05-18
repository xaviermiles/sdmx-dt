from abc import ABC

from sdmx_dt.information_model.base import MaintainableArtefact


class Representation:
    pass


class Component:
    def __init__(self, has_local_repr: bool = True) -> None:
        self.local_representation = Representation() if has_local_repr else None


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
