import itertools
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import jsonschema
import requests
from datatable import dt, f


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

        if "meta" in message_obj.keys():
            self.meta: Optional[SdmxJsonMeta] = SdmxJsonMeta(message_obj["meta"])
        else:
            self.meta = None

        if "data" in message_obj.keys():
            self.data: Optional[SdmxJsonData] = SdmxJsonData(message_obj["data"])
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


class DataStructureDefinition:
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

    def get_dimensions(
        self, include_values: bool = False, locale: Optional[str] = None
    ) -> dt.Frame:
        """Get datatable of dimensions at all levels

        If `include_values` is True and series or observation level dimensions
        have multiple values, then each of these will be on a different row.
        """
        return self._parse_components(self.dimensions, True, include_values, locale)

    def get_attributes(
        self, include_values: bool = False, locale: Optional[str] = None
    ):
        """Get datatable of attributes at all levels

        If `include_values` is True and series or observation level dimensions
        have multiple values, then each of these will be on a different row.
        """
        return self._parse_components(self.attributes, False, include_values, locale)

    def _parse_components(
        self,
        components: dict,
        include_keyPosition: bool,
        include_values: bool,
        locale: Optional[str],
    ):
        levels = ["dataSet", "series", "observation"]
        nested_rows = [
            self._get_components_rows(
                dimension, include_keyPosition, level, include_values, locale
            )
            for level in levels
            for dimension in components[level]
        ]
        rows = list(itertools.chain.from_iterable(nested_rows))
        tidy_component = dt.Frame(rows)
        if include_keyPosition:
            tidy_component = tidy_component[:, :, dt.sort(f.keyPosition)]
        return tidy_component

    def _get_components_rows(
        self,
        component: dict,
        include_keyPosition: bool,
        level: str,
        include_values: bool,
        locale: Optional[str],
    ) -> List[dict]:
        """Helper method to parse information from given component"""
        base_cols = {
            "id": component["id"],
            "name": component["names"].get(locale) if locale else component["name"],
            "level": level,
        }
        if include_keyPosition:
            # If present, keyPosition is first column
            base_cols = {"keyPosition": component["keyPosition"], **base_cols}

        if not include_values:
            return [base_cols]

        value_ids = [v["id"] for v in component["values"]]
        value_names = [
            v["names"].get(locale) if locale else v["name"] for v in component["values"]
        ]
        # Get a row for each dimension value
        rows = [
            {**base_cols, "value_id": val_id, "value_name": val_name}
            for val_id, val_name in zip(value_ids, value_names)
        ]
        return rows


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
        # TODO: Is "structure" truly optional?
        self.structure = DataStructureDefinition(**data_obj["structure"])

        if "dataSets" in data_obj.keys():
            self.dataSets = [DataSet(**d) for d in data_obj["dataSets"]]
        else:
            self.dataSets = []

    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return self.__dict__ == other.__dict__
        return NotImplemented

    def get_observations(self) -> Union[List[dt.Frame], dt.Frame]:
        """Parse dataset(s) from message into datatable(s)

        These datatables will contain dimensions, observations values,
        and attributes, but NOT annotations. Empty datatables will be
        returned for datasets with "Delete" action.

        Returns single datatable if the message only contains one "dataSet".
        Returns list of datatables if the message contains multiple dataSets.
        """
        # TODO: add support for localised name and values-name
        if len(self.dataSets) > 1:
            return self.get_dataSets_level()
        elif self.dataSets[0].series:
            return self.get_series_level()
        elif self.dataSets[0].observations:
            return self.get_observations_level()

        return dt.Frame()

    def get_dataSets_level(self) -> List[dt.Frame]:
        return [
            self.get_series_level(dataSet_idx=i)
            if self.dataSets[i].series
            else self.get_observations_level(dataSet_idx=i)
            for i in range(len(self.dataSets))
        ]

    def get_series_level(self, dataSet_idx: int = 0) -> dt.Frame:
        """Get observations datatable from series-level"""
        dataSet = self.dataSets[dataSet_idx]
        if dataSet.action == "Delete":
            return dt.Frame()

        vals = dataSet.series
        if vals is None:
            return dt.Frame()

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

            # series-level attributes
            if series_info.get("attributes"):
                series_attr_cols = self._parse_attributes(
                    series_info["attributes"],
                    self.structure.attributes["series"],
                    num_repeats=num_datapoints,
                )
            else:
                series_attr_cols = {}

            # observation-level attributes
            obs_attr_cols = self._parse_attributes(
                [v[1:] for v in series_info["observations"].values()],
                self.structure.attributes["observation"],
            )

            series_tables.append(
                {
                    **series_dim_cols,
                    **obs_dim_cols,
                    "Value": values,
                    **series_attr_cols,
                    **obs_attr_cols,
                }
            )

        col_names = series_tables[0].keys()
        full_table = {
            col_name: list(
                itertools.chain.from_iterable(s[col_name] for s in series_tables)
            )
            for col_name in col_names
        }
        return dt.Frame(full_table)

    def get_observations_level(self, dataSet_idx: int = 0) -> dt.Frame:
        """Get observations datatable from observation-level"""
        dataSet = self.dataSets[dataSet_idx]
        if dataSet.action == "Delete":
            return dt.Frame()

        vals = dataSet.observations
        if vals is None:
            return dt.Frame()

        obs_dim_cols = self._parse_observations_dimensions(vals.keys())
        values = [v[0] for v in vals.values()]
        obs_attr_cols = self._parse_attributes(
            [v[1:] for v in vals.values()], self.structure.attributes["observation"]
        )

        observations = {**obs_dim_cols, "Value": values, **obs_attr_cols}
        return dt.Frame(observations)

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

    def _parse_attributes(self, attr_vals, attr_structure, num_repeats=1):
        """Helper to translate attributes into columns

        This can be used for observation-level or series-level attributes.
        """
        attr_columns = {
            structure_i["name"]: num_repeats
            * [
                self._parse_single_attribute(obs_val_j, i, structure_i)
                for obs_val_j in attr_vals
            ]
            for i, structure_i in enumerate(attr_structure)
        }
        return attr_columns

    def _parse_single_attribute(self, attr_indices, attr_num, attr_structure_i):
        if attr_num > len(attr_indices) - 1:
            # Take default "name", when attribute index not specified
            default_id = attr_structure_i["default"]
            default_info = next(
                val for val in attr_structure_i["values"] if val["id"] == default_id
            )
            return default_info["name"]

        attr_idx = attr_indices[attr_num]
        if attr_idx is None:
            return None  # TODO: check this is correct

        attr_name = attr_structure_i["values"][attr_idx]["name"]
        return attr_name

    def get_dimensions(
        self, include_values: bool = False, locale: Optional[str] = None
    ) -> dt.Frame:
        """Get datatable of dimensions at all levels"""
        return self.structure.get_dimensions(include_values, locale)

    def get_attributes(
        self, include_values: bool = False, locale: Optional[str] = None
    ) -> dt.Frame:
        """Get datatable of attributes at all levels"""
        return self.structure.get_attributes(include_values, locale)


class SdmxJsonError:
    def __init__(self, errors_obj) -> None:
        pass

    def __eq__(self, other) -> bool:
        return True
