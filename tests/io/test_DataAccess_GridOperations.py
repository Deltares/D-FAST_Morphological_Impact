from pathlib import Path
import sys
import os
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


class Test_data_access_read_variable():
    def test_read_variable_04(self):
        """
        Testing read_variable: variable by standard name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "sea_floor_depth_below_sea_surface"
        map_file = GridOperations(filename)
        datac = map_file.read_face_variable(varname)
        dataref = 3.894498393076889
        assert datac[1] == dataref

    def test_read_variable_05(self):
        """
        Testing read_variable: variable by long name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "Water level"
        map_file = GridOperations(filename)
        datac = map_file.read_face_variable(varname)
        dataref = 3.8871328177527262
        assert datac[1] == dataref

    def test_read_variable_06(self):
        """
        Testing read_variable: variable by long name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "water level"
        with pytest.raises(Exception) as cm:
            map_file = GridOperations(filename)
            datac = map_file.read_face_variable(varname)
        assert str(cm.value) == 'Expected one variable for "water level", but obtained 0.'

    def test_read_variable_07(self):
        """
        Testing read_variable: multiple mesh2dids.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "water level"
        with pytest.raises(Exception) as cm:
            map_file = GridOperations(filename)
            datac = map_file.read_face_variable(varname)
        assert str(cm.value) == 'Expected one variable for "water level", but obtained 0.'

class TestReadGridGeometryFromMapFile():
    def test_get_node_x_coordinates(self):
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        map_file = GridOperations(filename)
        
        node_x_coordinates = map_file.node_x_coordinates
        
        assert node_x_coordinates.shape == (2363,)
        assert node_x_coordinates[0] == pytest.approx(62.5)
        assert node_x_coordinates[1181] == pytest.approx(6750)
        assert node_x_coordinates[2362] == pytest.approx(0.0)
        
    def test_get_node_y_coordinates(self):
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        map_file = GridOperations(filename)

        node_y_coordinates = map_file.node_y_coordinates
        
        assert node_y_coordinates.shape == (2363,)
        assert node_y_coordinates[0] == pytest.approx(7000)
        assert node_y_coordinates[1181] == pytest.approx(7200.542889)
        assert node_y_coordinates[2362] == pytest.approx(7500)
     
    def test_get_face_node_connectivity(self):
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        map_file = GridOperations(filename)

        face_node_connectivity = map_file.face_node_connectivity
        
        assert face_node_connectivity.shape == (4132, 3)
        assert numpy.array_equal(face_node_connectivity[0], [2361, 0, 1])
        assert numpy.array_equal(face_node_connectivity[2066], [1137, 1147, 1136])
        assert numpy.array_equal(face_node_connectivity[4131], [2348, 2352, 2350])
          

class Test_data_access_get_mesh_and_facedim_names():
    def test_get_mesh2d_name(self):
        """
        Testing mesh2d_name property.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        map_file = GridOperations(filename)
        mesh2d_name = map_file.mesh2d_name
        assert mesh2d_name == "mesh2d"

    def test_get_face_dimension_name(self):
        """
        Testing face_dimension_name property.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        map_file = GridOperations(filename)
        face_dimension_name = map_file.face_dimension_name
        assert face_dimension_name == "mesh2d_nFaces"

class Test_ugrid_add():
    dst_filename = "test.nc"
    
    @pytest.fixture
    def setup_data(self):
        """
        Foreach test setup test netcdf file, clean up after test is run
        """
        if os.path.exists(self.dst_filename):
            os.remove(self.dst_filename)
        nc_file = netCDF4.Dataset(self.dst_filename, mode='w')
        try:
            # Define dimensions
            nc_file.createDimension('time', 0)  # 3 time dimensions will be defined later (0=unlimited)
            nc_file.createDimension('face', 4132)  # 4132 faces

            # Create variables
            mesh2d = nc_file.createVariable('mesh2d', 'f4')  # 'f4' specifies the data type as float32
            mesh2d.setncattr('cf_role', "mesh_topology")
            mesh2d.setncattr('topology_dimension', 2)
        finally:
            nc_file.close()
        yield
        
        print("Trying to remove created NetCDF file 'test.nc'.")
        if os.path.exists(self.dst_filename):            
            try:
                os.remove(self.dst_filename)
                print("NetCDF file 'test.nc' removed successfully.")
            except Exception as e:
                print("Failed to remove created NetCDF file 'test.nc'. Exception thrown : "+ str(e))
        

    def test_ugrid_add_01(self, setup_data):
        """
        Testing ugrid_add.
        """
        meshname = "mesh2d"
        facedim = "face"
        #
        varname = "xxx"
        ldata = numpy.zeros((4132))
        ldata[1] = 3.14159
        long_name = "added_variable"
        unit = "some_unit"
        #
        map_file = GridOperations(self.dst_filename)        
        map_file.add_variable(varname, ldata, meshname, facedim, long_name, unit)
        #
        datac = map_file.read_face_variable(long_name)
        assert datac[1] == ldata[1]

    def test_ugrid_add_02(self, setup_data):
        """
        Testing ugrid_add with custom unit.
        """
        meshname = "mesh2d"
        facedim = "face"
        #
        varname = "new_xxx"
        ldata = numpy.zeros((4132))
        ldata[1] = 3.14159
        long_name = "new_added_variable"
        units = "kmh"
        #
        
        map_file = GridOperations(self.dst_filename)
        map_file.add_variable(varname, ldata, meshname, facedim, long_name, units)
        rootgrp = netCDF4.Dataset(self.dst_filename)
        var = rootgrp.get_variables_by_attributes(
                long_name=long_name, mesh=meshname, location="face"
            )
        #
        new_added_units = var[0].units
        rootgrp.close()
        assert new_added_units == units


class Test_copy_var():
    dst_filename = "test.nc"
    
    @pytest.fixture
    def setup_data(self):
        """
        Foreach test setup test netcdf file, clean up after test is run
        """
        
        if os.path.exists(self.dst_filename):            
            os.remove(self.dst_filename)
            
        nc_file = netCDF4.Dataset(self.dst_filename, mode='w')
        try:

            # Define dimensions
            nc_file.createDimension('time', 0)  # 3 time dimensions will be defined later (0=unlimited)
            nc_file.createDimension('face', 2)  # 2 faces

            # Create variables
            mesh2d = nc_file.createVariable('mesh2d', 'f4')  # 'f4' specifies the data type as float32
            mesh2d.setncattr('cf_role', "mesh_topology")
            mesh2d.setncattr('topology_dimension', 2)

            print("NetCDF file 'test.nc' created successfully.")

        finally:
            nc_file.close()
        yield
        
        print("Trying to remove created NetCDF file 'test.nc'.")
        if os.path.exists(self.dst_filename):            
            try:
                os.remove(self.dst_filename)
                print("NetCDF file 'test.nc' removed successfully.")
            except Exception as e:
                print("Failed to remove created NetCDF file 'test.nc'. Exception thrown : "+ str(e))        

    def test_copy_var_01(self, setup_data):
        """
        Testing copy_var.
        """
        src_filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        #
        
        src = netCDF4.Dataset(src_filename)
        dst = netCDF4.Dataset(self.dst_filename, "a")
        GridOperations._copy_var(src, "mesh2d_s1", dst)
        src.close()
        dst.close()
        #                
        varname = "sea_surface_height"
        map_file = GridOperations(self.dst_filename)
        datac = map_file.read_face_variable(varname)
        dataref = 3.8871328177527262
        assert datac[1] == dataref


class Test_copy_ugrid():
    dst_filename = Path("test.nc")
    
    @pytest.fixture
    def setup_data(self):
        """
        Foreach test clean up after test is run
        """        
        yield
                 
        try:
            self.dst_filename.unlink(missing_ok=True)
            print("NetCDF file 'test.nc' removed successfully.")
        except Exception as e:
            print("Failed to remove created NetCDF file 'test.nc'. Exception thrown : "+ str(e))        

    def test_copy_ugrid_01(self, setup_data):
        """
        Testing copy_ugrid (depends on copy_var).
        """
        src_filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        
        map_file = GridOperations(src_filename)
        map_file.copy_ugrid(self.dst_filename)
        #
        map_file = GridOperations(self.dst_filename)
        datac = map_file.face_node_connectivity
        dataref = 2352
        assert datac[-1][1] == dataref


