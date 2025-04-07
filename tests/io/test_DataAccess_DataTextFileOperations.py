import sys
from contextlib import contextmanager
from io import StringIO

import mock
import numpy
import pytest

from dfastmi.io.DataTextFileOperations import DataTextFileOperations


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_read_waqua_xyz:
    def test_read_waqua_xyz_01(self):
        """
        Read WAQUA xyz file default column 2.
        """
        filename = "tests/files/read_waqua_xyz_test.xyc"
        data = DataTextFileOperations.read_waqua_xyz(filename)
        datar = numpy.array([3.0, 6.0, 9.0, 12.0])
        print("data reference: ", datar)
        print("data read     : ", data)
        assert numpy.shape(data) == (4,)
        assert (data == datar).all() == True

    def test_read_waqua_xyz_02(self):
        """
        Read WAQUA xyz file columns 1 and 2.
        """
        filename = "tests/files/read_waqua_xyz_test.xyc"
        col = (1, 2)
        data = DataTextFileOperations.read_waqua_xyz(filename, col)
        datar = numpy.array([[2.0, 3.0], [5.0, 6.0], [8.0, 9.0], [11.0, 12.0]])
        print("data reference: ", datar)
        print("data read     : ", data)
        assert numpy.shape(data) == (4, 2)
        assert (data == datar).all() == True


class Test_write_simona_box:
    def test_write_simona_box_01(self):
        """
        Write small SIMONA BOX file.
        """
        filename = "test.box"
        data = numpy.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        firstm = 0
        firstn = 0
        DataTextFileOperations.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = [
            "      BOX MNMN=(   1,    1,    3,    3), VARIABLE_VAL=",
            "          1.000       2.000       3.000",
            "          4.000       5.000       6.000",
            "          7.000       8.000       9.000",
        ]
        assert all_lines == all_lines_ref

    def test_write_simona_box_02(self):
        """
        Write small SIMONA BOX file with offset.
        """
        filename = "test.box"
        data = numpy.array(
            [[0, 0, 0, 0, 0], [0, 0, 1, 2, 3], [0, 0, 4, 5, 6], [0, 0, 7, 8, 9]]
        )
        firstm = 1
        firstn = 2
        DataTextFileOperations.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = [
            "      BOX MNMN=(   2,    3,    4,    5), VARIABLE_VAL=",
            "          1.000       2.000       3.000",
            "          4.000       5.000       6.000",
            "          7.000       8.000       9.000",
        ]
        assert all_lines == all_lines_ref

    def test_write_simona_box_03(self):
        """
        Write large SIMONA BOX file.
        """
        filename = "test.box"
        data = numpy.zeros((15, 15))
        firstm = 0
        firstn = 0
        DataTextFileOperations.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ["      BOX MNMN=(   1,    1,   15,   10), VARIABLE_VAL="]
        all_lines_ref.extend(
            [
                "          0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000"
            ]
            * 15
        )
        all_lines_ref.extend(["      BOX MNMN=(   1,   11,   15,   15), VARIABLE_VAL="])
        all_lines_ref.extend(
            ["          0.000       0.000       0.000       0.000       0.000"] * 15
        )
        self.maxDiff = None
        assert all_lines == all_lines_ref


class Test_get_xykm:
    def test_get_xykm_01(self):
        """
        read .xyc file with val as xykm
        """
        line = DataTextFileOperations.get_xykm("tests/files/read_xyc_test.xyc")

        assert line.wkt == "LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)"
