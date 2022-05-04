import pytest
from datatable import Frame


class Helpers:
    @staticmethod
    def check_dt_Frames_eq(f1, f2):
        assert isinstance(f1, Frame) and isinstance(f2, Frame)

        # Using to_dict() method since __eq__() method doesn't seem to work
        assert f1.to_dict() == f2.to_dict()
        assert f1.types == f2.types


@pytest.fixture
def helpers():
    return Helpers
