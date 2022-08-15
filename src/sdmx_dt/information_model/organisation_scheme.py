from abc import ABC
from dataclasses import dataclass

from sdmx_dt.information_model.base import InternationalString
from sdmx_dt.information_model.item_scheme import Item, ItemScheme
from sdmx_dt.information_model.misc import Url


@dataclass
class Contact:
    name: str
    organisation_unit: str
    telephone: str
    responsibility: InternationalString
    fax: str
    email: str
    X400: str
    uri: Url


# Items
class Organisation(Item, ABC):
    def __init__(self, num_contacts: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        # Organisation has 0..* relationship to Contact
        self.contacts = [
            Contact("", "", "", InternationalString({}), "", "", "", Url())
            for _ in range(num_contacts)
        ]


class Agency(Organisation):
    # no hierarchy
    pass


class DataConsumer(Organisation):
    # no hierarchy
    pass


class DataProvider(Organisation):
    # no hierarchy
    pass


class OrganisationUnit(Organisation):
    # yes hierarchy
    pass


# Schemes
class OrganisationScheme(ItemScheme, ABC):
    pass


class AgencyScheme(OrganisationScheme):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.agencies = self.items  # alias


class DataConsumerScheme(OrganisationScheme):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data_consumers = self.items  # alias


class DataProviderScheme(OrganisationScheme):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data_providers = self.items  # alias


class OrganisationUnitScheme(OrganisationScheme):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.organisation_units = self.items  # alias
