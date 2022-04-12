import os

import requests

from sdmx_dt import fread
from tests import DATA_DIR


def test_fread_json_samples():
    path_r = "https://github.com/sdmx-twg/sdmx-json/raw/master/data-message/samples/agri.json"
    message_remote = fread.fread_json(path_r)

    path_l = os.path.join(DATA_DIR, path_r.split("/")[-1])
    r = requests.get(path_r, stream=True)
    with open(path_l, "w") as f:
        f.write(r.content.decode())
    message_local = fread.fread_json(path_l, is_url=False)

    # TODO: implement __eq__() ?
    # assert message_remote == message_local

    assert type(message_remote) is fread.SdmxJsonDataMessage
    # Check for empty top-level objects?
    assert type(message_remote.meta) is fread.SdmxJsonMeta
    assert type(message_remote.data) is fread.SdmxJsonData
    assert type(message_remote.error) is fread.SdmxJsonErrors
