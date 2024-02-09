import sys
from contextlib import contextmanager
from io import StringIO
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


class Test_data_access_read_fm_map():
    def test_read_fm_map_from_example_file_x_coordinates_of_faces(self):
        """
        Testing read_fm_map: x coordinates of the faces.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "x"
        #location = "face"
        datac = GridOperations.read_fm_map(filename, varname)
        dataref = 41.24417604888325
        assert datac[1] == dataref

    def test_read_fm_map_02(self):
        """
        Testing read_fm_map: y coordinates of the edges.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "y"
        location = "edge"
        datac = GridOperations.read_fm_map(filename, varname, location)
        dataref = 7059.853000358055
        assert datac[1] == dataref

    def test_read_fm_map_03(self):
        """
        Testing read_fm_map: face node connectivity.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "face_node_connectivity"
        datac = GridOperations.read_fm_map(filename, varname)
        dataref = 2352
        assert datac[-1][1] == dataref

    def test_read_fm_map_04(self):
        """
        Testing read_fm_map: variable by standard name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "sea_floor_depth_below_sea_surface"
        datac = GridOperations.read_fm_map(filename, varname)
        dataref = 3.894498393076889
        assert datac[1] == dataref

    def test_read_fm_map_05(self):
        """
        Testing read_fm_map: variable by long name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "Water level"
        datac = GridOperations.read_fm_map(filename, varname)
        dataref = 3.8871328177527262
        assert datac[1] == dataref

    def test_read_fm_map_06(self):
        """
        Testing read_fm_map: variable by long name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "water level"
        with pytest.raises(Exception) as cm:
            datac = GridOperations.read_fm_map(filename, varname)
        assert str(cm.value) == 'Expected one variable for "water level", but obtained 0.'

    def test_read_fm_map_07(self):
        """
        Testing read_fm_map: multiple mesh2dids.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "water level"
        with pytest.raises(Exception) as cm:
            datac = GridOperations.read_fm_map(filename, varname)
        assert str(cm.value) == 'Expected one variable for "water level", but obtained 0.'


class Test_data_access_get_mesh_and_facedim_names():
    def test_get_mesh_and_facedim_names_01(self):
        """
        Testing get_mesh_and_facedim_names.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        name_and_dim = GridOperations.get_mesh_and_facedim_names(filename)
        assert name_and_dim == ("mesh2d", "mesh2d_nFaces")


class Test_ugrid_add():
    def test_ugrid_add_01(self):
        """
        Testing ugrid_add.
        """
        dst_filename = "test.nc"
        meshname = "mesh2d"
        facedim = "mesh2d_nFaces"
        #
        varname = "xxx"
        ldata = numpy.zeros((4132))
        ldata[1] = 3.14159
        long_name = "added_variable"
        #
        GridOperations.ugrid_add(dst_filename, varname, ldata, meshname, facedim, long_name)
        #
        datac = GridOperations.read_fm_map(dst_filename, long_name)
        assert datac[1] == ldata[1]

    def test_ugrid_add_02(self):
        """
        Testing ugrid_add with custom unit.
        """
        dst_filename = "test.nc"
        meshname = "mesh2d"
        facedim = "mesh2d_nFaces"
        #
        varname = "new_xxx"
        ldata = numpy.zeros((4132))
        ldata[1] = 3.14159
        long_name = "new_added_variable"
        units = "kmh"
        #
        GridOperations.ugrid_add(dst_filename, varname, ldata, meshname, facedim, long_name, units)
        rootgrp = netCDF4.Dataset(dst_filename)
        var = rootgrp.get_variables_by_attributes(
                long_name=long_name, mesh=meshname, location="face"
            )
        #
        assert var[0].units == units


class Test_copy_var():
    def test_copy_var_01(self):
        """
        Testing copy_var.
        """
        src_filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        dst_filename = "test.nc"
        #
        with netCDF4.Dataset(src_filename) as src:
            with netCDF4.Dataset(dst_filename, "a") as dst:
                GridOperations.copy_var(src, "mesh2d_s1", dst)
        #
        varname = "sea_surface_height"
        datac = GridOperations.read_fm_map(dst_filename, varname)
        dataref = 3.8871328177527262
        assert datac[1] == dataref


class Test_copy_ugrid():
    def test_copy_ugrid_01(self):
        """
        Testing copy_ugrid (depends on copy_var).
        """
        src_filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        dst_filename = "test.nc"
        meshname, facedim = GridOperations.get_mesh_and_facedim_names(src_filename)
        GridOperations.copy_ugrid(src_filename, meshname, dst_filename)
        #
        varname = "face_node_connectivity"
        datac = GridOperations.read_fm_map(dst_filename, varname)
        dataref = 2352
        assert datac[-1][1] == dataref