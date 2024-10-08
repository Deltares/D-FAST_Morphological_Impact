import sys
from contextlib import contextmanager
from io import StringIO
from typing import Optional

import netCDF4
import numpy
import pytest
from mock import MagicMock, patch

from dfastmi.io.OutputFile import OutputFile


class TestOutputFile(OutputFile):
    def x_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> numpy.ndarray:
        return numpy.array([[0.0], [1.0], [2.0]])

    def y_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> numpy.ndarray:
        return numpy.array([[0.0], [1.0], [2.0]])

    def water_depth(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> numpy.ndarray:
        return numpy.array([[0.0], [1.0], [2.0]])


def open_test_output_file() -> TestOutputFile:
    filename = "tests/files/"
    return TestOutputFile(filename)


@pytest.fixture
def test_output_file() -> OutputFile:
    return open_test_output_file()


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_OutputFile:
    def _setup_netcdf_variable_mock(
        self,
        dataref: float,
        variable_length: int = 1,
        dimension_isunlimited: bool = False,
    ) -> MagicMock:
        mock_var = MagicMock(spec=netCDF4._netCDF4.Variable)
        return_value = numpy.array([[0.0], [dataref], [2.0]])
        mock_var.__getitem__.return_value = return_value
        mock_var.__len__.return_value = variable_length

        mock_dim = MagicMock(spec=netCDF4._netCDF4.Dimension)
        mock_var.get_dims.return_value = [mock_dim]
        mock_dim.isunlimited.return_value = dimension_isunlimited
        return mock_var

    def _setup_mesh2d_mock(self, getncattr_return_value: str) -> MagicMock:
        mock_mesh2d = MagicMock()
        mock_mesh2d.name = "myMesh2d"
        mock_mesh2d.getncattr.return_value = getncattr_return_value
        return mock_mesh2d

    def _setup_coordinate_mock(
        self, coordinate_standard_name: str, coor_ref: float = 1.0
    ) -> MagicMock:
        mock_coordinate = MagicMock()
        return_value = numpy.array([[0.0], [coor_ref], [2.0]])
        mock_coordinate.standard_name = coordinate_standard_name
        mock_coordinate.__getitem__.return_value = return_value
        return mock_coordinate

    @pytest.mark.parametrize(
        "data_file, dataref",
        [
            (open_test_output_file(), 1.0),
        ],
    )
    def test_x_velocity(self, data_file: test_output_file, dataref: float):
        """
        Testing x_velocity.
        """
        datac = data_file.x_velocity()
        assert datac[1] == dataref

    @pytest.mark.parametrize(
        "data_file, dataref",
        [
            (open_test_output_file(), 1.0),
        ],
    )
    def test_y_velocity(self, data_file: TestOutputFile, dataref: float):
        """
        Testing y_velocity.
        """
        datac = data_file.y_velocity()
        assert datac[1] == dataref

    @pytest.mark.parametrize(
        "data_file, dataref",
        [
            (open_test_output_file(), 1.0),
        ],
    )
    def test_water_depth(self, data_file: TestOutputFile, dataref: float):
        """
        Testing water_depth.
        """
        datac = data_file.water_depth()
        assert datac[1] == dataref

    def test_read_face_variable_standard_more_than_1_return_value_throws_an_exception(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by standard name.
        """
        varname = "standard_name"
        return_value = numpy.array([[0.0], [1.0], [2.0]])

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=return_value,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            with pytest.raises(Exception) as cm:
                _ = test_output_file.read_face_variable(varname)
            assert (
                str(cm.value)
                == 'Expected one variable for "standard_name", but obtained 3.'
            )

    def test_read_face_variable_standard(self, test_output_file: OutputFile):
        """
        Testing read_face_variable: variable by standard name.
        """

        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(dataref)
        varname = "standard_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[mock_var],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            datac = test_output_file.read_face_variable(varname)

            assert datac[1] == dataref

    def test_read_face_variable_standard_not_mocking_get_face_vars_by_standard_name(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by standard name.
        """

        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(dataref)
        varname = "standard_name"

        with (patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.get_variables_by_attributes.return_value = [mock_var]

            datac = test_output_file.read_face_variable(varname)
            assert datac[1] == dataref

    def test_read_face_variable_long_name(self, test_output_file: OutputFile):
        """
        Testing read_face_variable: variable by long name.
        """

        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(dataref)
        varname = "long_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_long_name",
                return_value=[mock_var],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset

            datac = test_output_file.read_face_variable(varname)
            assert datac[1] == dataref

    def test_read_face_variable_long_name_not_mocking_get_face_vars_by_long_name(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by long name.
        """

        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(dataref)
        varname = "long_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.get_variables_by_attributes.return_value = [mock_var]

            datac = test_output_file.read_face_variable(varname)
            assert datac[1] == dataref

    def test_read_face_variable_long_name_is_unlimited_no_time_slice(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by long name.
        """
        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(dataref, dimension_isunlimited=True)
        varname = "long_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_long_name",
                return_value=[mock_var],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset

            datac = test_output_file.read_face_variable(varname)
            assert datac[1] == dataref

    def test_read_face_variable_long_name_is_unlimited_with_1_time_slice(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by long name.
        """

        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(
            dataref, variable_length=2, dimension_isunlimited=True
        )
        varname = "long_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_long_name",
                return_value=[mock_var],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset

            datac = test_output_file.read_face_variable(varname, 1)
            assert datac[1] == dataref

    def test_read_face_variable_long_name_is_time_independent_variable_with_1_time_slice_throws_exeption(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by long name.
        """

        dataref = 80.1
        mock_var = self._setup_netcdf_variable_mock(dataref, variable_length=2)
        varname = "long_name"
        mock_var.name = varname

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_long_name",
                return_value=[mock_var],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset

            with pytest.raises(Exception) as cm:
                _ = test_output_file.read_face_variable(varname, 1)
            assert (
                str(cm.value)
                == f'Trying to access time-independent variable "{varname}" with time offset -2.'
            )

    def test_read_face_variable_long_name_more_than_1_return_value_throws_an_exception(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by long name.
        """
        return_value = numpy.array([[0.0], [1.0], [2.0]])
        varname = "long_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_long_name",
                return_value=return_value,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            with pytest.raises(Exception) as cm:
                _ = test_output_file.read_face_variable(varname)
            assert (
                str(cm.value)
                == 'Expected one variable for "long_name", but obtained 3.'
            )

    def test_read_face_variable_long_name_no_return_value_throws_an_exception(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_variable: variable by long name.
        """
        varname = "long_name"

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_standard_name",
                return_value=[],
            ),
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_face_vars_by_long_name",
                return_value=[],
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock()
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            with pytest.raises(Exception) as cm:
                _ = test_output_file.read_face_variable(varname)
            assert (
                str(cm.value)
                == 'Expected one variable for "long_name", but obtained 0.'
            )

    def test_read_node_x_coordinates(self, test_output_file: OutputFile):
        """
        Testing read_node_x_coordinates
        """

        mock_mesh2d = self._setup_mesh2d_mock(
            "projection_x_coordinate projection_y_coordinate"
        )

        coor_ref = 80.1
        mock_x_coordinate = self._setup_coordinate_mock(
            "projection_x_coordinate", coor_ref
        )
        mock_y_coordinate = self._setup_coordinate_mock("projection_y_coordinate")

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_mesh2d_variable",
                return_value=mock_mesh2d,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.variables = {
                "myMesh2d": mock_mesh2d,
                "projection_x_coordinate": mock_x_coordinate,
                "projection_y_coordinate": mock_y_coordinate,
            }

            x_coor = test_output_file.node_x_coordinates
            assert x_coor[1] == coor_ref

    def test_read_node_y_coordinates(self, test_output_file: OutputFile):
        """
        Testing read_node_y_coordinates
        """

        mock_mesh2d = self._setup_mesh2d_mock(
            "projection_x_coordinate projection_y_coordinate"
        )

        coor_ref = 80.1
        mock_x_coordinate = self._setup_coordinate_mock("projection_x_coordinate")
        mock_y_coordinate = self._setup_coordinate_mock(
            "projection_y_coordinate", coor_ref
        )

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_mesh2d_variable",
                return_value=mock_mesh2d,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.variables = {
                "myMesh2d": mock_mesh2d,
                "projection_x_coordinate": mock_x_coordinate,
                "projection_y_coordinate": mock_y_coordinate,
            }

            y_coor = test_output_file.node_y_coordinates
            assert y_coor[1] == coor_ref

    def test_read_node_x_coordinates_via_longitude(self, test_output_file: OutputFile):
        """
        Testing read_node_x_coordinates via longitude
        """

        mock_mesh2d = self._setup_mesh2d_mock("longitude latitude")

        coor_ref = 80.1
        mock_x_coordinate = self._setup_coordinate_mock("longitude", coor_ref)
        mock_y_coordinate = self._setup_coordinate_mock("latitude")

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_mesh2d_variable",
                return_value=mock_mesh2d,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.variables = {
                "myMesh2d": mock_mesh2d,
                "longitude": mock_x_coordinate,
                "latitude": mock_y_coordinate,
            }

            x_coor = test_output_file.node_x_coordinates
            assert x_coor[1] == coor_ref

    def test_read_node_y_coordinates_via_latitude(self, test_output_file: OutputFile):
        """
        Testing read_node_y_coordinates via latitude
        """

        mock_mesh2d = self._setup_mesh2d_mock("longitude latitude")

        coor_ref = 80.1
        mock_x_coordinate = self._setup_coordinate_mock("longitude")
        mock_y_coordinate = self._setup_coordinate_mock("latitude", coor_ref)

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_mesh2d_variable",
                return_value=mock_mesh2d,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.variables = {
                "myMesh2d": mock_mesh2d,
                "longitude": mock_x_coordinate,
                "latitude": mock_y_coordinate,
            }

            y_coor = test_output_file.node_y_coordinates
            assert y_coor[1] == coor_ref

    def test_read_face_node_connectivity(self, test_output_file: OutputFile):
        """
        Testing read_face_node_connectivity
        """

        mock_mesh2d = self._setup_mesh2d_mock("face_node_connectivity")

        mock_face_node_connectivity = MagicMock()
        node_index_ref = 1.0
        return_value_node_indices = numpy.array([[0.0], [node_index_ref], [2.0]])
        mock_face_node_connectivity.__getitem__.return_value = return_value_node_indices

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_mesh2d_variable",
                return_value=mock_mesh2d,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.variables = {
                "myMesh2d": mock_mesh2d,
                "face_node_connectivity": mock_face_node_connectivity,
            }

            face_node_connectivity = test_output_file.face_node_connectivity
            assert face_node_connectivity[1] == node_index_ref

    def test_read_face_node_connectivity_with_start_index(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_face_node_connectivity with a start index (1)
        """

        mock_mesh2d = self._setup_mesh2d_mock("face_node_connectivity")

        mock_face_node_connectivity = MagicMock()
        node_index_ref = 3.0
        start_index = 1
        return_value_node_indices = numpy.array(
            [[3.0], [node_index_ref + start_index], [5.0]]
        )
        mock_face_node_connectivity.ncattrs.return_value = "start_index"
        mock_face_node_connectivity.getncattr.return_value = start_index
        mock_face_node_connectivity.__getitem__.return_value = return_value_node_indices

        with (
            patch(
                "dfastmi.io.OutputFile.OutputFile._get_mesh2d_variable",
                return_value=mock_mesh2d,
            ),
            patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,
        ):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.variables = {
                "myMesh2d": mock_mesh2d,
                "face_node_connectivity": mock_face_node_connectivity,
            }

            face_node_connectivity = test_output_file.face_node_connectivity
            assert face_node_connectivity[1] == node_index_ref

    def test_read_mesh2d_name(self, test_output_file: OutputFile):
        """
        Testing read_mesh2d_name
        """
        mock_mesh2d = MagicMock()
        mock_mesh2d.name = "myMesh2d"

        with (patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.get_variables_by_attributes.return_value = [mock_mesh2d]

            mesh2d_name = test_output_file.mesh2d_name
            mesh2d_name_ref = "myMesh2d"
            assert mesh2d_name == mesh2d_name_ref

    def test_read_mesh2d_name_with_3_mesh2d_throw_exception(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_mesh2d_name
        """
        mock_mesh2d = MagicMock()
        mock_mesh2d.name = "myMesh2d"

        with (patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.get_variables_by_attributes.return_value = [
                mock_mesh2d,
                mock_mesh2d,
                mock_mesh2d,
            ]
            with pytest.raises(Exception) as cm:
                _ = test_output_file.mesh2d_name
            assert (
                str(cm.value)
                == "Currently only one 2D mesh supported ... this file contains 3 2D meshes."
            )

    def test_read_mesh2d_name_with_0_mesh2d_throw_exception(
        self, test_output_file: OutputFile
    ):
        """
        Testing read_mesh2d_name
        """
        with (patch("dfastmi.io.OutputFile.nc.Dataset") as mock_nc_dataset,):
            mock_dataset = MagicMock(spec=netCDF4._netCDF4.Dataset)
            mock_nc_dataset.return_value.__enter__.return_value = mock_dataset
            mock_dataset.get_variables_by_attributes.return_value = []
            with pytest.raises(Exception) as cm:
                _ = test_output_file.mesh2d_name
            assert (
                str(cm.value)
                == "Currently only one 2D mesh supported ... this file contains 0 2D meshes."
            )
