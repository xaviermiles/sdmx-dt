import os

import pytest
import requests

from sdmx_dt import fread
from tests import DATA_DIR

# Commit 21d2034 is v1.0 of SDMX-JSON
sdmx_json_samples_url = (
    "https://raw.githubusercontent.com/sdmx-twg/sdmx-json/21d2034/data-message/samples/"
)
pytestmark = pytest.mark.parametrize(
    "name",
    [
        "agri.json",
        "exr/exr-action-delete.json",
        "exr/exr-cross-section.json",
    ],
)


@pytest.fixture
def sdmx_json_msg_remote(name):
    return fread.fread_json(sdmx_json_samples_url + name)


@pytest.fixture
def sdmx_json_msg_local(name):
    path = os.path.join(DATA_DIR, name.split("/")[-1])
    r = requests.get(sdmx_json_samples_url + name)
    with open(path, "w") as f:
        f.write(r.content.decode())
    return fread.fread_json(path, is_url=False)


def test_fread_json_local_and_remote_eq(sdmx_json_msg_remote, sdmx_json_msg_local):
    assert sdmx_json_msg_remote == sdmx_json_msg_local


def test_fread_json_types(name, sdmx_json_msg_remote):
    msg = sdmx_json_msg_remote  # shorter alias
    assert isinstance(msg, fread.SdmxJsonDataMessage)
    assert isinstance(msg.meta, fread.SdmxJsonMeta) or msg.meta is None
    assert isinstance(msg.data, fread.SdmxJsonData) or msg.data is None
    assert isinstance(msg.errors, list) and (
        len(msg.errors) == 0 or isinstance(msg.errors[0], fread.SdmxJsonError)
    )
