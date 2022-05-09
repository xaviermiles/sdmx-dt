import pytest
from datatable import Frame


class Helpers:
    @staticmethod
    def check_dt_Frames_eq(f1, f2):
        assert isinstance(f1, Frame) and isinstance(f2, Frame)

        # Note: Simply using __eq__() method doesn't seem to work
        # Check order/type of columns
        assert f1.keys() == f2.keys()
        assert f1.types == f2.types

        # Check datapoints
        assert f1.to_csv() == f2.to_csv()
        assert f1.to_dict() == f2.to_dict()


@pytest.fixture
def helpers():
    return Helpers
