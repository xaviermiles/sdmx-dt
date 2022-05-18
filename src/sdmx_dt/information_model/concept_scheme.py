from __future__ import annotations

from typing import Optional

from sdmx_dt.information_model.base import Representation
from sdmx_dt.information_model.item_scheme import Item, ItemScheme


class ISOConceptReference:
    def __init__(
        self, concept_agency: str, concept_scheme_id: str, concept_id: str
    ) -> None:
        self.concept_agency = concept_agency
        self.concept_scheme_id = concept_scheme_id
        self.concept_id = concept_id


class Concept(Item):
    def __init__(
        self,
        has_core_repr: bool,
        has_ISO_concept: bool,
        parent: Optional[Concept] = None,
        **kwargs,
    ) -> None:
        self.core_representation = Representation() if has_core_repr else None
        # TODO: where do ISOConceptReference arguments come from?
        self.ISO_concept = ISOConceptReference("", "", "") if has_ISO_concept else None
        super().__init__(parent=parent, **kwargs)


class ConceptScheme(ItemScheme):
    pass
