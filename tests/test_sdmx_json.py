import json
import os

import pytest
import requests
from datatable import Frame, dt

from sdmx_dt import sdmx_json
from tests import DATA_DIR

# SDMX-JSON v1.0 aligns to SDMX v2.1
sdmx_json_v1_commit = "d2bf3f7"
sdmx_json_samples_url = (
    f"https://raw.githubusercontent.com/sdmx-twg/sdmx-json/{sdmx_json_v1_commit}/"
    "data-message/samples/"
)
expected_all = {
    "agri.json": {
        "attributes": Frame(
            {
                "id": [
                    "UNIT_MEASURE",
                    "UNIT_MULT",
                    "BASE_PER",
                    "PREF_SCALE",
                    "DECIMALS",
                ],
                "name": [
                    "Unit of measure",
                    "Unit multiplier",
                    "Base Period",
                    "Preferred scale",
                    "Decimals",
                ],
                "values": [
                    "Tones",
                    "Thousands",
                    "2010=100",
                    "Thousandth",
                    "One decimal",
                ],
            }
        ),
        "observations": Frame(
            {
                "Reference area": [
                    "Banteay Meanchey",
                    "Banteay Meanchey",
                    "Banteay Meanchey",
                    "Banteay Meanchey",
                    "Battambang",
                    "Battambang",
                    "Battambang",
                    "Battambang",
                ],
                "Time Period": [
                    "2014",
                    "2015",
                    "2016",
                    "2017",
                    "2014",
                    "2015",
                    "2016",
                    "2017",
                ],
                "Value": [
                    350.154,
                    389.385,
                    395.729,
                    433.638,
                    442.996,
                    426.588,
                    479.686,
                    522.296,
                ],
                "Source": [
                    "MAFF_Agricultural Statistics_2014",
                    "MAFF_Agricultural Statistics_2015",
                    "MAFF_Agricultural Statistics_2016",
                    "MAFF_Agricultural Statistics_2017",
                    "MAFF_Agricultural Statistics_2014",
                    "MAFF_Agricultural Statistics_2015",
                    "MAFF_Agricultural Statistics_2016",
                    "MAFF_Agricultural Statistics_2017",
                ],
                "Observation status": 8 * ["Normal value"],
            }
        ),
    },
    "exr/exr-action-delete.json": {
        "attributes": Frame(
            {
                "id": ["TIME_FORMAT"],
                "name": ["Time Format"],
                "values": ["Daily"],
            }
        ),
        "observations": [
            Frame(
                {
                    "Time period or range": ["2013-01-18", "2013-01-21"],
                    "Currency": ["Russian rouble", "Russian rouble"],
                    "Value": [40.3426, 40.3],
                    "Series title": ["Russian rouble (RUB)", "Russian rouble (RUB)"],
                    "Observation status": ["Normal value", "Normal value"],
                }
            ),
            Frame(),
        ],
    },
    "exr/exr-cross-section.json": {
        "attributes": Frame(
            {
                "id": ["TIME_FORMAT"],
                "name": ["Time Format"],
                "values": ["Daily"],
            }
        ),
        "observations": Frame(
            {
                "Time period or range": [
                    "2013-01-18",
                    "2013-01-18",
                    "2013-01-21",
                    "2013-01-21",
                ],
                "Currency": [
                    "New Zealand dollar",
                    "Russian rouble",
                    "New Zealand dollar",
                    "Russian rouble",
                ],
                "Value": [1.5931, 40.3426, 1.5925, 40.3],
                "Observation status": 4 * ["Normal value"],
                "Series title": [
                    "New Zealand dollar (NZD)",
                    "Russian rouble (RUB)",
                    "New Zealand dollar (NZD)",
                    "Russian rouble (RUB)",
                ],
            }
        ),
    },
}

pytestmark = pytest.mark.parametrize("name", expected_all.keys())


@pytest.fixture
def sdmx_json_msg_remote(name):
    return sdmx_json.fread_json(sdmx_json_samples_url + name)


@pytest.fixture
def sdmx_json_msg_local(name):
    path = os.path.join(DATA_DIR, name.split("/")[-1])
    r = requests.get(sdmx_json_samples_url + name)
    raw_msg = json.loads(r.content.decode())

    # Fix typos in agri.json. This doesn't preserve original ordering
    if name == "agri.json":
        for section_name in ["attributes", "dimensions"]:
            section = raw_msg["data"]["structure"][section_name]
            section["dataSet"] = section.pop("dataset")
    # Fix typos in exr/exr-action-delete.json
    elif name == "exr/exr-action-delete.json":
        obs_1 = raw_msg["data"]["dataSets"][0]["series"]["0"]["observations"]["1"]
        obs_1[1], obs_1[2] = obs_1[2], obs_1[1]
        obs_2 = raw_msg["data"]["dataSets"][0]["series"]["1"]["observations"]["1"]
        obs_2[1], obs_2[2] = obs_2[2], obs_2[1]

    with open(path, "w") as f:
        json.dump(raw_msg, f, indent=4)
    return sdmx_json.fread_json(path, is_url=False)


@pytest.fixture
def expected_dts(name):
    suffix = ".csv"

    tidy_name = name.split("/")[-1]
    name_dir = os.path.join("tests", "expected_data", tidy_name)
    expected_dts = {
        f[: -len(suffix)]: dt.fread(os.path.join(name_dir, f))
        for f in os.listdir(name_dir)
        if f.endswith(suffix)
    }
    return expected_dts


def test_fread_json_local_and_remote_eq(
    name, sdmx_json_msg_remote, sdmx_json_msg_local
):
    # FIXME: Is it possible to fix typos when retrieving from remote??
    if name in ["agri.json", "exr/exr-action-delete.json"]:
        return NotImplemented

    assert sdmx_json_msg_remote == sdmx_json_msg_local


def test_fread_json_types(name, sdmx_json_msg_local):
    msg = sdmx_json_msg_local  # shorter alias
    assert isinstance(msg, sdmx_json.SdmxJsonDataMessage)
    assert isinstance(msg.meta, sdmx_json.SdmxJsonMeta) or msg.meta is None
    assert isinstance(msg.data, sdmx_json.SdmxJsonData) or msg.data is None
    assert isinstance(msg.errors, list) and (
        len(msg.errors) == 0 or isinstance(msg.errors[0], sdmx_json.SdmxJsonError)
    )


def test_get_attributes(name, sdmx_json_msg_local, helpers):
    actual = sdmx_json_msg_local.data.get_attributes()
    expected = expected_all[name]["attributes"]

    helpers.check_dt_Frames_eq(actual, expected)


def test_get_observations(name, sdmx_json_msg_local, helpers):
    actual = sdmx_json_msg_local.data.get_observations()
    expected = expected_all[name]["observations"]

    # Should return list of datatables when there is multiple dataSets
    if isinstance(expected, list):
        assert isinstance(actual, list)
        for actual_i, expected_i in zip(actual, expected):
            helpers.check_dt_Frames_eq(actual_i, expected_i)
    else:
        helpers.check_dt_Frames_eq(actual, expected)


def test_get_dimensions(name, sdmx_json_msg_local, expected_dts, helpers):
    actual = sdmx_json_msg_local.data.structure.get_dimensions(include_values=True)
    expected = expected_dts["dimensions"]

    helpers.check_dt_Frames_eq(actual, expected)

    # Method should be accessible from SdmxJsonData
    helpers.check_dt_Frames_eq(
        actual, sdmx_json_msg_local.data.get_dimensions(include_values=True)
    )
