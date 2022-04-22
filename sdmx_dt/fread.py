import json
from dataclasses import dataclass

import datatable as dt
import jsonschema
import requests


class InvalidSdmxJsonException(ValueError):
    pass


def fread_json(path, is_url=True):
    if is_url:
        try:
            r = requests.get(path)
        except requests.exceptions.MissingSchema:
            raise ValueError(
                "Invalid URL: No scheme supplied. If you are using a file path set `is_url` to False."
            )
        if r.status_code == 404:
            raise InvalidSdmxJsonException("That URL `path` is not a real place.")
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

    def get_observations(self):
        if self.data is None:
            return None

        return self.data.get_observations()


class SdmxJsonMeta:
    def __init__(self, meta_obj) -> None:
        pass

    def __eq__(self, other) -> bool:
        return True


class Link:
    pass


class Structure:
    def __init__(
        self, links=None, dimensions=None, attributes=None, annotations=None, **kwargs
    ):
        self.links = links
        self.dimensions = dimensions
        self.attributes = attributes
        self.annotations = annotations
        self.custom = kwargs

    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return self.__dict__ == other.__dict__
        return NotImplemented


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
        # TODO: need to add fields to Link dataclass
        # if self.links:
        #     self.links = [Link(**l) for l in self.links]
        # "series" and "observations" cannot co-exist
        assert (self.series is None) != (self.observations is None)


class SdmxJsonData:
    def __init__(self, data_obj) -> None:
        if "structure" in data_obj.keys():
            self.structure = Structure(**data_obj["structure"])
        else:
            self.structure = None

        if "dataSets" in data_obj.keys():
            self.dataSets = [DataSet(**d) for d in data_obj["dataSets"]]
        else:
            self.dataSets = []

    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return self.__dict__ == other.__dict__
        return NotImplemented

    def get_observations(self):
        """Get observations datatable

        Comes with columns for values, all dimensions and all attributes.
        """
        # TODO: should this loop over self.dataSets?
        vals = self.dataSets[0].observations
        dimensions_ref = self.structure.dimensions["observation"]
        attributes_ref = self.structure.attributes["observation"]

        rows = []
        for dimension_vals_joined, obs_nums in vals.items():
            dimension_vals = dimension_vals_joined.split(":")

            dimension_cols = {
                dimensions_ref[dim_num]["name"]: dimensions_ref[dim_num]["values"][
                    int(val)
                ]["name"]
                for dim_num, val in enumerate(dimension_vals)
            }
            num_attributes_set = len(obs_nums) - 1  # first slot is for "Value"

            attribute_cols = {}
            for att_num in range(len(attributes_ref)):
                col_name = attributes_ref[att_num]["name"]

                if att_num > num_attributes_set - 1:
                    attribute_cols[col_name] = attributes_ref[att_num]["default"]
                    continue

                attribute_val = obs_nums[att_num + 1]
                if attribute_val is None:
                    attribute_cols[col_name] = None
                else:
                    attribute_cols[col_name] = attributes_ref[att_num]["values"][
                        attribute_val
                    ]["name"]

            row = {
                **dimension_cols,
                "Value": obs_nums[0],
                **attribute_cols,
            }
            rows.append(row)

        denormalised_dt = dt.Frame(
            {col: [row[col] for row in rows] for col in rows[0].keys()}
        )
        return denormalised_dt

    def get_attributes(self):
        """Get datatable of dataset-level attributes"""
        # TODO: add support for localised name and values-name
        raw = self.structure.attributes.get("dataSet")
        if raw is None:
            return None
        # Can take position 0 of "values" since SDMX-JSON v1.0 field guide line #332:
        #   "Note that `dimensions` and `attributes` presented at `dataSet` level can
        #    only have one single component value."
        extracted = [
            (attr["id"], attr["name"], attr["values"][0]["name"]) for attr in raw
        ]
        extracted_transposed = [list(x) for x in zip(*extracted)]

        colnames = ["id", "name", "values"]
        attributes = dt.Frame(
            {
                colname: colitems
                for colname, colitems in zip(colnames, extracted_transposed)
            }
        )
        return attributes


class SdmxJsonError:
    def __init__(self, errors_obj) -> None:
        pass

    def __eq__(self, other) -> bool:
        return True
