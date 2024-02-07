import io
import mock
import context
import dfastmi.io
import configparser
import os
import numpy
import netCDF4
import tempfile

import pytest

import sys
from contextlib import contextmanager
from io import StringIO

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_load_program_texts():
     def test_load_program_texts_in_global_PROGTEXT(self):
         with mock.patch("builtins.open", mock.mock_open(read_data="[header]\r\ncontent\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")
            assert dfastmi.io.PROGTEXTS['header'] == ['content']
         
     def test_load_program_texts_multiline_in_global_PROGTEXT(self):
         with mock.patch("builtins.open", mock.mock_open(read_data="[header]\r\ncontent\r\ncontent2\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")
            assert dfastmi.io.PROGTEXTS['header'] == ['content', 'content2']
         
     def test_load_program_texts_line_header_with_no_value_in_global_PROGTEXT(self):
         with mock.patch("builtins.open", mock.mock_open(read_data="[header]\r\n[otherheader]\r\ncontent\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")
            assert dfastmi.io.PROGTEXTS['header'] == []
            assert dfastmi.io.PROGTEXTS['otherheader'] == ['content']
         
     def test_load_program_texts_double_header_throws_exception(self):
         with mock.patch("builtins.open", mock.mock_open(read_data="[header]\r\n[header]\r\ncontent\r\n")) as mock_file:
            with pytest.raises(Exception) as cm:
                dfastmi.io.load_program_texts("")
            assert str(cm.value) == 'Duplicate entry for "header" in "".'
         
    
class Test_data_access_load_program_texts():
    def test_load_program_texts_load_default_uk_messages_file(self):
        """
        Testing load_program_texts.
        """
        print("current work directory: ", os.getcwd())
        assert dfastmi.io.load_program_texts("dfastmi/messages.UK.ini") == None    

class Test_log_text():
    @pytest.fixture
    def setup_data(self):
        dfastmi.io.PROGTEXTS = {}        
        
    def test_log_text_no_key_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        with captured_output() as (out, err):
            dfastmi.io.log_text(key)
        outstr = out.getvalue().splitlines()
        strref = "No message found for " + key
        assert outstr[0] == strref
    
    def test_log_text_with_key_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        with mock.patch("builtins.open", mock.mock_open(read_data="[confirm]\r\nConfirm key found\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")
        with captured_output() as (out, err):
            dfastmi.io.log_text(key)
        outstr = out.getvalue().splitlines()
        strref = "Confirm key found"
        assert outstr[0] == strref

    def test_log_text_with_key_and_variable_id_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        dict = {"value": "ABC"}
        with mock.patch("builtins.open", mock.mock_open(read_data="[confirm]\r\nConfirm key found with {value}\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")
        with captured_output() as (out, err):
            dfastmi.io.log_text(key,dict=dict)
        outstr = out.getvalue().splitlines()
        strref = "Confirm key found with ABC"
        assert outstr[0] == strref
    
    def test_log_text_two_times_with_key_and_variable_id_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        dict = {"value": "ABC"}
        with mock.patch("builtins.open", mock.mock_open(read_data="[confirm]\r\nConfirm key found with {value}\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")
        with captured_output() as (out, err):
            dfastmi.io.log_text(key, dict=dict, repeat=2)
        outstr = out.getvalue().splitlines()
        strref = "Confirm key found with ABC"
        assert outstr[0] == strref
        assert outstr[1] == strref

    def test_log_text_with_key_and_variable_id_in_global_PROGTEXT_write_in_file(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        dict = {"value": "ABC"}
        with mock.patch("builtins.open", mock.mock_open(read_data="[confirm]\r\nConfirm key found with {value}\r\n")) as mock_file:
            dfastmi.io.load_program_texts("")

        with mock.patch("builtins.open") as mock_file:
            dfastmi.io.log_text(key, dict=dict, file=mock_file)
            assert mock_file.write.called
            mock_file.write.assert_called_once_with("Confirm key found with ABC\n")    

class Test_data_access_log_text():
    @pytest.fixture
    def setup_data(self):
        dfastmi.io.load_program_texts("dfastmi/messages.UK.ini")

    def test_log_text_check_content_messages_uk(self, setup_data: None):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        with captured_output() as (out, err):
            dfastmi.io.log_text(key)
        outstr = out.getvalue().splitlines()
        strref = ['Confirm using "y" ...', '']
        assert outstr == strref

    def test_log_text_empty_keys(self, setup_data: None):
        """
        Testing standard output of a repeated text without expansion.
        """
        key = ""
        nr = 3
        with captured_output() as (out, err):
            dfastmi.io.log_text(key, repeat=nr)
        outstr = out.getvalue().splitlines()
        strref = ['', '', '']
        assert outstr == strref

    def test_log_text_replace_variable_id_with_provided_value_in_dictionary(self, setup_data: None):
        """
        Testing standard output of a text with expansion.
        """
        key = "reach"
        dict = {"reach": "ABC"}
        with captured_output() as (out, err):
            dfastmi.io.log_text(key, dict=dict)
        outstr = out.getvalue().splitlines()
        strref = ['The measure is located on reach ABC']
        assert outstr == strref

    def test_log_text_replace_variable_id_with_provided_value_in_dictionary_and_write_in_file(self, setup_data: None):
        """
        Testing file output of a text with expansion.
        """
        key = "reach"
        dict = {"reach": "ABC"}
        filename = "test.log"
        with open(filename, "w") as f:
            dfastmi.io.log_text(key, dict=dict, file=f)
        all_lines = open(filename, "r").read().splitlines()
        strref = ['The measure is located on reach ABC']
        assert all_lines == strref

class Test_get_filename():
    def test_get_filename_get_filename_from_uk_keys(self):
        """
        Testing get_filename wrapper for get_text.
        """
        dfastmi.io.PROGTEXTS = {"filename_report.out": ["report.txt"]}
        file = dfastmi.io.get_filename("report.out")
        assert  file == "report.txt"

class Test_data_access_get_filename():
    def test_get_filename_get_filename_from_uk_keys(self):
        """
        Testing get_filename wrapper for get_text.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.UK.ini")
        assert dfastmi.io.get_filename("report.out") == "report.txt"

class Test_get_text():
    def test_get_text_from_empty_global_PROGTEXTS_results_in_no_message_found(self):
        """
        Testing get_text: key not found.
        """
        dfastmi.io.PROGTEXTS = {}
        assert dfastmi.io.get_text("@") == ["No message found for @"]

    def test_get_text_from_empty_key_in_global_PROGTEXTS_results_in_specified_value(self):
        """
        Testing get_text: empty line key.
        """
        dfastmi.io.PROGTEXTS = {'':''}
        assert dfastmi.io.get_text("") == ''

    def test_get_text_from_custom_key_in_global_PROGTEXTS_results_in_specified_value(self):
        """
        Testing get_text: "confirm" key.
        """
        dfastmi.io.PROGTEXTS = {"confirm":'Confirm using "y" ...'}
        confirmText = dfastmi.io.get_text("confirm")
        assert confirmText == 'Confirm using "y" ...'


class Test_data_access_get_text():
    @pytest.fixture
    def setup_data(self):
        dfastmi.io.load_program_texts("dfastmi/messages.UK.ini")

    def test_get_text_messages_uk_loaded_key_not_found(self):
        """
        Testing get_text: key not found.
        """
        assert dfastmi.io.get_text("@") == ["No message found for @"]

    def test_get_text_messages_uk_loaded_key_empty(self, setup_data: None):
        """
        Testing get_text: empty line key.
        """
        assert dfastmi.io.get_text("") == [""]

    def test_get_text_messages_uk_loaded_key_confirm_returns_value(self, setup_data: None):
        """
        Testing get_text: "confirm" key.
        """
        confirmText = dfastmi.io.get_text("confirm")
        assert confirmText == ['Confirm using "y" ...','']

class Test_write_config():
    def test_write_config_check_written(self):
        """
        Testing write_config.
        """
        filename = "test.cfg"
        config = configparser.ConfigParser()
        config.add_section("G 1")
        config["G 1"]["K 1"] = "V 1"
        config.add_section("Group 2")
        config["Group 2"]["K1"] = "1.0 0.1 0.0 0.01"
        config["Group 2"]["K2"] = "2.0 0.2 0.02 0.0"
        config.add_section("Group 3")
        config["Group 3"]["LongKey"] = "3"

        with mock.patch("builtins.open") as mock_file:
            dfastmi.io.write_config(filename, config)
            mock_file.assert_called_once_with(filename, 'w')
            mock_file.return_value.__enter__().write.assert_called()
            mock_file.return_value.__enter__().write.assert_any_call('[G 1]\n')
            mock_file.return_value.__enter__().write.assert_any_call('  k 1     = V 1\n')
            mock_file.return_value.__enter__().write.assert_any_call('\n')
            mock_file.return_value.__enter__().write.assert_any_call('[Group 2]\n')
            mock_file.return_value.__enter__().write.assert_any_call('  k1      = 1.0 0.1 0.0 0.01\n')
            mock_file.return_value.__enter__().write.assert_any_call('  k2      = 2.0 0.2 0.02 0.0\n')
            mock_file.return_value.__enter__().write.assert_any_call('[Group 3]\n')
            mock_file.return_value.__enter__().write.assert_any_call('  longkey = 3\n')
            

        

class Test_data_access_write_config():
    def test_write_config_and_read_back(self):
        """
        Testing write_config.
        """
        filename = "test.cfg"
        config = configparser.ConfigParser()
        config.add_section("G 1")
        config["G 1"]["K 1"] = "V 1"
        config.add_section("Group 2")
        config["Group 2"]["K1"] = "1.0 0.1 0.0 0.01"
        config["Group 2"]["K2"] = "2.0 0.2 0.02 0.0"
        config.add_section("Group 3")
        config["Group 3"]["LongKey"] = "3"
        dfastmi.io.write_config(filename, config)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['[G 1]',
                         '  k 1     = V 1',
                         '',
                         '[Group 2]',
                         '  k1      = 1.0 0.1 0.0 0.01',
                         '  k2      = 2.0 0.2 0.02 0.0',
                         '',
                         '[Group 3]',
                         '  longkey = 3']
        assert all_lines == all_lines_ref

class Test_read_fm_map():

    def test_read_fm_map_mock_2_2dmeshes_in_file_raises_exception(self):
        """
        Testing read_fm_map: raise exception when multiple meshes are in netCDF4 Dataset
        """
        filename = "mock_file_name.nc"
        varname = "mock_variable"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            netCDF4Dataset.get_variables_by_attributes.return_value = ['2dMesh_1', '2dMesh_2']
            with pytest.raises(Exception) as cm:
                dfastmi.io.read_fm_map(filename, varname)
            assert str(cm.value) == "Currently only one 2D mesh supported ... this file contains 2 2D meshes."

    def test_read_fm_map_mock_2dmesh_unknown_varname_and_multi_attribute_raises_exception(self):
        """
        Testing read_fm_map: raise exception when unknown (custom) variable is read from netcdf4 Dataset 
        on attribute 'long_name' but 2 are returned after on attribute 'standard_name' return nothing
        """
        filename = "mock_file_name.nc"
        varname = "naam"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            netCDF4Dataset.get_variables_by_attributes.side_effect = [
                [mock.MagicMock(name="mesh2D", spec=netCDF4.Variable)], 
                [], 
                [
                    [mock.MagicMock(name="aVariable", spec=netCDF4.Variable)],
                    [mock.MagicMock(name="aVariable", spec=netCDF4.Variable)]
                ]]            
            with pytest.raises(Exception) as cm:
                dfastmi.io.read_fm_map(filename, varname)
            assert str(cm.value) == 'Expected one variable for "naam", but obtained 2.'

    def test_read_fm_map_mock_2dmesh_reading_var_without_unlimited_times_with_custom_offset_raises_exception(self):
        """
        Testing read_fm_map: reading var without unlimited times (so time dimension is an integer) 
        with custom time offset raises exception. We see this variable not as a time depended variable 
        but independend. Time (slicing) cannot work if it is not an argument of the variable 
        """
        filename = "mock_file_name.nc"
        varname = "naam"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            var = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [var]
            dim = mock.MagicMock(spec=netCDF4.Dimension)
            dim.isunlimited.return_value = False
            var.get_dims.return_value = [dim]
            with pytest.raises(Exception) as cm:
                dfastmi.io.read_fm_map(filename, varname, ifld=8)
            assert str(cm.value) == 'Trying to access time-independent variable "naam" with time offset -9.'
            
    def test_read_fm_map_mock_2dmesh_get_double_var(self):
        """
        Testing read_fm_map: reading a variable from netCDF4 dataset should return 
        expected return value
        """
        filename = "mock_file_name.nc"
        varname = "naam"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            mock_variable.__getitem__.return_value = [801, 802]
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([801,802]))

    def test_read_fm_map_instantiate_dataset_in_memory_get_last_double_var(self):
        with tempfile.NamedTemporaryFile(suffix='_map.nc') as temp_file:
            nc_file = netCDF4.Dataset(temp_file.name, mode='w', diskless=True)
            
            # Define dimensions
            nc_file.createDimension('time', 0)  # 3 time dimensions will be defined later (0=unlimited)
            nc_file.createDimension('face', 2)  # 2 faces

            # Create variables
            mesh2d = nc_file.createVariable('mesh2d', 'f4')  # 'f4' specifies the data type as float32
            mesh2d.setncattr('cf_role', "mesh_topology")
            mesh2d.setncattr('topology_dimension', 2)

            discharge = nc_file.createVariable('discharge', 'f4', ('time', 'face'))
            discharge.setncattr('standard_name', 'discharge')
            discharge.setncattr('mesh', mesh2d.name)
            discharge.setncattr('location', 'face')

            discharge[:] = [[27, 76], 
                            [801, 802], 
                            [214, 588]]
                
            with mock.patch('netCDF4.Dataset') as mock_nc_dataset:
                mock_nc_dataset.return_value = nc_file               
                data = dfastmi.io.read_fm_map(filename="mock.nc", varname='discharge')
                assert numpy.array_equal(data, [214,588])

    def test_read_fm_map_instantiate_dataset_in_memory_get_indexed_double_var(self):
        with tempfile.NamedTemporaryFile(suffix='_map.nc') as temp_file:
            nc_file = netCDF4.Dataset(temp_file.name, mode='w', diskless=True)
            
            # Define dimensions
            nc_file.createDimension('time', 0)  # 3 time dimensions will be defined later (0=unlimited)
            nc_file.createDimension('face', 2)  # 2 faces

            # Create variables
            mesh2d = nc_file.createVariable('mesh2d', 'f4')  # 'f4' specifies the data type as float32
            mesh2d.setncattr('cf_role', "mesh_topology")
            mesh2d.setncattr('topology_dimension', 2)

            discharge = nc_file.createVariable('discharge', 'f4', ('time', 'face'))
            discharge.setncattr('standard_name', 'discharge')
            discharge.setncattr('mesh', mesh2d.name)
            discharge.setncattr('location', 'face')

            discharge[:] = [[27, 76], 
                            [801, 802], 
                            [214, 588]]
            
            with mock.patch('netCDF4.Dataset') as mock_nc_dataset:
                mock_nc_dataset.return_value = nc_file
                data = dfastmi.io.read_fm_map(filename="mock.nc", varname='discharge', ifld=2)
                assert numpy.array_equal(data, [27,76])                                   

    def test_read_fm_map_from_mocked_dataset_x_coordinates_of_faces_by_projection_x_coordinate(self):
        """
        Testing read_fm_map: x coordinates of the faces by projection_x_coordinate.
        """
        filename = "mocked_file_name.nc"
        varname = "x"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[0].standard_name = 'projection_x_coordinate'
            netCDF4Dataset.variables[0].return_value = mock_variable
            netCDF4Dataset.variables[0].__getitem__.return_value  = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = "projection_x_coordinate projection_y_coordinate"
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([801,802]))           
    
    def test_read_fm_map_from_mocked_dataset_x_coordinates_of_faces_by_longitude(self):
        """
        Testing read_fm_map: x coordinates of the faces by longitude.
        """
        filename = "mocked_file_name.nc"
        varname = "x"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[0].standard_name = 'longitude'
            netCDF4Dataset.variables[0].return_value = mock_variable
            netCDF4Dataset.variables[0].__getitem__.return_value  = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = "longitude latitude"
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([801,802]))   
    
    def test_read_fm_map_from_mocked_dataset_y_coordinates_of_faces_by_projection_y_coordinate(self):
        """
        Testing read_fm_map: y coordinates of the faces by projection_y_coordinate.
        """
        filename = "mocked_file_name.nc"
        varname = "y"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[1].standard_name = 'projection_y_coordinate'
            netCDF4Dataset.variables[1].return_value = mock_variable
            netCDF4Dataset.variables[1].__getitem__.return_value  = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = "projection_x_coordinate projection_y_coordinate"
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([801,802]))           
    
    def test_read_fm_map_from_mocked_dataset_y_coordinates_of_faces_by_latitude(self):
        """
        Testing read_fm_map: y coordinates of the faces by latitude.
        """
        filename = "mocked_file_name.nc"
        varname = "y"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_variable = mock.MagicMock(name="aVariable", spec=netCDF4.Variable)
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_variable]
            netCDF4Dataset.variables[1].standard_name = 'latitude'
            netCDF4Dataset.variables[1].return_value = mock_variable
            netCDF4Dataset.variables[1].__getitem__.return_value  = [801, 802]
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = True
            mock_variable.get_dims.return_value = [dim]
            mock_variable.getncattr.return_value = "longitude latitude"
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([801,802]))   
    
    def test_read_fm_map_from_mocked_dataset_mesh_connectivity_variable(self):
        """
        Testing read_fm_map: dataset mesh connectivity variable
        """
        filename = "mocked_file_name.nc"
        varname = "face_node_connectivity"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_mesh = mock.MagicMock(name="mesh2d", spec=netCDF4.Variable)
            mock_mesh.getncattr.return_value = "aVar"
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_mesh]
            
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = False
            mock_variable = mock.MagicMock(name="aVar", spec=netCDF4.Variable)            
            mock_variable.get_dims.return_value = [dim]
            mock_variable.__getitem__.return_value = numpy.ma.masked_array(data=[801,802])
            netCDF4Dataset.variables = {'aVar':mock_variable}
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([801,802]))   
    
    def test_read_fm_map_from_mocked_dataset_mesh_connectivity_variable_with_start_index_of_1(self):
        """
        Testing read_fm_map: dataset mesh connectivity variable with start index of 1
        """
        filename = "mocked_file_name.nc"
        varname = "face_node_connectivity"
        with mock.patch('netCDF4.Dataset') as netCDF4Dataset:
            netCDF4Dataset.return_value = netCDF4.Dataset
            mock_mesh = mock.MagicMock(name="mesh2d", spec=netCDF4.Variable)
            mock_mesh.getncattr.return_value = "aVar"
            netCDF4Dataset.get_variables_by_attributes.return_value = [mock_mesh]
            
            dim = mock.MagicMock(name="aDimension", spec=netCDF4.Dimension)
            dim.isunlimited.return_value = False
            mock_variable = mock.MagicMock(name="aVar", spec=netCDF4.Variable)            
            mock_variable.get_dims.return_value = [dim]
            mock_variable.ncattrs.return_value = ['start_index']
            mock_variable.getncattr.return_value = 1
            mock_variable.__getitem__.return_value = numpy.ma.masked_array(data=[801,802])
            netCDF4Dataset.variables = {'aVar':mock_variable}
            data = dfastmi.io.read_fm_map(filename, varname)                
            assert numpy.array_equal(data, numpy.array([800,801]))

class Test_data_access_read_fm_map():
    def test_read_fm_map_from_example_file_x_coordinates_of_faces(self):
        """
        Testing read_fm_map: x coordinates of the faces.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "x"
        #location = "face"
        datac = dfastmi.io.read_fm_map(filename, varname)
        dataref = 41.24417604888325
        assert datac[1] == dataref

    def test_read_fm_map_02(self):
        """
        Testing read_fm_map: y coordinates of the edges.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "y"
        location = "edge"
        datac = dfastmi.io.read_fm_map(filename, varname, location)
        dataref = 7059.853000358055
        assert datac[1] == dataref

    def test_read_fm_map_03(self):
        """
        Testing read_fm_map: face node connectivity.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "face_node_connectivity"
        datac = dfastmi.io.read_fm_map(filename, varname)
        dataref = 2352
        assert datac[-1][1] == dataref

    def test_read_fm_map_04(self):
        """
        Testing read_fm_map: variable by standard name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "sea_floor_depth_below_sea_surface"
        datac = dfastmi.io.read_fm_map(filename, varname)
        dataref = 3.894498393076889
        assert datac[1] == dataref

    def test_read_fm_map_05(self):
        """
        Testing read_fm_map: variable by long name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "Water level"
        datac = dfastmi.io.read_fm_map(filename, varname)
        dataref = 3.8871328177527262
        assert datac[1] == dataref

    def test_read_fm_map_06(self):
        """
        Testing read_fm_map: variable by long name.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "water level"
        with pytest.raises(Exception) as cm:
            datac = dfastmi.io.read_fm_map(filename, varname)
        assert str(cm.value) == 'Expected one variable for "water level", but obtained 0.'

    def test_read_fm_map_07(self):
        """
        Testing read_fm_map: multiple mesh2dids.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        varname = "water level"
        with pytest.raises(Exception) as cm:
            datac = dfastmi.io.read_fm_map(filename, varname)
        assert str(cm.value) == 'Expected one variable for "water level", but obtained 0.'
        
class Test_get_mesh_and_facedim_names():
    def test_get_mesh_and_facedim_names_01(self):
        """
        Testing get_mesh_and_facedim_names.
        """
        filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        name_and_dim = dfastmi.io.get_mesh_and_facedim_names(filename)
        assert name_and_dim == ("mesh2d", "mesh2d_nFaces")

class Test_copy_ugrid():
    def test_copy_ugrid_01(self):
        """
        Testing copy_ugrid (depends on copy_var).
        """
        src_filename = "tests/files/e02_f001_c011_simplechannel_map.nc"
        dst_filename = "test.nc"
        meshname, facedim = dfastmi.io.get_mesh_and_facedim_names(src_filename)
        dfastmi.io.copy_ugrid(src_filename, meshname, dst_filename)
        #
        varname = "face_node_connectivity"
        datac = dfastmi.io.read_fm_map(dst_filename, varname)
        dataref = 2352
        assert datac[-1][1] == dataref


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
                dfastmi.io.copy_var(src, "mesh2d_s1", dst)
        #
        varname = "sea_surface_height"
        datac = dfastmi.io.read_fm_map(dst_filename, varname)
        dataref = 3.8871328177527262
        assert datac[1] == dataref

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
        dfastmi.io.ugrid_add(dst_filename, varname, ldata, meshname, facedim, long_name)
        #
        datac = dfastmi.io.read_fm_map(dst_filename, long_name)
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
        dfastmi.io.ugrid_add(dst_filename, varname, ldata, meshname, facedim, long_name, units)
        rootgrp = netCDF4.Dataset(dst_filename)        
        var = rootgrp.get_variables_by_attributes(
                long_name=long_name, mesh=meshname, location="face"
            )
        #
        assert var[0].units == units

class Test_read_waqua_xyz():
    def test_read_waqua_xyz_01(self):
        """
        Read WAQUA xyz file default column 2.
        """
        filename = "tests/files/read_waqua_xyz_test.xyc"
        data = dfastmi.io.read_waqua_xyz(filename)
        datar = numpy.array([3., 6., 9., 12.])
        print("data reference: ", datar)
        print("data read     : ", data)
        assert numpy.shape(data) == (4,)
        assert (data == datar).all() == True

    def test_read_waqua_xyz_02(self):
        """
        Read WAQUA xyz file columns 1 and 2.
        """
        filename = "tests/files/read_waqua_xyz_test.xyc"
        col = (1,2)
        data = dfastmi.io.read_waqua_xyz(filename, col)
        datar = numpy.array([[ 2., 3.], [ 5., 6.], [ 8., 9.], [11., 12.]])
        print("data reference: ", datar)
        print("data read     : ", data)
        assert numpy.shape(data) == (4,2)
        assert (data == datar).all() == True

class Test_write_simona_box():
    def test_write_simona_box_01(self):
        """
        Write small SIMONA BOX file.
        """
        filename = "test.box"
        data = numpy.array([[1, 2, 3],[4, 5, 6],[7, 8, 9]])
        firstm = 0
        firstn = 0
        dfastmi.io.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['      BOX MNMN=(   1,    1,    3,    3), VARIABLE_VAL=',
                         '          1.000       2.000       3.000',
                         '          4.000       5.000       6.000',
                         '          7.000       8.000       9.000']
        assert all_lines == all_lines_ref

    def test_write_simona_box_02(self):
        """
        Write small SIMONA BOX file with offset.
        """
        filename = "test.box"
        data = numpy.array([[0, 0, 0, 0, 0], [0, 0, 1, 2, 3],[0, 0, 4, 5, 6],[0, 0, 7, 8, 9]])
        firstm = 1
        firstn = 2
        dfastmi.io.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['      BOX MNMN=(   2,    3,    4,    5), VARIABLE_VAL=',
                         '          1.000       2.000       3.000',
                         '          4.000       5.000       6.000',
                         '          7.000       8.000       9.000']
        assert all_lines == all_lines_ref

    def test_write_simona_box_03(self):
        """
        Write large SIMONA BOX file.
        """
        filename = "test.box"
        data = numpy.zeros((15,15))
        firstm = 0
        firstn = 0
        dfastmi.io.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['      BOX MNMN=(   1,    1,   15,   10), VARIABLE_VAL=']
        all_lines_ref.extend(['          0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000']*15)
        all_lines_ref.extend(['      BOX MNMN=(   1,   11,   15,   15), VARIABLE_VAL='])
        all_lines_ref.extend(['          0.000       0.000       0.000       0.000       0.000']*15)
        self.maxDiff = None
        assert all_lines == all_lines_ref

class Test_collect_int_values1():
    def test_collect_int_values1_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        globalKey = "KEY"
        globalVal = "YES"
        branches = ["branch1","branch2"]
        nreaches = [2, 3]
        config[generalGroup][globalKey] = globalVal
        with pytest.raises(Exception) as cm:
            dfastmi.io.collect_int_values1(config, branches, nreaches, globalKey)
        assert str(cm.value) == 'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(globalKey, 1, "branch1", globalVal, 1)
    
    def test_collect_int_values1_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        globalKey = "KEY"
        globalVal = "1"
        branches = ["branch1","branch2"]
        nreaches = [2, 3]
        config[generalGroup][globalKey] = globalVal
        intValues = dfastmi.io.collect_int_values1(config, branches, nreaches, globalKey)
        assert intValues == [[1,1],[1,1,1]]

    def test_collect_int_values1_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        key = "KEY"
        branches = ["branch1","branch2"]
        nreaches = [2, 3]
        intValues = dfastmi.io.collect_int_values1(config, branches, nreaches, key, 1)
        assert intValues == [[1,1],[1,1,1]]

    def test_collect_int_values1_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        key = "KEY"
        branch1 = "branch1"
        branch2 = "branch2"
        branches = [branch1, branch2]
        nreaches = [2, 3]
        config.add_section(branch1)
        config[branch1][key + "1"] = "2"
        config[branch1][key + "2"] = "3"

        config.add_section(branch2)
        config[branch2][key + "1"] = "4"
        config[branch2][key + "2"] = "5"
        config[branch2][key + "3"] = "6"

        intValues = dfastmi.io.collect_int_values1(config, branches, nreaches, key)
        assert intValues == [[2,3],[4,5,6]]

class Test_config_get_bool():
    def test_config_get_bool_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_bool(config, myGroup, myKey) == True

    def test_config_get_bool_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_bool(config, myGroup, myKey)
        assert str(cm.value) == 'No boolean value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)

    def test_config_get_bool_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        assert dfastmi.io.config_get_bool(config, myGroup, myKey, default=True) == True

class Test_config_get_int():
    def test_config_get_int_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "1"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_int(config, myGroup, myKey) == 1

    def test_config_get_int_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_int(config, myGroup, myKey)
        assert str(cm.value) == 'No integer value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)

    def test_config_get_int_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "-1"
        config[myGroup][myKey] = myVal
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_int(config, myGroup, myKey, positive=True)
        assert str(cm.value) == 'Value for "{}" in block "{}" must be positive, not {}.'.format(
                    myKey, myGroup, myVal
                )
    
    def test_config_get_int_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0"
        config[myGroup][myKey] = myVal
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_int(config, myGroup, myKey, positive=True)
        assert str(cm.value) == 'Value for "{}" in block "{}" must be positive, not {}.'.format(
                    myKey, myGroup, myVal
                )
        
    def test_config_get_int_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"        
        assert dfastmi.io.config_get_int(config, myGroup, myKey, default=1) == 1

class Test_config_get_float():
    def test_config_get_float_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "1"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_float(config, myGroup, myKey) == 1

    def test_config_get_float_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_float(config, myGroup, myKey)
        assert str(cm.value) == 'No floating point value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)

    def test_config_get_float_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "-0.5"
        config[myGroup][myKey] = myVal
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_float(config, myGroup, myKey, positive=True)
        assert str(cm.value) == 'Value for "{}" in block "{}" must be positive, not {}.'.format(
                    myKey, myGroup, myVal
                )
    
    def test_config_get_float_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0"
        config[myGroup][myKey] = myVal           
        assert dfastmi.io.config_get_float(config, myGroup, myKey, positive=True) == 0.0
        
    def test_config_get_float_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"        
        assert dfastmi.io.config_get_float(config, myGroup, myKey, default=0.5) == 0.5        

class Test_config_get_str():
    def test_config_get_str_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_str(config, myGroup, myKey) == "YES"

    def test_config_get_str_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_str(config, myGroup, myKey)
        assert str(cm.value) == 'No value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)
 
    def test_config_get_str_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        assert dfastmi.io.config_get_str(config, myGroup, myKey, default="YES") == "YES"

class Test_config_get_range():
    def test_config_get_range_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "[0.0:10.0]"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_range(config, myGroup, myKey) == (0.0,10.0)
    
    def test_config_get_range_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "[10.0:0.0]"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_range(config, myGroup, myKey) == (0.0,10.0)

    @pytest.mark.skip(reason="Other exception is thrown")
    def test_config_get_range_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        #myVal = "0.0:10.0"
        myVal = "0.0-10.0"
        config[myGroup][myKey] = myVal #even on not setting this value we expect the exception
        with pytest.raises(Exception) as cm:
            dfastmi.io.config_get_range(config, myGroup, myKey)
        assert range(cm.value) == 'Invalid range specification "{}" for required keyword "{}" in block "{}".'.format("", myKey, myGroup)
 
    def test_config_get_range_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        assert dfastmi.io.config_get_range(config, myGroup, myKey, default="YES") == "YES"        
    
    def test_config_get_range_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0.0:10.0"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_range(config, myGroup, myKey) == (0.0,10.0)
    
    def test_config_get_range_06(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "10.0:0.0"
        config[myGroup][myKey] = myVal
        assert dfastmi.io.config_get_range(config, myGroup, myKey) == (0.0,10.0)

class Test_get_progloc():
    def test_get_progloc_01(self):
        """
        Get the location of the program.
        """
        assert dfastmi.io.get_progloc() != ""

class Test_get_xykm():
    def test_get_xykm_01(self):
        """
        read .xyc file with val as xykm
        """
        line = dfastmi.io.get_xykm("tests/files/read_xyc_test.xyc")

        assert line.wkt == 'LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)'

class Test_read_xyc():
    @pytest.fixture
    def setup_data(self):
        with mock.patch('os.path.splitext') as mock_splitext:
            mock_splitext.return_value = ("c:\\", ".XYC")
            yield self

    def test_read_xyc_read_waqua_xyz_test_xyc_file(self):
        """
        Read WAQUA xyz file columns 2 and 3 = X & Y, column 1 is chainage. 
        """
        line = dfastmi.io.read_xyc("tests/files/read_waqua_xyz_test.xyc", 3, ",", True)

        assert line.wkt == 'LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)'
        
    def test_read_xyc_with_header_with_chainages_custom_separator(self, setup_data):
        """
        read .xyc file with chainage
        With custom header and seperator.
        """
        data_string = '''\
                        "A", "B", "C"
                        1, 2, 3
                        4, 5, 6
                        7, 8, 9
                        10, 11, 12
                        '''
        string_io = io.StringIO(data_string)
        
        line = dfastmi.io.read_xyc(string_io, 3, ",", True)        
        assert line.wkt == 'LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)'

    def test_read_xyc_with_header_without_chainages_custom_separator(self, setup_data):
        """
        read .xyc file without chainage (X,Y only)
        With custom header and seperator.
        """
        data_string = '''\
                        "A", "B"
                        2, 3
                        5, 6
                        8, 9
                        11, 12
                        '''
        string_io = io.StringIO(data_string)
        
        line = dfastmi.io.read_xyc(string_io, 2, ",", True)
        assert line.wkt == 'LINESTRING (2 3, 5 6, 8 9, 11 12)'

    def test_read_xyc_with_header_with_chainages_no_custom_separator(self, setup_data):
        """
        read .xyc file with chainage
        With custom header and seperator.
        """
        data_string = '''\
                        "A" "B" "C"
                        1 2 3
                        4 5 6
                        7 8 9
                        10 11 12
                        '''
        string_io = io.StringIO(data_string)
        
        line = dfastmi.io.read_xyc(string_io, 3, hasHeader=True)        
        assert line.wkt == 'LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)'

    def test_read_xyc_with_header_without_chainages_no_custom_separator(self, setup_data):
        """
        read .xyc file without chainage (X,Y only)
        With custom header and seperator.
        """
        data_string = '''\
                        "A" "B"
                        2 3
                        5 6
                        8 9
                        11 12
                        '''
        string_io = io.StringIO(data_string)
        
        line = dfastmi.io.read_xyc(string_io, 2, hasHeader=True)
        assert line.wkt == 'LINESTRING (2 3, 5 6, 8 9, 11 12)'
    
    def test_read_xyc_no_header_with_chainages_no_custom_separator(self, setup_data):
        """
        read .xyc file with chainage
        No header and no custom seperator.
        """
        data_string = '''\
                        1 2 3
                        4 5 6
                        7 8 9
                        10 11 12
                        '''
        string_io = io.StringIO(data_string)
        line = dfastmi.io.read_xyc(string_io, 3)

        assert line.wkt == 'LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)'

    def test_read_xyc_no_header_without_chainages_no_custom_separator(self, setup_data):
        """
        read .xyc file without chainage
        No header and no custom seperator.
        """
        data_string = '''\
                        2 3
                        5 6
                        8 9
                        11 12
                        '''
        string_io = io.StringIO(data_string)
        line = dfastmi.io.read_xyc(string_io, 2)
        
        assert line.wkt == 'LINESTRING (2 3, 5 6, 8 9, 11 12)'
    
    def test_read_xyc_no_header_with_chainages_custom_separator(self, setup_data):
        """
        read .xyc file with chainage
        No header and custom seperator.
        """
        data_string = '''\
                        1;2;3
                        4;5;6
                        7;8;9
                        10;11;12
                        '''
        string_io = io.StringIO(data_string)
        line = dfastmi.io.read_xyc(string_io, 3, ";")

        assert line.wkt == 'LINESTRING Z (2 3 1, 5 6 4, 8 9 7, 11 12 10)'

    def test_read_xyc_no_header_without_chainages_custom_separator(self, setup_data):
        """
        read .xyc file without chainage (X,Y only)
        No header and custom seperator.
        """
        data_string = '''\
                        2;3
                        5;6
                        8;9
                        11;12
                        '''
        string_io = io.StringIO(data_string)
        line = dfastmi.io.read_xyc(string_io, 2, ";")
        assert line.wkt == 'LINESTRING (2 3, 5 6, 8 9, 11 12)'    

    def test_read_xyc_read_kml_file(self):
        """
        read .kml file with val
        """
        line = dfastmi.io.read_xyc("tests/files/cta_rail_lines.kml")
        assert line.wkt == 'MULTILINESTRING Z ((-87.77678526964958 41.8708863930319 0, -87.77826234150609 41.87097820122218 0, -87.78251583439344 41.87130129991005 0, -87.78418294588424 41.87145055520308 0, -87.7872369165933 41.8717239119163 0, -87.79160214925886 41.87210797280065 0))'
    
    def test_read_xyc_read_shp_file(self):
        """
        read .shp file with val 
        """
        line = dfastmi.io.read_xyc("tests/files/Twentekanaal_nieuw/Twentekanaal.shp")
        assert line.wkt == 'MULTIPOLYGON Z (((243077.031 473933.145 10.156, 243138.949 473975.542 10.156, 243170.516 473996.96 10.156, 243197.123 474014.916 10.156, 243203.828 474005.251 10.156, 243165.927 473979.29 10.156, 243147.099 473966.578 10.156, 243083.538 473923.611 10.156, 243077.031 473933.145 10.156)), ((243107.38 473885.244 16.053, 243108.29 473885.717 16.053, 243112.823 473887.192 16.053, 243120.986 473890.36 16.053, 243125.769 473892.765 16.053, 243131.894 473896.537 16.053, 243144.475 473905.211 16.053, 243160.992 473916.497 16.053, 243178.45 473928.322 16.053, 243189.182 473935.731 16.053, 243220.605 473956.91 16.053, 243230.196 473963.633 16.053, 243238.403 473951.601 16.053, 243215.07 473935.239 16.053, 243182.215 473913.278 16.053, 243178.04 473910.293 16.053, 243169.65 473904.586 16.053, 243161.837 473899.185 16.053, 243153.834 473894.228 16.053, 243141.354 473885.655 16.053, 243135.838 473882.014 16.053, 243132.378 473879.354 16.053, 243129.299 473876.375 16.053, 243126.754 473873.044 16.053, 243123.83 473869.642 16.053, 243122.105 473867.439 16.053, 243120.282 473866.17 16.053, 243107.38 473885.244 16.053)), ((243197.289 474015.028 16.053, 243201.48 474017.857 16.053, 243221.937 474035.934 16.053, 243250.448 474061.025 16.053, 243269.143 474077.557 16.053, 243270.462 474079.526 16.053, 243271.094 474081.829 16.053, 243289.796 474094.538 16.053, 243313.869 474110.934 16.053, 243343.222 474130.813 16.053, 243368.964 474148.294 16.053, 243397.283 474167.525 16.053, 243425.464 474186.741 16.053, 243456.814 474208.082 16.053, 243453.933 474212.498 16.053, 243460.194 474216.679 16.053, 243471.443 474224.499 16.053, 243471.594 474225.36 16.051, 243472.14 474226.032 16.051, 243484.617 474234.897 16.051, 243490.18 474238.705 16.051, 243495.963 474242.105 16.051, 243498.339 474243.56 16.051, 243499.845 474244.39 16.051, 243502.05 474245.516 16.051, 243506.087 474247.659 16.053, 243548.542 474276.519 16.053, 243589.338 474304.183 16.053, 243621.84 474325.754 16.053, 243643.517 474339.378 16.053, 243670.285 474356.004 16.053, 243700.387 474374.475 16.053, 243729.545 474391.954 16.053, 243753.001 474405.509 16.053, 243775.539 474418.257 16.053, 243802.28 474432.734 16.053, 243832.212 474448.244 16.053, 243858.198 474461.038 16.053, 243886.124 474474.32 16.053, 243909.357 474485.036 16.053, 243937.815 474497.611 16.053, 243961.348 474507.375 16.053, 243987.781 474518.064 16.053, 244007.874 474525.867 16.053, 244035.122 474535.878 16.053, 244060.568 474544.923 16.053, 244100.901 474558.383 16.053, 244111.129 474561.584 16.053, 244159.218 474575.937 16.053, 244170.849 474583.362 16.053, 244177.413 474584.811 16.053, 244198.448 474589.195 16.053, 244213.652 474592.426 16.053, 244215.383 474592.798 16.053, 244306.881 474611.593 16.053, 244367.846 474624.146 16.053, 244373.067 474630.474 16.053, 244375.917 474633.903 16.053, 244380.477 474634.489 16.053, 244465.807 474645.156 16.053, 244493.638 474648.667 16.053, 244509.443 474639.198 16.053, 244543.809 474637.059 16.053, 244556.781 474637.433 16.053, 244563.714 474637.437 16.053, 244566.326 474637.571 16.053, 244568.544 474637.199 16.053, 244581.613 474637.697 16.053, 244583.6 474637.992 16.053, 244589.52 474638.55 16.053, 244592.81 474639.138 16.053, 244616.206 474643.344 16.053, 244627.832 474645.286 16.053, 244633.603 474645.704 16.053, 244645.32 474645.553 16.053, 244693.639 474646.238 16.053, 244693.64 474646.437 16.053, 244693.633 474648.308 16.053, 244694.955 474648.301 16.053, 244695.016 474646.456 16.053, 244695.022 474646.258 16.053, 244728.145 474646.728 16.053, 244784.944 474647.311 16.053, 244839.07 474647.928 16.053, 244898.589 474648.74 16.053, 244962.443 474649.544 16.053, 245014.842 474650.254 16.053, 245060.13 474650.85 16.053, 245114.386 474651.589 16.053, 245161.095 474652.214 16.053, 245201.522 474652.841 16.053, 245251.829 474653.444 16.053, 245287.611 474653.815 16.053, 245287.251 474655.352 16.053, 245288.187 474655.363 16.053, 245288.553 474653.825 16.053, 245296.33 474653.906 16.053, 245296.498 474657.745 16.053, 245297.29 474657.541 16.053, 245298.561 474657.53 16.053, 245299.806 474657.581 16.053, 245301.104 474657.894 16.053, 245301.192 474654.001 16.053, 245338.474 474654.566 16.053, 245359.674 474654.85 16.053, 245409.543 474655.424 16.053, 245500.842 474656.858 16.053, 245541.167 474657.548 16.053, 245584.357 474658.013 16.053, 245616.26 474658.468 16.053, 245651.838 474658.849 16.053, 245704.448 474659.579 16.053, 245743.674 474660.198 16.053, 245817.147 474661.187 16.053, 245873.941 474661.972 16.053, 245920.752 474662.637 16.053, 245961.035 474663.163 16.053, 245997.796 474658.494 16.053, 246043.164 474659.066 16.053, 246084.147 474659.54 16.053, 246093.416 474660.473 16.053, 246120.583 474663.156 16.053, 246136.584 474662.896 16.053, 246172.287 474661.99 16.053, 246214.753 474661.11 16.053, 246251.118 474659.5 16.053, 246283.59 474658.041 16.053, 246314.711 474656.678 16.053, 246359.25 474654.896 16.053, 246415.984 474652.429 16.053, 246468.786 474650.286 16.053, 246503.423 474648.96 16.053, 246538.291 474647.415 16.053, 246542.19 474647.28 16.053, 246543.656 474647.442 16.055, 246545.643 474648.317 16.055, 246547.704 474648.467 16.055, 246550.523 474648.12 16.055, 246555.182 474647.74 16.055, 246558.425 474647.64 16.055, 246561.517 474647.313 16.055, 246562.975 474646.647 16.055, 246563.743 474646.214 16.053, 246575.209 474645.92 16.053, 246604.885 474644.741 16.053, 246650.285 474642.758 16.053, 246709.385 474640.397 16.053, 246745.351 474638.988 16.053, 246779.974 474637.402 16.053, 246819.763 474635.618 16.053, 246832.107 474635.168 16.053, 246879.066 474633.289 16.053, 246956.697 474629.85 16.053, 247050.647 474626.008 16.053, 247107.128 474623.55 16.053, 247159.551 474621.685 16.053, 247223.793 474618.711 16.053, 247306.147 474615.314 16.053, 247382.19 474612.139 16.053, 247429.879 474610.272 16.053, 247476.923 474608.308 16.053, 247516.49 474606.482 16.053, 247517.169 474606.499 16.054, 247517.588 474606.784 16.054, 247517.832 474606.989 16.054, 247518.31 474607.356 16.054, 247518.894 474607.656 16.054, 247523.266 474607.646 16.054, 247532.541 474607.121 16.054, 247532.868 474606.994 16.054, 247533.169 474606.747 16.054, 247533.416 474606.093 16.054, 247533.654 474605.945 16.054, 247534.494 474605.815 16.053, 247585.229 474603.689 16.053, 247664.274 474600.218 16.053, 247741.766 474596.886 16.053, 247814.77 474593.967 16.053, 247886.218 474590.893 16.053, 247937.11 474588.775 16.053, 247995.996 474586.499 16.053, 248036.365 474584.768 16.053, 248101.778 474581.996 16.053, 248166.851 474579.28 16.053, 248229.384 474576.508 16.053, 248294.292 474573.753 16.053, 248321.432 474572.557 16.053, 248360.526 474570.872 16.058, 248376.515 474570.33 16.058, 248466.33 474566.66 16.058, 248551.239 474562.942 16.058, 248591.408 474561.306 16.058, 248660.491 474558.275 16.058, 248733.962 474554.165 16.058, 248756.775 474552.715 16.058, 248775.876 474551.271 16.058, 248793.347 474550.093 16.058, 248805.871 474549.08 16.058, 248817.408 474548.026 16.058, 248828.018 474547.002 16.058, 248885.919 474542.038 16.058, 248908.787 474539.902 16.058, 248944.632 474536.307 16.058, 248971.159 474533.441 16.058, 248980.502 474532.31 16.058, 248981.51 474532.47 16.058, 248981.84 474536.835 16.058, 248972.042 474538.07 16.058, 248972.945 474545.353 16.058, 248979.186 474544.428 16.058, 248979.212 474544.831 16.058, 248970.337 474546.254 16.058, 248967.067 474546.671 16.058, 248967.437 474550.39 16.058, 248977.336 474549.206 16.058, 248976.864 474556.258 16.058, 248972.192 474556.858 16.058, 248960.45 474561.306 16.058, 248934.273 474570.021 16.058, 248904.294 474580.439 16.058, 248912.217 474606.372 16.058, 248916.33 474619.471 16.058, 248917.218 474620.653 16.058, 248918.425 474621.634 16.058, 248919.964 474622.165 16.058, 248921.584 474622.311 16.058, 248923.451 474622.039 16.058, 248925.077 474621.476 16.058, 248954.477 474612.867 16.058, 248983.294 474604.286 16.058, 249023.623 474592.285 16.058, 249051.142 474583.748 16.058, 249044.209 474560.223 16.058, 249041.377 474550.443 16.058, 248996.664 474555.86 16.058, 248998.219 474539.496 16.058, 248998.692 474537.841 16.058, 248999.618 474536.548 16.058, 249000.279 474536.08 16.058, 249000.878 474535.855 16.058, 249000.734 474534.334 16.058, 249001.135 474534.028 16.058, 249000.582 474530.154 16.058, 249031.062 474526.31 16.058, 249057.764 474523.015 16.058, 249058.222 474522.945 16.059, 249059.629 474522.929 16.059, 249060.171 474523.018 16.059, 249060.812 474523.032 16.059, 249061.221 474522.912 16.059, 249061.666 474522.612 16.059, 249061.977 474522.528 16.058, 249080.127 474520.199 16.058, 249121.759 474514.433 16.058, 249138.946 474511.947 16.058, 249143.47 474511.179 16.058, 249178.357 474501.943 16.058, 249192.624 474497.976 16.058, 249196.699 474497.829 16.058, 249239.6 474490.423 16.058, 249277.767 474483.785 16.058, 249307.109 474492.018 16.058, 249308.136 474491.921 16.176, 249358.471 474483.701 16.176, 249415.107 474474.461 16.176, 249482.208 474463.507 16.176, 249541.609 474453.928 16.176, 249602.916 474443.868 16.176, 249629.263 474439.633 16.176, 249640.341 474438.798 16.176, 249651.976 474436.899 16.176, 249705.405 474428.042 16.176, 249764.194 474418.54 16.176, 249901.468 474396.122 16.176, 249949.195 474388.316 16.176, 249998.205 474380.287 16.176, 250000 474380 16.182, 250038.076 474373.907 16.308, 250150.396 474355.565 16.308, 250233.212 474342.067 16.308, 250314.488 474328.717 16.308, 250345.005 474323.74 16.308, 250384.31 474317.498 16.308, 250384.343 474317.41 16.308, 250385.072 474317.274 16.308, 250386.096 474317.047 16.308, 250386.703 474316.605 16.308, 250387.516 474316.319 16.308, 250389.092 474316.078 16.308, 250391.433 474316.114 16.308, 250393.618 474316.281 16.308, 250395.071 474316.724 16.308, 250396.391 474317.426 16.308, 250396.666 474317.797 16.308, 250396.944 474318.784 16.308, 250398.214 474320.053 16.308, 250402.195 474323.803 16.308, 250404.064 474325.925 16.308, 250410.022 474332.315 16.308, 250416.207 474338.823 16.308, 250424.86 474348.579 16.308, 250433.464 474358.201 16.308, 250436.699 474361.386 16.308, 250437.581 474362.111 16.308, 250441.963 474366.801 16.308, 250448.457 474373.908 16.308, 250453.009 474378.582 16.308, 250456.076 474376.066 16.308, 250521.71 474447.633 16.308, 250551.004 474479.362 16.308, 250568.064 474497.985 16.308, 250593.225 474475.434 16.308, 250560.187 474439.203 16.308, 250508.873 474383.033 16.308, 250488.549 474360.87 16.308, 250485.487 474357.648 16.308, 250484.922 474358.161 16.308, 250481.237 474354.039 16.308, 250482.104 474353.203 16.308, 250480.947 474351.139 16.308, 250478.355 474348.151 16.308, 250468.35 474337.899 16.308, 250464.49 474334.068 16.308, 250462.71 474331.188 16.308, 250460.719 474327.197 16.308, 250459.72 474323.949 16.308, 250458.892 474321.31 16.308, 250458.325 474316.307 16.308, 250458.69 474313.909 16.308, 250459.12 474312.077 16.308, 250459.958 474309.812 16.308, 250460.931 474308.252 16.308, 250462.989 474306.904 16.308, 250464.405 474306.156 16.308, 250466.873 474305.725 16.308, 250470.02 474304.913 16.308, 250472.474 474303.705 16.308, 250475.002 474302.938 16.308, 250479.027 474302.299 16.308, 250481.768 474301.62 16.308, 250484.464 474300.806 16.308, 250491.047 474299.739 16.308, 250497.517 474298.989 16.308, 250502.308 474298.367 16.308, 250507.78 474297.701 16.308, 250513.421 474296.682 16.308, 250518.193 474295.65 16.308, 250521.207 474295.092 16.308, 250531.813 474293.53 16.308, 250541.167 474291.59 16.308, 250542.826 474291.642 16.308, 250543.364 474292.104 16.308, 250545.531 474292.086 16.308, 250547.818 474291.459 16.308, 250548.666 474290.484 16.308, 250549.337 474290.232 16.308, 250550.908 474289.944 16.308, 250556.931 474288.887 16.308, 250564.852 474287.887 16.308, 250573.012 474286.851 16.308, 250574.264 474286.683 16.308, 250574.312 474286.186 16.308, 250602.409 474281.566 16.308, 250632.546 474276.751 16.308, 250632.816 474277.223 16.308, 250656.116 474273.446 16.308, 250667.643 474271.54 16.308, 250669.182 474271.172 16.308, 250678.701 474269.956 16.308, 250683.049 474269.667 16.308, 250687.343 474269.039 16.308, 250691.533 474268.168 16.308, 250695.049 474267.127 16.308, 250697.912 474266.397 16.308, 250699.55 474265.636 16.308, 250709.165 474258.002 16.308, 250709.293 474257.679 16.308, 250720.111 474249.505 16.308, 250730.225 474247.809 16.308, 250772.667 474240.579 16.308, 250789.303 474246.455 16.308, 250799.302 474249.889 16.308, 250812.658 474247.946 16.308, 250813.598 474251.401 16.308, 250799.769 474277.942 16.308, 250788.856 474299.154 16.308, 250797.499 474303.567 16.308, 250809.445 474280.65 16.308, 250821.294 474257.798 16.308, 250834.115 474244.435 16.308, 250840.322 474243.38 16.308, 250845.267 474242.542 16.308, 250863.202 474239.624 16.308, 250864.529 474239.492 16.308, 250865.646 474239.797 16.308, 250867.544 474240.818 16.308, 250870.357 474241.982 16.308, 250873.445 474242.089 16.308, 250877.583 474241.512 16.308, 250879.319 474240.706 16.308, 250880.124 474240.004 16.308, 250881.375 474239.074 16.308, 250882.401 474238.244 16.308, 250883.418 474237.347 16.308, 250884.875 474236.573 16.308, 250887.083 474236.138 16.308, 250889.605 474235.81 16.308, 250892.637 474235.412 16.308, 250894.747 474234.44 16.308, 250896.705 474233.832 16.308, 250899.199 474233.375 16.308, 250901.093 474233.432 16.308, 250902.263 474234.037 16.308, 250902.708 474235.341 16.308, 250903.049 474236.182 16.308, 250903.465 474237.197 16.308, 250903.882 474237.885 16.308, 250904.819 474238.041 16.308, 250906.116 474237.947 16.308, 250907.196 474237.548 16.308, 250908.248 474237.179 16.308, 250910.746 474237.084 16.308, 250912.428 474237.228 16.308, 250913.67 474236.973 16.308, 250915.197 474236.137 16.308, 250916.958 474234.522 16.308, 250917.745 474232.941 16.308, 250917.759 474232.203 16.308, 250918.504 474231.636 16.308, 250919.127 474231.414 16.308, 250919.834 474230.845 16.308, 250909.429 474230.859 16.308, 250909.429 474230.659 16.308, 250919.834 474230.645 16.308, 250954.983 474225.024 16.308, 251023.549 474214.322 16.308, 251042.341 474211.264 16.308, 251081.217 474205.079 16.308, 251087.427 474204.091 16.308, 251092.59 474203.483 16.308, 251097.363 474203.26 16.308, 251102.047 474203.904 16.308, 251105.608 474204.985 16.308, 251119.979 474209.967 16.308, 251134.024 474216.114 16.308, 251159.6 474226.6 16.308, 251182.763 474236.145 16.308, 251183.61 474236.478 16.308, 251188.273 474233.298 16.308, 251188.81 474233.254 16.308, 251205.025 474240.003 16.308, 251205.535 474240.221 16.308, 251293.459 474277.039 16.308, 251293.741 474276.423 16.308, 251307.24 474282.062 16.308, 251307.014 474282.588 16.308, 251357.482 474303.965 16.308, 251359.291 474299.777 16.308, 251366.615 474303.063 16.308, 251364.908 474307.052 16.308, 251401.831 474322.577 16.308, 251417.706 474284.673 16.308, 251380.882 474269.375 16.308, 251379.061 474273.36 16.308, 251372.33 474270.474 16.308, 251374.085 474266.366 16.308, 251327.567 474246.978 16.308, 251322.899 474245.092 16.308, 251319.618 474243.044 16.308, 251316.142 474240.352 16.308, 251313.759 474237.927 16.308, 251311.314 474234.531 16.308, 251309.773 474231.85 16.308, 251308.506 474229.124 16.308, 251304.234 474212.931 16.308, 251303.524 474208.604 16.308, 251303.138 474204.505 16.308, 251302.924 474199.33 16.308, 251303.282 474188.953 16.308, 251303.455 474187.988 16.308, 251306.048 474180.799 16.308, 251308.068 474177.343 16.308, 251310.139 474175.086 16.308, 251311.09 474174.425 16.308, 251310.846 474173.904 16.308, 251315.34 474170.047 16.308, 251318.682 474167.89 16.308, 251320.663 474167.071 16.308, 251337.997 474164.229 16.308, 251371.29 474158.791 16.308, 251405.091 474153.216 16.308, 251468.814 474142.748 16.308, 251506.027 474136.672 16.308, 251551.125 474129.189 16.308, 251573.918 474125.44 16.308, 251574.164 474126.388 16.308, 251574.302 474126.353 16.308, 251574.492 474126.304 16.308, 251574.957 474127.299 16.308, 251579.824 474126.478 16.308, 251579.726 474125.485 16.308, 251579.909 474125.455 16.308, 251580.029 474126.433 16.308, 251585.162 474125.58 16.308, 251585.115 474124.425 16.308, 251585.315 474124.384 16.308, 251585.43 474124.361 16.308, 251585.319 474123.448 16.308, 251609.708 474119.449 16.308, 251646.809 474113.24 16.308, 251679.587 474107.937 16.308, 251679.342 474106.656 16.308, 251679.305 474105.477 16.308, 251679.539 474103.957 16.308, 251680.262 474102.554 16.308, 251681.447 474101.49 16.308, 251682.755 474100.598 16.308, 251702.166 474088.911 16.308, 251713.754 474082.074 16.308, 251714.397 474081.979 16.308, 251714.839 474081.905 16.309, 251733.657 474078.721 16.356, 251733.719 474078.71 16.356, 251737.624 474078.103 16.17, 251735.729 474066.186 16.17, 251732.059 474066.798 16.356, 251715.679 474069.473 16.309, 251715.263 474069.543 16.308, 251713.243 474069.835 16.308, 251711.382 474070.206 16.308, 251710.122 474070.294 16.308, 251703.529 474070.554 16.308, 251680.538 474071.454 16.308, 251637.743 474072.974 16.308, 251624.166 474073.369 16.308, 251622.649 474073.261 16.308, 251620.878 474072.789 16.308, 251619.364 474072.011 16.308, 251617.969 474070.923 16.308, 251616.74 474069.298 16.308, 251616.243 474068.009 16.308, 251615.871 474066.169 16.308, 251615.724 474065.225 16.308, 251613.008 474058.705 16.308, 251614.503 474054.663 16.308, 251615.135 474052.948 16.308, 251618.469 474047.248 16.308, 251626.86 474043.347 16.308, 251637.006 474039.537 16.308, 251646.888 474036.443 16.308, 251655.398 474034.106 16.308, 251664.027 474032.118 16.308, 251677.889 474029.67 16.308, 251683.866 474028.843 16.308, 251687.833 474028.572 16.308, 251692.396 474028.389 16.308, 251699.723 474028.564 16.308, 251699.868 474028.953 16.308, 251701.748 474028.553 16.308, 251702.008 474027.904 16.308, 251702.52 474025.452 16.308, 251704.449 474024.974 16.308, 251703.997 474022.453 16.308, 251701.625 474022.898 16.308, 251701.531 474022.464 16.308, 251703.943 474022.028 16.308, 251703.512 474019.519 16.308, 251701.106 474019.991 16.308, 251701.037 474019.61 16.308, 251703.438 474019.089 16.308, 251703.047 474016.813 16.308, 251700.545 474017.131 16.308, 251700.266 474015.255 16.308, 251699.494 474014.03 16.308, 251699.076 474014.03 16.308, 251697.428 474014.57 16.308, 251692.35 474016.56 16.308, 251684.232 474019.228 16.308, 251678.707 474020.692 16.308, 251673.847 474021.495 16.308, 251663.998 474022.759 16.308, 251658.658 474023.823 16.308, 251648.007 474027.032 16.308, 251646.831 474027.065 16.308, 251645.337 474027.015 16.308, 251640.727 474028.368 16.308, 251632.112 474031.018 16.308, 251621.927 474035.143 16.308, 251612.61 474039.251 16.308, 251609.803 474040.437 16.308, 251604.354 474042.739 16.308, 251597.091 474045.982 16.308, 251593.884 474047.414 16.308, 251593.083 474046.544 16.308, 251592.159 474047.003 16.308, 251592.469 474048.334 16.308, 251578.348 474055.338 16.308, 251566.366 474060.929 16.308, 251556.053 474065.44 16.308, 251536.927 474072.764 16.308, 251524.852 474076.94 16.308, 251518.29 474078.973 16.308, 251512.489 474080.664 16.308, 251507.763 474081.679 16.308, 251500.706 474082.974 16.308, 251471.85 474087.664 16.308, 251451.051 474091.092 16.308, 251437.87 474093.353 16.308, 251435.881 474094.105 16.308, 251434.044 474094.497 16.308, 251428.839 474095.045 16.308, 251423.54 474095.603 16.308, 251422.035 474094.378 16.308, 251421.871 474094.424 16.308, 251417.723 474091.236 16.308, 251412.265 474085.866 16.308, 251386.863 474090.218 16.308, 251325.676 474100.314 16.308, 251275.905 474108.147 16.308, 251259.122 474110.667 16.308, 251250.515 474109.528 16.308, 251250.572 474109.845 16.308, 251248.308 474110.163 16.308, 251248.286 474109.725 16.308, 251246.52 474110.026 16.308, 251247.811 474116.987 16.308, 251226.515 474120.456 16.308, 251226.166 474120.52 16.308, 251197.877 474124.964 16.308, 251197.131 474120.087 16.308, 251163.013 474125.437 16.308, 251135.946 474129.822 16.308, 251116.634 474133.278 16.308, 251116.732 474133.989 16.308, 251106.768 474135.603 16.308, 251057.422 474143.793 16.308, 251008.84 474151.637 16.308, 250965.332 474158.889 16.308, 250920.138 474166.288 16.308, 250913.929 474167.245 16.308, 250913.722 474165.9 16.308, 250878.85 474171.786 16.308, 250785.503 474187.492 16.308, 250783.381 474189.117 16.308, 250783.616 474189.205 16.308, 250783.546 474189.392 16.308, 250782.613 474189.043 16.308, 250781.204 474190.151 16.308, 250781.391 474191.109 16.308, 250781.195 474191.147 16.308, 250781.126 474190.793 16.308, 250766.574 474202.042 16.308, 250729.05 474208.476 16.308, 250717.451 474210.453 16.308, 250697.92 474204.5 16.308, 250688.469 474201.563 16.308, 250673.75 474204.129 16.308, 250643.74 474209.118 16.308, 250620.401 474213.023 16.308, 250619.867 474213.882 16.308, 250616.688 474214.413 16.308, 250615.833 474213.698 16.308, 250597.504 474216.748 16.308, 250560.303 474222.933 16.308, 250525.951 474228.795 16.308, 250526.156 474229.193 16.308, 250525.644 474229.309 16.308, 250525.433 474228.881 16.308, 250521.859 474229.473 16.308, 250521.789 474229.958 16.308, 250521.293 474230.025 16.308, 250521.375 474229.492 16.308, 250504.986 474232.235 16.308, 250454.654 474240.633 16.308, 250407.075 474248.481 16.308, 250362.189 474255.861 16.308, 250345.945 474258.534 16.308, 250345.702 474258.322 16.308, 250344.844 474258.227 16.308, 250341.461 474258.235 16.308, 250327.779 474260.263 16.308, 250307.198 474263.404 16.308, 250295.253 474265.468 16.308, 250296.149 474271.09 16.308, 250285.95 474272.783 16.308, 250255.047 474277.848 16.308, 250236.211 474281.095 16.308, 250235.677 474277.756 16.308, 250220.086 474280.362 16.308, 250193.866 474284.586 16.308, 250192.674 474282.223 16.308, 250185.361 474283.502 16.308, 250186.478 474289.614 16.308, 250186.119 474290.066 16.308, 250163.209 474294.033 16.308, 250162.677 474293.626 16.308, 250161.928 474288.671 16.308, 250140.471 474292.171 16.308, 250128.026 474294.089 16.308, 250114.528 474296.169 16.308, 250080.027 474301.748 16.308, 250030.235 474310.016 16.308, 250000 474314.919 16.196, 249994.681 474315.782 16.176, 249966.817 474320.237 16.176, 249966.586 474320.279 16.176, 249966.301 474320.356 16.176, 249964.36 474320.076 16.176, 249962.481 474320.395 16.176, 249962.3 474319.489 16.176, 249961.803 474318.084 16.176, 249961.257 474317.107 16.176, 249960.436 474315.617 16.176, 249960.183 474315.656 16.176, 249959.925 474314.561 16.176, 249958.104 474314.878 16.176, 249958.259 474315.835 16.176, 249957.959 474315.902 16.176, 249957.743 474317.773 16.176, 249957.52 474319.348 16.176, 249957.527 474320.489 16.176, 249957.651 474321.119 16.176, 249954.785 474321.674 16.176, 249953.579 474322.43 16.176, 249907.272 474329.926 16.176, 249850.701 474339.23 16.176, 249804.751 474346.658 16.176, 249732.066 474358.549 16.176, 249677.692 474367.472 16.176, 249637.052 474374.089 16.176, 249631.749 474374.979 16.176, 249630.627 474375.027 16.176, 249629.87 474373.453 16.176, 249628.835 474373.637 16.176, 249628.362 474375.226 16.176, 249627.649 474375.495 16.176, 249609.377 474378.572 16.176, 249595.188 474380.969 16.176, 249595.107 474380.3 16.176, 249571.471 474384.082 16.176, 249546.07 474388.202 16.176, 249527.074 474391.37 16.176, 249510.974 474394.118 16.176, 249490.592 474397.415 16.176, 249472.239 474400.384 16.176, 249444.49 474405.017 16.176, 249417.692 474409.383 16.176, 249390.911 474413.681 16.176, 249358.86 474419.272 16.176, 249322.676 474425.222 16.176, 249296.397 474429.721 16.176, 249294.266 474431.691 16.176, 249292.211 474432.057 16.176, 249291.557 474428.641 16.176, 249289.117 474429.048 16.176, 249289.738 474433.342 16.176, 249286.463 474435.064 16.176, 249285.036 474435.697 16.058, 249284.544 474435.839 16.058, 249284.023 474435.879 16.058, 249283.513 474435.782 16.058, 249283.18 474435.766 16.058, 249282.658 474435.95 16.058, 249282.223 474436.236 16.058, 249281.913 474436.455 16.058, 249281.762 474436.669 16.058, 249281.591 474436.982 16.058, 249281.412 474437.258 16.058, 249277.823 474434.439 16.058, 249276.012 474435.854 16.058, 249277.82 474439.937 16.058, 249277.572 474440.105 16.058, 249267.089 474447.192 16.058, 249256.346 474448.928 16.058, 249226.654 474453.808 16.058, 249215.773 474455.538 16.058, 249189.146 474459.918 16.058, 249177.49 474460.265 16.058, 249138.016 474461.604 16.058, 249103.831 474466.493 16.058, 249062.649 474472.061 16.058, 249011.734 474478.472 16.058, 248965.768 474483.809 16.058, 248945.356 474486.232 16.058, 248942.438 474486.578 16.058, 248936.025 474486.998 16.058, 248920.633 474484.201 16.058, 248908.99 474482.115 16.058, 248898.805 474479.724 16.058, 248883.001 474475.67 16.058, 248882.733 474475.678 16.058, 248878.99 474474.819 16.058, 248876.106 474486.312 16.058, 248879.88 474487.276 16.058, 248879.761 474487.692 16.058, 248869.481 474488.678 16.058, 248860.943 474495.032 16.058, 248860.764 474494.675 16.058, 248828.148 474497.168 16.058, 248788.376 474500.426 16.058, 248759.625 474502.545 16.058, 248759.62 474500.096 16.058, 248756.572 474500.317 16.058, 248756.519 474498.123 16.058, 248752.978 474498.308 16.058, 248753.096 474500.533 16.058, 248750.327 474500.713 16.058, 248750.457 474503.128 16.058, 248693.363 474506.635 16.058, 248626.243 474509.961 16.058, 248558.691 474512.766 16.058, 248521.137 474514.527 16.058, 248461.649 474516.908 16.058, 248406.237 474519.378 16.058, 248371.105 474520.823 16.058, 248332.359 474522.472 16.053, 248295.002 474524.09 16.053, 248245.626 474526.047 16.053, 248194.042 474528.293 16.053, 248139.173 474530.59 16.053, 248089.735 474532.639 16.053, 248023.217 474535.378 16.053, 247966.328 474537.824 16.053, 247924.874 474539.506 16.053, 247881.118 474541.452 16.053, 247841.335 474542.92 16.053, 247806.303 474544.375 16.053, 247755.811 474546.566 16.053, 247716.419 474548.2 16.053, 247657.035 474550.694 16.053, 247597.072 474553.214 16.053, 247557.856 474554.88 16.053, 247534.563 474555.816 16.053, 247534.086 474555.576 16.054, 247533.8 474555.26 16.054, 247533.41 474554.553 16.054, 247533.028 474554.476 16.054, 247521.272 474554.795 16.054, 247519.705 474554.918 16.054, 247519.08 474555.166 16.054, 247518.731 474555.588 16.054, 247518.364 474556.167 16.054, 247517.872 474556.473 16.054, 247517.548 474556.476 16.053, 247509.555 474556.789 16.053, 247473.775 474558.365 16.053, 247430.148 474560.13 16.053, 247382.897 474562.123 16.053, 247343.613 474563.765 16.053, 247262.672 474567.143 16.053, 247215.768 474569.058 16.053, 247193.507 474569.992 16.053, 247126.301 474572.842 16.053, 247067.066 474575.276 16.053, 247010.186 474577.716 16.053, 246931.3 474581.04 16.053, 246906.117 474582.055 16.053, 246898.112 474582.248 16.053, 246887.474 474581.363 16.053, 246877.74 474579.79 16.053, 246871.619 474578.363 16.053, 246865.021 474576.045 16.053, 246857.716 474572.877 16.053, 246845.569 474566.589 16.053, 246835.381 474560.381 16.053, 246803.393 474540.633 16.053, 246784.576 474529.328 16.053, 246760.385 474530.533 16.053, 246722.998 474558.079 16.053, 246701.631 474573.622 16.053, 246687.098 474582.947 16.053, 246679.037 474587.474 16.053, 246674.374 474589.282 16.053, 246667.492 474591.058 16.053, 246661.629 474592.056 16.053, 246650.953 474592.999 16.053, 246638.941 474593.564 16.053, 246596.938 474595.021 16.053, 246558.568 474596.814 16.053, 246558.172 474596.496 16.055, 246557.909 474595.912 16.055, 246557.589 474595.626 16.055, 246557.196 474595.588 16.055, 246549.607 474595.623 16.055, 246545.581 474595.861 16.055, 246545.066 474596.043 16.055, 246544.691 474596.326 16.055, 246544.434 474596.612 16.055, 246543.951 474597.128 16.055, 246543.579 474597.248 16.053, 246532.629 474597.77 16.053, 246500.641 474599.084 16.053, 246464.482 474600.64 16.053, 246406.576 474602.974 16.053, 246348.498 474605.386 16.053, 246311.656 474607.087 16.053, 246278.128 474608.499 16.053, 246245.321 474609.854 16.053, 246205.548 474611.404 16.053, 246170.872 474612.282 16.053, 246130.35 474613.025 16.053, 246119.598 474613.072 16.053, 246083.838 474618.375 16.053, 246044.27 474618.666 16.053, 246008.726 474618.881 16.053, 245997.762 474617.62 16.053, 245963.493 474613.636 16.053, 245948.196 474613.481 16.053, 245908.476 474612.743 16.053, 245874.904 474612.283 16.053, 245833.089 474611.707 16.053, 245791.759 474611.173 16.053, 245744.592 474610.372 16.053, 245707.2 474609.924 16.053, 245665.282 474609.208 16.053, 245623.477 474608.674 16.053, 245574.953 474608.001 16.053, 245533.236 474607.534 16.053, 245495.827 474607.028 16.053, 245465.196 474606.525 16.053, 245465.11 474603.717 16.053, 245464.415 474603.385 16.055, 245463.837 474603.511 16.055, 245461.915 474603.602 16.055, 245460.43 474603.689 16.055, 245459.852 474603.754 16.053, 245459.773 474606.546 16.053, 245432.065 474606.196 16.053, 245391.499 474605.585 16.053, 245357.35 474605.003 16.053, 245325.306 474604.593 16.053, 245297.296 474604.294 16.053, 245261.555 474603.645 16.053, 245219.922 474603.16 16.053, 245177.242 474602.575 16.053, 245135.001 474602.093 16.053, 245096.766 474601.626 16.053, 245048.858 474600.912 16.053, 245004.262 474600.299 16.053, 244967.073 474599.662 16.053, 244933.9 474599.342 16.053, 244909.466 474598.884 16.053, 244909.455 474595.61 16.053, 244904.398 474595.665 16.053, 244904.319 474598.888 16.053, 244856.406 474598.341 16.053, 244808.678 474597.688 16.053, 244764.083 474597.078 16.053, 244726.299 474596.479 16.053, 244684.59 474596.017 16.053, 244646.29 474595.267 16.053, 244637.208 474595.131 16.053, 244628.896 474595.09 16.053, 244615.403 474596.572 16.053, 244589.525 474599.526 16.053, 244547.86 474598.545 16.053, 244546.641 474598.31 16.053, 244523.112 474592.733 16.053, 244505.414 474588.728 16.053, 244487.571 474587.095 16.053, 244467 474584.801 16.053, 244429.296 474580.718 16.053, 244386.658 474574.46 16.053, 244336.049 474566.065 16.053, 244286.883 474556.272 16.053, 244240.973 474545.913 16.053, 244196.153 474534.364 16.053, 244175.887 474528.863 16.053, 244160.923 474524.544 16.053, 244144.799 474519.709 16.053, 244121.888 474512.73 16.053, 244096.794 474504.651 16.053, 244072.169 474496.311 16.053, 244046.745 474487.207 16.053, 244031.554 474481.443 16.053, 244012.013 474474.175 16.053, 243982.725 474462.379 16.053, 243957.286 474451.656 16.053, 243930.632 474440.045 16.053, 243913.489 474432.222 16.053, 243892.551 474422.384 16.053, 243874.234 474413.396 16.053, 243851.614 474402.016 16.053, 243823.152 474387.315 16.053, 243807.824 474378.914 16.053, 243793.863 474371.309 16.053, 243736.93 474338.335 16.053, 243720.17 474327.952 16.053, 243700.533 474315.921 16.053, 243675.825 474300.773 16.053, 243651.45 474285.725 16.053, 243633.595 474274.796 16.053, 243619.519 474266.122 16.053, 243607.704 474258.716 16.053, 243597.089 474251.573 16.053, 243578.633 474237.863 16.053, 243552.876 474218.467 16.053, 243539.936 474208.739 16.053, 243520.713 474193.263 16.053, 243497.09 474173.813 16.053, 243450.546 474133.272 16.053, 243407.866 474094.504 16.053, 243385.199 474073.605 16.053, 243367.951 474057.677 16.053, 243351.987 474043.081 16.053, 243331.619 474024.332 16.053, 243314.961 474009.015 16.053, 243296.625 473993.401 16.053, 243287.94 473986.663 16.053, 243240.761 473953.647 16.053, 243239.224 473955.916 16.053, 243238.378 473955.391 16.053, 243233.963 473961.985 16.053, 243234.723 473962.595 16.053, 243232.519 473965.937 16.053, 243251.207 473978.58 16.053, 243253.35 473980.03 16.053, 243255.347 473982.089 16.053, 243257.378 473984.914 16.053, 243258.357 473987.727 16.053, 243258.67 473990.115 16.053, 243258.419 473992.703 16.053, 243257.297 473995.496 16.053, 243253.392 474001.476 16.053, 243246.321 474011.882 16.053, 243245.191 474013.607 16.053, 243244.65 474014.155 16.053, 243243.841 474014.667 16.053, 243242.965 474015.107 16.053, 243242.064 474015.309 16.053, 243240.948 474015.362 16.053, 243228.177 474012.682 16.053, 243208.861 474008.521 16.053, 243203.992 474005.365 16.053, 243197.289 474015.028 16.053), (243249.909 473975.707 16.053, 243244.279 473971.939 16.053, 243246.539 473968.78 16.053, 243252.068 473972.481 16.053, 243251.43 473973.434 16.053, 243249.909 473975.707 16.053), (246028.494 474654.753 16.053, 246028.408 474652.848 16.053, 246036.929 474652.797 16.053, 246036.912 474654.747 16.053, 246028.494 474654.753 16.053), (246036.997 474624.863 16.053, 246028.615 474624.835 16.053, 246028.649 474622.922 16.053, 246037.058 474622.874 16.053, 246036.997 474624.863 16.053), (251334.175 474118.685 16.308, 251333.896 474117.375 16.308, 251348.432 474115.058 16.308, 251348.643 474116.379 16.308, 251334.27 474118.67 16.308, 251334.175 474118.685 16.308)))'
        
class Test_absolute_path():
    def test_absolute_path_01(self):
        """
        Convert absolute path into relative path using relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        afile = "d:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert dfastmi.io.absolute_path(rootdir, rfile) == afile

    def test_absolute_path_02(self):
        """
        Empty string should not be adjusted by relative_path.
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = ""
        assert dfastmi.io.absolute_path(rootdir, file) == file

    def test_absolute_path_03(self):
        """
        If path on different drive, it shouldn't be adjusted by relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = "e:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert dfastmi.io.absolute_path(rootdir, file) == file

    def test_absolute_path_04(self):
        """
        Convert absolute path into relative path using relative_path (Linux).
        """
        rootdir = os.sep + "some" + os.sep + "dir"
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert dfastmi.io.absolute_path(rootdir, rfile) == afile

class Test_relative_path():
    def test_relative_path_01(self):
        """
        Convert absolute path into relative path using relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        afile = "d:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert dfastmi.io.relative_path(rootdir, afile) == rfile

    def test_relative_path_02(self):
        """
        Empty string should not be adjusted by relative_path.
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = ""
        assert dfastmi.io.relative_path(rootdir, file) == file

    def test_relative_path_03(self):
        """
        If path on different drive, it shouldn't be adjusted by relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = "e:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert dfastmi.io.relative_path(rootdir, file) == file

    def test_relative_path_04(self):
        """
        Convert absolute path into relative path using relative_path (Linux).
        """
        rootdir = os.sep + "some" + os.sep + "dir"
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert dfastmi.io.relative_path(rootdir, afile) == rfile
