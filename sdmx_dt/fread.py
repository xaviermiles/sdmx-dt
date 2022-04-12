import json

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
        self.verify_top_level_object(message_obj)
        self.meta = SdmxJsonMeta(message_obj.get("meta"))
        self.data = SdmxJsonData(message_obj.get("data"))
        self.error = SdmxJsonErrors(message_obj.get("error"))

    def verify_top_level_object(self, message_obj) -> None:
        """Check top-level object names.

        There may be "meta" and there should be exactly one of "data" or
        "error".
        """
        expected_keys = {"meta", "data", "error"}
        if len({"data", "error"} & message_obj.keys()) == 0:
            raise InvalidSdmxJsonException(
                "The message did not contain 'data' or 'error' top-level objects."
            )
        elif len({"data", "error"} & message_obj.keys()) == 2:
            raise InvalidSdmxJsonException(
                "The message contained both 'data' and 'error' top-level objects."
            )
        elif len(message_obj.keys() - expected_keys) > 0:
            raise InvalidSdmxJsonException(
                f"The message contained unexpected top-level objects ({message_obj.keys() - expected_keys})."
            )


class SdmxJsonMeta:
    def __init__(self, meta_obj) -> None:
        pass


class SdmxJsonData:
    def __init__(self, data_obj) -> None:
        pass


class SdmxJsonErrors:
    def __init__(self, errors_obj) -> None:
        pass
