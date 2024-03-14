import sys
import tempfile
from contextlib import contextmanager
from io import StringIO

import mock
import netCDF4
import numpy
import pytest

from dfastmi.io.GridOperations import GridOperations


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_read_fm_map:

    def test_read_fm_map_mock_2_2dmeshes_in_file_raises_exception(self):
        """
        Testing read_fm_map: raise exception when multiple meshes are in netCDF4 Dataset
        """
        filename = "mock_file_name.nc"
        varname = "mock_variable"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            netCDF4Dataset.get_variables_by_attributes.return_value = [
                "2dMesh_1",
                "2dMesh_2",
            ]
            with pytest.raises(Exception) as cm:
                GridOperations.read_fm_map(filename, varname)
            assert (
                str(cm.value)
                == "Currently only one 2D mesh supported ... this file contains 2 2D meshes."
            )

    def test_read_fm_map_mock_2dmesh_unknown_varname_and_multi_attribute_raises_exception(
        self,
    ):
        """
        Testing read_fm_map: raise exception when unknown (custom) variable is read from netcdf4 Dataset
        on attribute 'long_name' but 2 are returned after on attribute 'standard_name' return nothing
        """
        filename = "mock_file_name.nc"
        varname = "naam"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            netCDF4Dataset.get_variables_by_attributes.side_effect = [
                [mock.MagicMock(name="mesh2D", spec=netCDF4.Variable)],
                [],
                [
                    [mock.MagicMock(name="aVariable", spec=netCDF4.Variable)],
                    [mock.MagicMock(name="aVariable", spec=netCDF4.Variable)],
                ],
            ]
            with pytest.raises(Exception) as cm:
                GridOperations.read_fm_map(filename, varname)
            assert str(cm.value) == 'Expected one variable for "naam", but obtained 2.'

    def test_read_fm_map_mock_2dmesh_reading_var_without_unlimited_times_with_custom_offset_raises_exception(
        self,
    ):
        """
        Testing read_fm_map: reading var without unlimited times (so time dimension is an integer)
        with custom time offset raises exception. We see this variable not as a time depended variable
        but independend. Time (slicing) cannot work if it is not an argument of the variable
        """
        filename = "mock_file_name.nc"
        varname = "naam"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            var = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [var]
            dim = mock.MagicMock(spec=netCDF4.Dimension)
            dim.isunlimited.return_value = False
            var.get_dims.return_value = [dim]
            with pytest.raises(Exception) as cm:
                GridOperations.read_fm_map(filename, varname, ifld=8)
            assert (
                str(cm.value)
                == 'Trying to access time-independent variable "naam" with time offset -9.'
            )

    def test_read_fm_map_mock_2dmesh_get_double_var(self):
        """
        Testing read_fm_map: reading a variable from netCDF4 dataset should return
        expected return value
        """
        filename = "mock_file_name.nc"
        varname = "naam"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            mock_variable.__getitem__.return_value = [801, 802]
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([801, 802]))

    def test_read_fm_map_instantiate_dataset_in_memory_get_last_double_var(self):
        with tempfile.NamedTemporaryFile(suffix="_map.nc") as temp_file:
            nc_file = netCDF4.Dataset(temp_file.name, mode="w", diskless=True)

            # Define dimensions
            nc_file.createDimension(
                "time", 0
            )  # 3 time dimensions will be defined later (0=unlimited)
            nc_file.createDimension("face", 2)  # 2 faces

            # Create variables
            mesh2d = nc_file.createVariable(
                "mesh2d", "f4"
            )  # 'f4' specifies the data type as float32
            mesh2d.setncattr("cf_role", "mesh_topology")
            mesh2d.setncattr("topology_dimension", 2)

            discharge = nc_file.createVariable("discharge", "f4", ("time", "face"))
            discharge.setncattr("standard_name", "discharge")
            discharge.setncattr("mesh", mesh2d.name)
            discharge.setncattr("location", "face")

            discharge[:] = [[27, 76], [801, 802], [214, 588]]

            with mock.patch("netCDF4.Dataset") as mock_nc_dataset:
                mock_nc_dataset.return_value = nc_file
                data = GridOperations.read_fm_map(
                    filename="mock.nc", varname="discharge"
                )
                assert numpy.array_equal(data, [214, 588])

    def test_read_fm_map_instantiate_dataset_in_memory_get_indexed_double_var(self):
        with tempfile.NamedTemporaryFile(suffix="_map.nc") as temp_file:
            nc_file = netCDF4.Dataset(temp_file.name, mode="w", diskless=True)

            # Define dimensions
            nc_file.createDimension(
                "time", 0
            )  # 3 time dimensions will be defined later (0=unlimited)
            nc_file.createDimension("face", 2)  # 2 faces

            # Create variables
            mesh2d = nc_file.createVariable(
                "mesh2d", "f4"
            )  # 'f4' specifies the data type as float32
            mesh2d.setncattr("cf_role", "mesh_topology")
            mesh2d.setncattr("topology_dimension", 2)

            discharge = nc_file.createVariable("discharge", "f4", ("time", "face"))
            discharge.setncattr("standard_name", "discharge")
            discharge.setncattr("mesh", mesh2d.name)
            discharge.setncattr("location", "face")

            discharge[:] = [[27, 76], [801, 802], [214, 588]]

            with mock.patch("netCDF4.Dataset") as mock_nc_dataset:
                mock_nc_dataset.return_value = nc_file
                data = GridOperations.read_fm_map(
                    filename="mock.nc", varname="discharge", ifld=2
                )
                assert numpy.array_equal(data, [27, 76])

    def test_read_fm_map_from_mocked_dataset_x_coordinates_of_faces_by_projection_x_coordinate(
        self,
    ):
        """
        Testing read_fm_map: x coordinates of the faces by projection_x_coordinate.
        """
        filename = "mocked_file_name.nc"
        varname = "x"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[0].standard_name = "projection_x_coordinate"
            netCDF4Dataset.variables[0].return_value = mock_variable
            netCDF4Dataset.variables[0].__getitem__.return_value = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = (
                "projection_x_coordinate projection_y_coordinate"
            )
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([801, 802]))

    def test_read_fm_map_from_mocked_dataset_x_coordinates_of_faces_by_longitude(self):
        """
        Testing read_fm_map: x coordinates of the faces by longitude.
        """
        filename = "mocked_file_name.nc"
        varname = "x"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[0].standard_name = "longitude"
            netCDF4Dataset.variables[0].return_value = mock_variable
            netCDF4Dataset.variables[0].__getitem__.return_value = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = "longitude latitude"
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([801, 802]))

    def test_read_fm_map_from_mocked_dataset_y_coordinates_of_faces_by_projection_y_coordinate(
        self,
    ):
        """
        Testing read_fm_map: y coordinates of the faces by projection_y_coordinate.
        """
        filename = "mocked_file_name.nc"
        varname = "y"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[1].standard_name = "projection_y_coordinate"
            netCDF4Dataset.variables[1].return_value = mock_variable
            netCDF4Dataset.variables[1].__getitem__.return_value = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = (
                "projection_x_coordinate projection_y_coordinate"
            )
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([801, 802]))

    def test_read_fm_map_from_mocked_dataset_y_coordinates_of_faces_by_latitude(self):
        """
        Testing read_fm_map: y coordinates of the faces by latitude.
        """
        filename = "mocked_file_name.nc"
        varname = "y"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[1].standard_name = "latitude"
            netCDF4Dataset.variables[1].return_value = mock_variable
            netCDF4Dataset.variables[1].__getitem__.return_value = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = "longitude latitude"
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([801, 802]))

    def test_read_fm_map_from_mocked_dataset_mesh_connectivity_variable(self):
        """
        Testing read_fm_map: dataset mesh connectivity variable
        """
        filename = "mocked_file_name.nc"
        varname = "face_node_connectivity"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_mesh = mock.MagicMock(name="mesh2d", spec=netCDF4.Variable)
            mock_mesh.getncattr.return_value = "aVar"
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_mesh]

            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = False
            mock_variable = mock.MagicMock(name="aVar", spec=netCDF4.Variable)
            mock_variable.get_dims.return_value = [dim]
            mock_variable.__getitem__.return_value = numpy.ma.masked_array(
                data=[801, 802]
            )
            netCDF4Dataset.variables = {"aVar": mock_variable}
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([801, 802]))

    def test_read_fm_map_from_mocked_dataset_mesh_connectivity_variable_with_start_index_of_1(
        self,
    ):
        """
        Testing read_fm_map: dataset mesh connectivity variable with start index of 1
        """
        filename = "mocked_file_name.nc"
        varname = "face_node_connectivity"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_mesh = mock.MagicMock(name="mesh2d", spec=netCDF4.Variable)
            mock_mesh.getncattr.return_value = "aVar"
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_mesh]

            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = False
            mock_variable = mock.MagicMock(name="aVar", spec=netCDF4.Variable)
            mock_variable.get_dims.return_value = [dim]
            mock_variable.ncattrs.return_value = ["start_index"]
            mock_variable.getncattr.return_value = 1
            mock_variable.__getitem__.return_value = numpy.ma.masked_array(
                data=[801, 802]
            )
            netCDF4Dataset.variables = {"aVar": mock_variable}
            data = GridOperations.read_fm_map(filename, varname)
            assert numpy.array_equal(data, numpy.array([800, 801]))


class Test_get_mesh_and_facedim_names:
    def test_get_mesh_and_facedim_names_01(self):
        """
        Testing get_mesh_and_facedim_names.
        """
        filename = "mocked_file_name.nc"
        with mock.patch("netCDF4.Dataset") as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_mesh = mock.MagicMock(name="mesh2d", spec=netCDF4.Variable)
            mock_mesh.getncattr.return_value = "aVar"
            netCDF4Dataset.get_variables_by_attributes.return_value = [
                mock_mesh,
                mock_mesh,
            ]
            with pytest.raises(Exception) as cm:
                GridOperations.get_mesh_and_facedim_names(filename)
            assert (
                str(cm.value)
                == "Currently only one 2D mesh supported ... this file contains 2 2D meshes."
            )
