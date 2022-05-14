from abc import ABC
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from sdmx_dt.information_model.misc import Uri, Url


# Concrete classes
@dataclass
class LocalisedString:
    label: str
    locale: str


class InternationalString:
    def __init__(self, text: Optional[Dict[str, str]]) -> None:
        self.localised_strings = [
            LocalisedString(label, locale) for label, locale in text.items()
        ]


class Annotation:
    def __init__(
        self,
        id: str,
        title: str,
        type: str,
        url: str,
        text: Optional[Dict[str, str]] = None,
    ) -> None:
        self.id = id
        self.title = title
        self.type = type
        self.url = url
        self.text = InternationalString(text) if text else None


class Agency:
    pass


# Abstract classes
class AnnotableArtefact(ABC):
    """All derived classes may have Annotations (or notes)."""

    def __init__(self, annotations: Optional[List[Annotation]] = None) -> None:
        self.annotations = annotations


class IdentifiableArtefact(AnnotableArtefact, ABC):
    def __init__(self, id, uri, urn) -> None:
        self.id = id
        self.uri = uri
        self.urn = urn


class NameableArtefact(IdentifiableArtefact, ABC):
    def __init__(self, name, description=None) -> None:
        self.name = InternationalString(name)
        self.description = InternationalString(description) if description else None


class VersionableArtefact(NameableArtefact, ABC):
    def __init__(self, version: str, valid_from: date, valid_to: date) -> None:
        self.version = version
        self.valid_from = valid_from
        self.valid_to = valid_to


class MaintainableArtefact(VersionableArtefact, ABC):
    def __init__(
        self,
        final: bool,
        is_external_reference: bool,
        service_url: Url,
        structure_url: Uri,
    ) -> None:
        self.final = final
        self.is_external_reference = is_external_reference
        self.service_url = service_url
        self.structure_url = structure_url

    # MaintainableArtefact can call Agency's properties/methods, but not vice versa


# Extended Abtracted Classes
class Item(NameableArtefact, ABC):
    pass


class Hierarchy(NameableArtefact, ABC):
    pass


class Structure(MaintainableArtefact, ABC):
    pass
