from dataclasses import dataclass
from typing import Optional


class Annotation:
    pass


class Link:
    pass


@dataclass
class Artefact:
    """Abstract to handle common SDMX artefact properties"""

    id: str
    agencyID: Optional[str] = None
    version: str = "1.0"
    name: Optional[str] = None
    names: Optional[dict] = None
    description: Optional[str] = None
    descriptions: Optional[dict] = None
    validFrom: Optional[str] = None
    validTo: Optional[str] = None
    isFinal: Optional[None] = None
    isExternalReference: Optional[bool] = None
    annotations: Optional[list] = None
    links: Optional[list] = None

    def __post_init__(self):
        self.annotations = [Annotation(**a) for a in self.annotations]
        self.links = [Link(**l) for l in self.links]
