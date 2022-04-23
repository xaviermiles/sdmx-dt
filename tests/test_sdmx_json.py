import json
import os

import pytest
import requests
from datatable import Frame

from sdmx_dt import sdmx_json
from tests import DATA_DIR

# Commit 21d2034 is v1.0 of SDMX-JSON
sdmx_json_samples_url = (
    "https://raw.githubusercontent.com/sdmx-twg/sdmx-json/21d2034/data-message/samples/"
)
expected = {
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
    },
    "exr/exr-action-delete.json": {
        "attributes": Frame(
            {
                "id": ["TIME_FORMAT"],
                "name": ["Time Format"],
                "values": ["Daily"],
            }
        ),
    },
    "exr/exr-cross-section.json": {
        "attributes": Frame(
            {
                "id": ["TIME_FORMAT"],
                "name": ["Time Format"],
                "values": ["Daily"],
            }
        ),
    },
}

pytestmark = pytest.mark.parametrize("name", expected.keys())


@pytest.fixture
def sdmx_json_msg_remote(name):
    return sdmx_json.fread_json(sdmx_json_samples_url + name)


@pytest.fixture
def sdmx_json_msg_local(name):
    path = os.path.join(DATA_DIR, name.split("/")[-1])
    r = requests.get(sdmx_json_samples_url + name)
    raw_msg = json.loads(r.content.decode())

    # Fix typo in agri.json. This doesn't preserve original ordering
    if name == "agri.json":
        attr_part = raw_msg["data"]["structure"]["attributes"]
        attr_part["dataSet"] = attr_part.pop("dataset")

    with open(path, "w") as f:
        json.dump(raw_msg, f, indent=4)
    return sdmx_json.fread_json(path, is_url=False)


def test_fread_json_local_and_remote_eq(
    name, sdmx_json_msg_remote, sdmx_json_msg_local
):
    # FIXME: Is it possible to fix agri.json typo when retrieving from remote??
    if name == "agri.json":
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


def test_get_attributes(name, sdmx_json_msg_local):
    # Using to_dict() method since __eq__() method doesn't seem to work
    # TODO: Is this sufficient? Or is there more it should check?
    assert (
        sdmx_json_msg_local.data.get_attributes().to_dict()
        == expected[name]["attributes"].to_dict()
    )
