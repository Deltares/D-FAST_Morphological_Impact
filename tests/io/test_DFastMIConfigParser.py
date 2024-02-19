"""
Tests for DFastMIConfig class
"""
import sys
from mock import Mock
from contextlib import contextmanager
from io import StringIO
from typing import Tuple
import pytest
import configparser

from dfastmi.io.IBranch import IBranch
from dfastmi.io.Reach import Reach, ReachAdvanced

from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class Test_DFastMIConfigParser():
    _reach : Reach

    @pytest.fixture
    def setup_data(self):
        self._reach = Reach("Reach1")
        branch = Mock(IBranch)
        branch.name = "Branch1"
        self._reach.parent_branch = branch


    def given_simple_river_config_when_read_key_with_custom_unknown_type_then_exception_thrown(self, setup_data):
        """
        When we
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        river_data._processor.register_processor(Test_DFastMIConfigParser, river_data._process_entry_value, lambda x: 1/0)

        with pytest.raises(Exception) as cm:
            river_data.read_key(Test_DFastMIConfigParser, myKey, self._reach)
        assert str(cm.value) == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "{myVal}". Expecting 1 values.'
    
    def given_simple_river_config_when_read_key_with_custom_unknown_tuple_type_then_exception_thrown(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        river_data._processor.register_processor(Test_DFastMIConfigParser, river_data._process_tuple_entry_value, lambda x: 1/0)
        assert river_data.read_key(Test_DFastMIConfigParser, myKey, self._reach) == ()
        


class Test_read_key():
    _reach : Reach

    @pytest.fixture
    def setup_data(self):
        self._reach = Reach("Reach1")
        branch = Mock(IBranch)
        branch.name = "Branch1"
        self._reach.parent_branch = branch

    def test_read_key_bool_01(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(bool, myKey, self._reach, False)

    def test_read_key_bool_02(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = ""
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)

        with pytest.raises(Exception) as cm:
            river_data.read_key(bool, myKey, self._reach)
        assert str(cm.value) == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "". Expecting 1 values.'

    def test_read_key_bool_03(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myKey = "KEY"
        river_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            river_data.read_key(bool, myKey, self._reach)
        assert str(cm.value) == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "". Expecting 1 values.'

    
    def test_read_key_int_01(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "1"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(int, myKey, self._reach,) == 1
    
    def test_read_key_int_02(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = ""
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(int, myKey, self._reach, 2) == 2
    
    def test_read_key_float_01(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "8.01"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(float, myKey, self._reach) == 8.01
    
    def test_read_key_float_tuple_01(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "8.01 8.02"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(Tuple[float, ...], myKey, self._reach, expected_number_of_values=2) == (8.01, 8.02)
    
    def test_read_key_float_tuple_02(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "8.01 8.02 2.14 5.88"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(Tuple[float, ...], myKey, self._reach, expected_number_of_values=4) == (8.01, 8.02, 2.14, 5.88)
    
    def test_read_key_float_tuple_03(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "8.01 8.02 2.14 5.88 76 27"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(Tuple[float, ...], myKey, self._reach) == (8.01, 8.02, 2.14, 5.88, 76, 27)
        
    def test_read_key_float_tuple_04(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = ""
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        assert river_data.read_key(Tuple[float, ...], myKey, self._reach, (0.0, 0.0), 2) == (0.0, 0.0)

    def test_read_key_float_tuple_05(self, setup_data):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "8.01 8.02 2.14 5.88 76 27"
        config[myGroup][myKey] = myVal
        river_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            river_data.read_key(Tuple[float, ...], myKey, self._reach, expected_number_of_values=4)
        assert str(cm.value) == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "{myVal}". Expecting 4 values.'
        
    
class Test_config_get():
    def test_config_get_bool_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)

        assert config_data.config_get(bool, myGroup, myKey)

    def test_config_get_bool_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(bool, myGroup, myKey)
        assert str(cm.value) == 'No bool value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)

    def test_config_get_bool_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(bool, myGroup, myKey, default=True)


    def test_config_get_int_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "1"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(int, myGroup, myKey) == 1

    def test_config_get_int_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(int, myGroup, myKey)
        assert str(cm.value) == f'No {int.__name__} value specified for required keyword "{myKey}" in block "{myGroup}".'

    def test_config_get_int_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "-1"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(int, myGroup, myKey, positive=True)
        assert str(cm.value) == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {myVal}.'
    
    def test_config_get_int_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(int, myGroup, myKey, positive=True)
        assert str(cm.value) == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {myVal}.'
        
    def test_config_get_int_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"        
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(int, myGroup, myKey, default=1) == 1

    def test_config_get_float_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "1"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(float, myGroup, myKey) == 1

    def test_config_get_float_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(float, myGroup, myKey)
        assert str(cm.value) == f'No {float.__name__} value specified for required keyword "{myKey}" in block "{myGroup}".'

    def test_config_get_float_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "-0.5"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(float, myGroup, myKey, positive=True)
        assert str(cm.value) == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {myVal}.'
    
    def test_config_get_float_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0"
        config[myGroup][myKey] = myVal      
        config_data = DFastMIConfigParser(config)     
        
        with pytest.raises(Exception) as cm:
            config_data.config_get(float, myGroup, myKey, positive=True)
        assert str(cm.value) == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {float(myVal)}.'
        
    def test_config_get_float_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"        
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(float, myGroup, myKey, default=0.5) == 0.5

    def test_config_get_str_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(str, myGroup, myKey) == "YES"

    def test_config_get_str_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(str, myGroup, myKey)
        assert str(cm.value) == f'No {str.__name__} value specified for required keyword "{myKey}" in block "{myGroup}".'
 
    def test_config_get_str_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(str, myGroup, myKey, default="YES sir") == "YES sir"

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
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_range(myGroup, myKey) == (0.0,10.0)
    
    def test_config_get_range_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "[10.0:0.0]"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_range(myGroup, myKey) == (0.0,10.0)

    def test_config_get_range_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0.0-10.0"
        config[myGroup][myKey] = myVal #even on not setting this value we expect the exception
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_range(myGroup, myKey)
        assert str(cm.value) == 'Invalid range specification "{}" for required keyword "{}" in block "{}".'.format(myVal, myKey, myGroup)
 
    def test_config_get_range_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_range(myGroup, myKey, default="YES") == "YES"        
    
    def test_config_get_range_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0.0:10.0"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_range(myGroup, myKey) == (0.0,10.0)
    
    def test_config_get_range_06(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "10.0:0.0"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_range(myGroup, myKey) == (0.0,10.0)
