from typing import Set

import pytest
from datatable import Frame, f


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

    @staticmethod
    def dt_unique(frame: Frame, columns: Set[str]) -> Frame:
        """Get unique rows when datatable is subset to given columns

        This mimics the R-data.table implementation of unique, as opposed to the
        current implementation within Python-datatable. See lines #653-655 of:

        https://github.com/h2oai/datatable/blob/8bb0056/docs/manual ...
        /comparison_with_rdatatable.rst
        """
        subset = frame[:, f[columns]]
        unique_rows = list(dict.fromkeys(subset.to_tuples()))
        unique_frame = Frame(unique_rows, names=columns)
        return unique_frame


@pytest.fixture
def helpers():
    return Helpers
