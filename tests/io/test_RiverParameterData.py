import pytest
import configparser

from dfastmi.io.RiverParameterData import RiverParameterData

def _initialize_river_data_from_config(config):
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        river_data = RiverParameterData(config)
        river_data.initialize(branches, nreaches)
        return river_data

class Test_collect_values1():
    
    def test_collect_values1_01(self):
        """
        Testing sucessful collect_values1 call.
        """
        config = configparser.ConfigParser()
        config.add_section("General")
        config["General"]["A"] = "0.0"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0"
        config["Branch1"]["A1"] = "2.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0"
        config["Branch2"]["A3"] = "4.0"
        river_data = _initialize_river_data_from_config(config)

        key = "A"
        data = [[2.0, 1.0], [3.0, 0.0, 4.0]]
        
        assert river_data.collect_values1(key) == data

    def test_collect_values1_02(self):
        """
        Testing collect_values1 raising an Exception.
        """
        config = configparser.ConfigParser()
        config.add_section("General")
        config["General"]["A"] = "0.0 0.1"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0"
        config["Branch1"]["A1"] = "2.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0"
        config["Branch2"]["A3"] = "4.0"
        river_data = _initialize_river_data_from_config(config)
        key = "A"
        expected_Message = 'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format("A", 2, "Branch2", "0.0 0.1", 1)
        with pytest.raises(Exception) as cm:
            river_data.collect_values1(key)
        assert str(cm.value) == expected_Message

class Test_collect_values2():
    def test_collect_values2_01(self):
        """
        Testing successful collect_values2 call.
        """
        config = configparser.ConfigParser()
        config.add_section("General")
        config["General"]["A"] = "0.0 0.0"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0 0.1"
        config["Branch1"]["A1"] = "2.0 0.2"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3"
        config["Branch2"]["A3"] = "4.0 0.4"
        river_data = _initialize_river_data_from_config(config)
        key = "A"
        data = [[(2.0, 0.2), (1.0, 0.1)], [(3.0, 0.3), (0.0, 0.0), (4.0, 0.4)]]        
        assert river_data.collect_values2(key) == data

    def test_collect_values2_02(self):
        """
        Testing collect_values2 raising an Exception.
        """
        config = configparser.ConfigParser()
        config.add_section("General")
        config["General"]["A"] = "0.0 0.0"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0"
        config["Branch1"]["A1"] = "2.0 0.2"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3"
        config["Branch2"]["A3"] = "4.0 0.4"
        river_data = _initialize_river_data_from_config(config)
        key = "A"
        with pytest.raises(Exception) as cm:
            river_data.collect_values2(key)
        assert str(cm.value) == 'Reading A for reach 2 on Branch1 returns "1.0". Expecting 2 values.'

class Test_collect_values4():
    
    def test_collect_values4_01(self):
        """
        Testing collect_values4.
        """
        config = configparser.ConfigParser()
        config.add_section("General")
        config["General"]["A"] = "0.0 0.0 0.0 0.1"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0 0.1 0.0 0.01"
        config["Branch1"]["A1"] = "2.0 0.2 0.02 0.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3 -0.03 0.0"
        config["Branch2"]["A3"] = "4.0 0.4 0.0 -0.04"
        river_data = _initialize_river_data_from_config(config)
        key = "A"
        data = [[(2.0, 0.2, 0.02, 0.0), (1.0, 0.1, 0.0, 0.01)], [(3.0, 0.3, -0.03, 0.0), (0.0, 0.0, 0.0, 0.1), (4.0, 0.4, 0.0, -0.04)]]
        assert river_data.collect_values4(key) == data

    def test_collect_values4_02(self):
        """
        Testing collect_values4 raising an Exception.
        """
        config = configparser.ConfigParser()
        config.add_section("General")
        config["General"]["A"] = "0.0 0.0 0.0 0.1"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0 0.1 0.0 0.01"
        config["Branch1"]["A1"] = "2.0 0.2 0.02 0.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3 -0.03 0.0"
        config["Branch2"]["A3"] = "4.0 0.4 -0.04"
        river_data = _initialize_river_data_from_config(config)
        key = "A"
        with pytest.raises(Exception) as cm:
            river_data.collect_values4(key)
        assert str(cm.value) == 'Reading A for reach 3 on Branch2 returns "4.0 0.4 -0.04". Expecting 4 values.'

class Test_collect_int_values1():
    def test_collect_int_values1_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        globalKey = "KEY"
        globalVal = "YES"
        config[generalGroup][globalKey] = globalVal
        river_data = _initialize_river_data_from_config(config)
        
        with pytest.raises(Exception) as cm:
            river_data.collect_int_values1(globalKey)
        assert str(cm.value) == 'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(globalKey, 1, "Branch1", globalVal, 1)
    
    def test_collect_int_values1_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        globalKey = "KEY"
        globalVal = "1"
        config[generalGroup][globalKey] = globalVal
        river_data = _initialize_river_data_from_config(config)
        
        int_values = river_data.collect_int_values1(globalKey)
        assert int_values == [[1,1],[1,1,1]]

    def test_collect_int_values1_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        key = "KEY"
        river_data = _initialize_river_data_from_config(config)
        int_values = river_data.collect_int_values1(key, 1)
        assert int_values == [[1,1],[1,1,1]]

    def test_collect_int_values1_04(self):
        """
        
        """
        config = configparser.ConfigParser()
        generalGroup = "General"
        config.add_section(generalGroup)
        key = "KEY"
        branch1 = "Branch1"
        branch2 = "Branch2"
        config.add_section(branch1)
        config[branch1][key + "1"] = "2"
        config[branch1][key + "2"] = "3"

        config.add_section(branch2)
        config[branch2][key + "1"] = "4"
        config[branch2][key + "2"] = "5"
        config[branch2][key + "3"] = "6"
        
        river_data = _initialize_river_data_from_config(config)
        
        intValues = river_data.collect_int_values1(key)
        assert intValues == [[2,3],[4,5,6]]

class Test_collect_values_logical():
    def _initialize_river_data_with_3_channels_from_config(self, config):
        branches = ['Channel1','Channel2','Channel3']
        nreaches  = [2,1,3]
        river_data = RiverParameterData(config)
        river_data.initialize(branches, nreaches)
        return river_data
    
    def test_collect_values_logical_01(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        river_data = self._initialize_river_data_with_3_channels_from_config(config)
        
        assert river_data.collect_values_logical(myKey) == [[True,True],[True],[True, True, True]]
    
    def test_collect_values_logical_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "General"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = ""
        config[myGroup][myKey] = myVal
        river_data = self._initialize_river_data_with_3_channels_from_config(config)

        with pytest.raises(Exception) as cm:
            river_data.collect_values_logical(myKey)
        assert str(cm.value) == 'Reading KEY for reach 1 on Channel1 returns "". Expecting 1 values.'

    def test_collect_values_logical_03(self):
        """
        
        """
        config = configparser.ConfigParser()
        myKey = "KEY"
        river_data = self._initialize_river_data_with_3_channels_from_config(config)
        with pytest.raises(Exception) as cm:
            river_data.collect_values_logical(myKey)
        assert str(cm.value) == 'Reading KEY for reach 1 on Channel1 returns "". Expecting 1 values.'

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
        config_data = RiverParameterData(config)

        assert config_data.config_get_bool(myGroup, myKey) == True

    def test_config_get_bool_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
        assert config_data.config_get_int(myGroup, myKey) == 1

    def test_config_get_int_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
        assert config_data.config_get_float(myGroup, myKey) == 1

    def test_config_get_float_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)     
        assert config_data.config_get_float(myGroup, myKey, positive=True) == 0.0
        
    def test_config_get_float_05(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"        
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
        assert config_data.config_get_str(myGroup, myKey) == "YES"

    def test_config_get_str_02(self):
        """
        
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
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
        config_data = RiverParameterData(config)
        assert config_data.config_get_range(myGroup, myKey) == (0.0,10.0)
