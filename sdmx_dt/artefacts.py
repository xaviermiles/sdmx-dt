from dataclasses import dataclass


class Annotation:
    pass


class Link:
    pass


@dataclass
class Artefact:
    """Abstract to handle common SDMX artefact properties"""

    id: str
    agencyID: str = ""
    version: str = "1.0"
    name: str = ""
    names: dict[str, str] = dict()
    description: str = None
    descriptions: dict[str, str] = dict()
    validFrom: str = None
    validTo: str = None
    isFinal: bool = None
    isExternalReference: bool = None
    annotations: list = []
    links: list = None

    def __post_init__(self):
        self.annotations = [Annotation(**a) for a in self.annotations]
        self.links = [Link(**l) for l in self.links]
