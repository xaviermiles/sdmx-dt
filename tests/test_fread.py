import os

import pytest
import requests

from sdmx_dt import fread
from tests import DATA_DIR

sdmx_json_samples_url = (
    "https://github.com/sdmx-twg/sdmx-json/raw/master/data-message/samples/"
)


@pytest.fixture
def sdmx_json_sample_names():
    return [
        "agri.json",
        "constructed-sample-full.json",
        # "generated-sample.json",  # FIXME: why is this raising DNS problems?
    ]


@pytest.fixture
def sdmx_json_sample_messages(sdmx_json_sample_names):
    return [fread.fread_json(sdmx_json_samples_url + f) for f in sdmx_json_sample_names]


@pytest.fixture
def local_sdmx_json_sample_messages(sdmx_json_sample_names):
    local_messages = []
    for name in sdmx_json_sample_names:
        path = os.path.join(DATA_DIR, name)
        r = requests.get(sdmx_json_samples_url + name)
        with open(path, "w") as f:
            f.write(r.content.decode())
        local_messages.append(fread.fread_json(path, is_url=False))
    return local_messages


def test_fread_json_local_and_remote_eq(
    sdmx_json_sample_messages, local_sdmx_json_sample_messages
):
    assert sdmx_json_sample_messages == local_sdmx_json_sample_messages


def test_fread_json_types(sdmx_json_sample_messages):
    for msg in sdmx_json_sample_messages:
        assert isinstance(msg, fread.SdmxJsonDataMessage)
        # Check for empty top-level objects?
        assert isinstance(msg.meta, fread.SdmxJsonMeta) or msg.meta is None
        assert isinstance(msg.data, fread.SdmxJsonData) or msg.data is None
        assert isinstance(msg.errors, fread.SdmxJsonErrors) or msg.errors is None
