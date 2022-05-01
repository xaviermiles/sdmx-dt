import itertools
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

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
    reportingBegin: Optional[str] = None
    reportingEnd: Optional[str] = None
    validFrom: Optional[str] = None
    validTo: Optional[str] = None
    publicationYear: Optional[str] = None
    publicationPeriod: Optional[str] = None
    links: Optional[List] = None
    annotations: Optional[List[int]] = None
    attributes: Optional[List[int]] = None
    series: Optional[Dict] = None
    observations: Optional[Dict] = None

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
        # TODO: implement for messages with multiple dataSets
        if self.dataSets[0].series:
            return self.get_series_level()
        elif self.dataSets[0].observations:
            return self.get_observations_level()

    def get_series_level(self):
        """Get observations datatables from series-level"""
        vals = self.dataSets[0].series

        series_tables = []
        for series_dims_joined, series_info in vals.items():
            num_datapoints = len(series_info["observations"].keys())

            # series-level dimensions
            series_dims = series_dims_joined.split(":")
            series_dim_ref = self.structure.dimensions["series"]

            series_dim_cols = {
                series_dim_ref[dim_num]["name"]: num_datapoints
                * [series_dim_ref[dim_num]["values"][int(val)]["name"]]
                for dim_num, val in enumerate(series_dims)
            }

            # observation-level dimensions
            obs_dim_cols = self._parse_observations_dimensions(
                series_info["observations"].keys()
            )

            # values
            values = [v[0] for v in series_info["observations"].values()]

            # TODO: series-level attributes

            # observation-level attributes
            obs_attr_cols = self._parse_obs_level_attributes(
                series_info["observations"].values()
            )

            # TODO: series/obs annotations??

            series_tables.append(
                {**series_dim_cols, **obs_dim_cols, "Value": values, **obs_attr_cols}
            )

        col_names = series_tables[0].keys()
        full_table = {
            col_name: list(
                itertools.chain.from_iterable(s[col_name] for s in series_tables)
            )
            for col_name in col_names
        }
        return dt.Frame(full_table)

    def get_observations_level(self):
        """Get observations datatable from observation-level

        Comes with columns for values, all dimensions and all attributes.
        """
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
                    # Take default "name"
                    default_id = attributes_ref[att_num]["default"]
                    default_info = next(
                        val
                        for val in attributes_ref[att_num]["values"]
                        if val["id"] == default_id
                    )
                    attribute_cols[col_name] = default_info["name"]
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

    def _parse_observations_dimensions(self, obs_dim_keys):
        """Helper to translate observation-level dimensions into columns"""
        dim_structure = self.structure.dimensions["observation"]

        obs_dim_vals = [o.split(":") for o in obs_dim_keys]
        num_dims = len(obs_dim_vals[0])
        obs_dim_columns = {
            dim_structure[dim_num]["name"]: [
                dim_structure[dim_num]["values"][int(vals[dim_num])]["name"]
                for vals in obs_dim_vals
            ]
            for dim_num in range(num_dims)
        }
        return obs_dim_columns

    def _parse_obs_level_attributes(self, obs_vals):
        """Helper to translate observation-level attributes into columns"""
        attr_structure = self.structure.attributes["observation"]

        obs_attr_columns = {}
        for attr_num in range(len(attr_structure)):
            col_name = attr_structure[attr_num]["name"]

            obs_attr_columns[col_name] = [
                self._parse_single_obs_level_attribute(vals_i, attr_num, attr_structure)
                for vals_i in obs_vals
            ]

        return obs_attr_columns

    def _parse_single_obs_level_attribute(
        self, obs_datapoint, attr_num, attr_structure
    ):
        num_attr_set = len(obs_datapoint) - 1  # first slot is for "Value"

        if attr_num > num_attr_set:
            # Take default "name"
            default_id = attr_structure[attr_num]["default"]
            print(attr_num)
            default_info = next(
                val
                for val in attr_structure[attr_num]["values"]
                if val["id"] == default_id
            )
            return default_info["name"]

        attr_idx = obs_datapoint[attr_num + 1]
        if attr_idx is None:
            return None  # TODO: check this is correct

        try:
            attr_name = attr_structure[attr_num]["values"][attr_idx]["name"]
        except IndexError:
            return -1  # FIXME: why does this happen?
        return attr_name

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
