import sys
from contextlib import contextmanager
from io import StringIO
from typing import Tuple
import pytest
import configparser
from dfastmi.io.Branch import Branch
from dfastmi.io.Reach import Reach, ReachAdvanced

from dfastmi.io.RiverParameterData import DFastMIConfigParser

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class Test_read_key():
    _reach : Reach

    @pytest.fixture
    def setup_data(self):
        self._reach = Reach("Reach1")
        self._reach.parent_branch_name = "Branch1"        

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
        config_data = DFastMIConfigParser(config)

        assert config_data.config_get_bool(myGroup, myKey) == True

    def test_config_get_bool_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_bool(myGroup, myKey)
        assert str(cm.value) == 'No boolean value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)

    def test_config_get_bool_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_bool(myGroup, myKey, default=True) == True

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
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_int(myGroup, myKey) == 1

    def test_config_get_int_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_int(myGroup, myKey)
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
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_int(myGroup, myKey, positive=True)
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
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_int(myGroup, myKey, positive=True)
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
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_int(myGroup, myKey, default=1) == 1

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
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_float(myGroup, myKey) == 1

    def test_config_get_float_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_float(myGroup, myKey)
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
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_float(myGroup, myKey, positive=True)
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
        config_data = DFastMIConfigParser(config)     
        assert config_data.config_get_float(myGroup, myKey, positive=True) == 0.0
        
    def test_config_get_float_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"        
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_float(myGroup, myKey, default=0.5) == 0.5        

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
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_str(myGroup, myKey) == "YES"

    def test_config_get_str_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get_str(myGroup, myKey)
        assert str(cm.value) == 'No value specified for required keyword "{}" in block "{}".'.format(myKey, myGroup)
 
    def test_config_get_str_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get_str(myGroup, myKey, default="YES") == "YES"

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
