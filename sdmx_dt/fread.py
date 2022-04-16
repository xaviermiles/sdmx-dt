import json
from dataclasses import dataclass

import jsonschema
import requests


class InvalidSdmxJsonException(ValueError):
    pass


def fread_json(path, is_url=True):
    if is_url:
        r = requests.get(path)
        if r.status_code == 404:
            raise InvalidSdmxJsonException("That URL path is not a real place.")
        try:
            raw = json.loads(r.content)
        except json.decoder.JSONDecodeError:
            raise InvalidSdmxJsonException("Response contents is not JSON.")
    else:
        with open(path) as f:
            raw = json.load(f)
    return SdmxJsonDataMessage(raw)


class SdmxJsonDataMessage:
    def __init__(self, message_obj) -> None:
        self.validate_with_schema(message_obj)

        if "meta" in message_obj:
            self.meta = SdmxJsonMeta(message_obj["meta"])
        else:
            self.meta = None

        if "data" in message_obj.keys():
            self.data = SdmxJsonData(message_obj["data"])
        else:
            self.data = None

        self.errors = [SdmxJsonError(err) for err in message_obj.get("errors", [])]

    def validate_with_schema(self, message_obj: dict) -> None:
        """Validate using JSON schema.

        If "schema" (URL) is provided under "meta" top-level object then that will be
        used. Otherwise, defaults to SDMX-JSON schema v2.0.0
        """
        if "meta" in message_obj.keys() and "schema" in message_obj["meta"].keys():
            schema_loc = message_obj["meta"]["schema"]
        else:
            # TODO: does this detect if both data & errors being present?
            schema_loc = (
                "https://github.com/sdmx-twg/sdmx-json/raw/master/metadata-message/"
                "tools/schemas/2.0.0/sdmx-json-metadata-schema.json"
            )
        r = requests.get(schema_loc)
        schema = json.loads(r.content)
        jsonschema.validate(message_obj, schema, cls=jsonschema.Draft202012Validator)

    def __eq__(self, other) -> bool:
        return (
            self.meta == other.meta
            and self.data == other.data
            and self.errors == other.errors
        )


class SdmxJsonMeta:
    def __init__(self, meta_obj) -> None:
        pass

    def __eq__(self, other) -> bool:
        return True


class Link:
    pass


@dataclass
class DataSet:
    action: str = "Information"
    reportingBegin: str = None
    reportingEnd: str = None
    validFrom: str = None
    validTo: str = None
    publicationYear: str = None
    publicationPeriod: str = None
    links: list = None
    annotations: list[int] = None
    attributes: list[int] = None
    series: dict = None
    observations: dict = None

    def __post_init__(self):
        if self.links:
            self.links = [Link(**l) for l in self.links]
        # "series" and "observations" cannot co-exist
        assert (self.series is None) != (self.observations is None)


class SdmxJsonData:
    def __init__(self, data_obj) -> None:
        if "dataSet" in data_obj.keys():
            self.dataSet = DataSet(**data_obj["dataSet"])

    def __eq__(self, other) -> bool:
        return True


class SdmxJsonError:
    def __init__(self, errors_obj) -> None:
        pass

    def __eq__(self, other) -> bool:
        return True
