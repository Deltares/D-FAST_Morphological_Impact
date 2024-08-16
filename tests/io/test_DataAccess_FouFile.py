import sys
from contextlib import contextmanager
from io import StringIO

import numpy
import pytest

from dfastmi.io.FouFile import FouFile

def open_fou_file() -> FouFile:
    filename = "tests/files/e02_f001_c011_simplechannel_fou.nc"
    return FouFile(filename)

@pytest.fixture
def fou_file() -> FouFile:
    return open_fou_file()

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_data_access_read_face_variable:
    @pytest.mark.parametrize(
        "data_file, dataref",
        [
            (open_fou_file(), 1.2839395356652856),
        ],
    )
    def test_x_velocity(self, data_file: FouFile, dataref: float):
        """
        Testing x_velocity.
        """
        datac = data_file.x_velocity()
        assert datac[1] == dataref

    @pytest.mark.parametrize(
        "data_file, dataref",
        [
            (open_fou_file(), 0.0001568670009850459),
        ],
    )
    def test_y_velocity(self, data_file: FouFile, dataref: float):
        """
        Testing y_velocity.
        """
        datac = data_file.y_velocity()
        assert datac[1] == dataref

    @pytest.mark.parametrize(
        "data_file, dataref",
        [
            (open_fou_file(), 3.89449840620317),
        ],
    )
    def test_water_depth(self, data_file: FouFile, dataref: float):
        """
        Testing water_depth.
        """
        datac = data_file.water_depth()
        assert datac[1] == dataref

    def test_read_face_variable_04(self, fou_file: FouFile):
        """
        Testing read_face_variable: variable by standard name.
        """
        varname = "sea_surface_height"
        datac = fou_file.read_face_variable(varname)
        dataref = 3.887132830889389
        assert datac[1] == dataref

    def test_read_face_variable_05(self, fou_file: FouFile):
        """
        Testing read_face_variable: variable by long name.
        """
        varname = "Last 001: water level, last values"
        datac = fou_file.read_face_variable(varname)
        dataref = 3.887132830889389
        assert datac[1] == dataref

    def test_read_face_variable_06(self, fou_file: FouFile):
        """
        Testing read_face_variable: variable by long name.
        """
        varname = "water level"
        with pytest.raises(Exception) as cm:
            datac = fou_file.read_face_variable(varname)
        assert (
            str(cm.value) == 'Expected one variable for "water level", but obtained 0.'
        )


class TestReadGridGeometryFromMapFile:

    def test_get_node_x_coordinates(self, fou_file: FouFile):
        node_x_coordinates = fou_file.node_x_coordinates

        assert node_x_coordinates.shape == (2363,)
        assert node_x_coordinates[0] == pytest.approx(62.5)
        assert node_x_coordinates[1181] == pytest.approx(6750)
        assert node_x_coordinates[2362] == pytest.approx(0.0)

    def test_get_node_y_coordinates(self, fou_file: FouFile):
        node_y_coordinates = fou_file.node_y_coordinates

        assert node_y_coordinates.shape == (2363,)
        assert node_y_coordinates[0] == pytest.approx(7000)
        assert node_y_coordinates[1181] == pytest.approx(7200.542889)
        assert node_y_coordinates[2362] == pytest.approx(7500)

    def test_get_face_node_connectivity(self, fou_file: FouFile):
        face_node_connectivity = fou_file.face_node_connectivity

        assert face_node_connectivity.shape == (4132, 3)
        assert numpy.array_equal(face_node_connectivity[0], [2361, 0, 1])
        assert numpy.array_equal(face_node_connectivity[2066], [1137, 1147, 1136])
        assert numpy.array_equal(face_node_connectivity[4131], [2348, 2352, 2350])


class Test_data_access_get_mesh2d_name:
    def test_get_mesh2d_name(self, fou_file: FouFile):
        """
        Testing mesh2d_name property.
        """
        mesh2d_name = fou_file.mesh2d_name
        assert mesh2d_name == "mesh2d"    