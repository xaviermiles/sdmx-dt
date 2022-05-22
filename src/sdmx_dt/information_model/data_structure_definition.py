from abc import ABC
from typing import List, Optional

from sdmx_dt.information_model.basic_data_types import UsageStatus
from sdmx_dt.information_model.concept_scheme import Concept
from sdmx_dt.information_model.structure import (
    Component,
    ComponentList,
    Structure,
    StructureUsage,
)


# Measure
class PrimaryMeasure(Component):
    pass


class MeasureDescriptor:
    pass


# Dimensions
class DimensionComponent(Component, ABC):
    def __init__(
        self, order: int, roles: Optional[List[Concept]] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.order = order
        self.roles = roles or []  # 0..*
        # self.concept_identity


class Dimension(DimensionComponent):
    pass


class MeasureDimension(DimensionComponent):
    def __init__(
        self, components: Optional[DimensionDescriptor] = None, **kwargs
    ) -> None:
        super().__init__(components=components, **kwargs)


class TimeDimension(DimensionComponent):
    def __init__(self, **kwargs) -> None:
        if "roles" in kwargs:
            raise ValueError("`roles` is not valid for TimeDimension.")

        super().__init__(**kwargs)


class DimensionDescriptor(ComponentList):
    def __init__(self, components: List[DimensionComponent], **kwargs) -> None:
        super().__init__(components=components, **kwargs)


class GroupDimensionDescriptor(ComponentList):
    def __init__(
        self,
        is_attachment_constraint: bool,
        constraint: Optional[AttachmentConstraint] = None,
        components: Optional[List[DimensionComponent]] = None,
    ) -> None:
        if constraint and components:
            raise ValueError("`constraint` and `components` are mutually exclusive.")

        self.is_attachment_constraint = is_attachment_constraint
        self.constraint = constraint
        self.components = components


# Attributes
class AttributeRelationship(ABC):
    pass


class NoSpecifiedRelationship(AttributeRelationship):
    pass


class PrimaryMeasureRelationship(AttributeRelationship):
    pass


class GroupRelationship(AttributeRelationship):
    """SDMX 2.1 line #1293 - "this is retained for compatibility reasons"."""

    def __init__(self, group_key: GroupDimensionDescriptor) -> None:
        self.group_key = group_key


class DimensionRelationship(AttributeRelationship):
    def __init__(
        self,
        group_keys: List[GroupDimensionDescriptor],
        dimensions: List[DimensionDescriptor],
    ) -> None:
        self.group_keys = group_keys  # 0..*
        self.dimensions = dimensions  # 1..*


class DataAttribute(Component):
    def __init__(
        self, usage_status: UsageStatus, roles: Optional[List[Concept]] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.usage_status = usage_status
        self.roles = roles or []  # 0..*
        # See table immediately after Figure 24 for "the possible relationships a DataAttribute may specify"
        self.related_to: Optional[AttributeRelationship] = None


class ReportingYearStartDate(DataAttribute):
    pass


class AttributeDescriptor:
    pass


# Top-level
class DataflowDefinition(StructureUsage):
    pass


class DataStructureDefinition(Structure):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.grouping = DimensionDescriptor()
