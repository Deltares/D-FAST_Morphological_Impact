import dfastmi.RiversObject
import configparser
import os

import pytest

class Test_read_rivers():
    def test_read_rivers_01(self):
        """
        Testing read_rivers, collect_values1, collect_values2 and collect_values4.
        """
        print("current work directory: ", os.getcwd())
        rivers = {}
        rivers['branches'] = ['Branch1', 'Branch2']
        rivers['reaches'] = [['Branch1 R1'], ['Branch2 R1', 'Branch2 R2']]
        rivers['qlocations'] = ['L1', 'L2']
        rivers['proprate_high'] = [[3.14], [3.65, 3.65]]
        rivers['proprate_low'] = [[0.8], [0.8, 0.9]]
        rivers['normal_width'] = [[250.0], [250.0, 100.0]]
        rivers['ucritical'] = [[0.3], [0.3, 0.3]]
        rivers['qbankfull'] = [[150.0], [2500.0, 2500.0]]
        rivers['qstagnant'] = [[50.0], [0.0, 1500.0]]
        rivers['qmin'] = [[1.0], [1.0, 1.0]]
        rivers['qfit'] = [[(10.0, 20.0)], [(800.0, 1280.0), (800.0, 1280.0)]]
        rivers['qlevels'] = [[(100.0, 200.0, 300.0, 400.0)], [(1000.0, 2000.0, 3000.0, 4000.0), (1000.0, 2000.0, 3000.0, 4000.0)]]
        rivers['dq'] = [[(5.0, 15.0)], [(1000.0, 1000.0), (1000.0, 1000.0)]]
        rivers['version'] = '1.0'
        self.maxDiff = None
        assert dfastmi.RiversObject.read_rivers("tests/files/read_rivers_test.ini") == rivers
    
    def test_read_rivers_02(self):
        """
        Testing read rivers raising an Exception.
        """        
        with pytest.raises(Exception) as cm:
            dfastmi.RiversObject.read_rivers("tests/files/read_rivers_test_no_version.ini")
        assert str(cm.value) == 'No version information in the file tests/files/read_rivers_test_no_version.ini!'

    def test_read_rivers_03(self):
        """
        Testing read rivers raising an Exception.
        """        
        with pytest.raises(Exception) as cm:
            dfastmi.RiversObject.read_rivers("tests/files/read_rivers_test_wrong_version.ini")
        assert str(cm.value) == 'Unsupported version number 0.0 in the file tests/files/read_rivers_test_wrong_version.ini!'

class Test_read_rivers2():    
    def test_read_rivers2_01(self):
        """
        Testing version
        """
        print("current work directory: ", os.getcwd())
        rivers = dfastmi.RiversObject.read_rivers("tests/files/read_rivers_test_2_0_version.ini")
        assert rivers['version'] == '2.0'
    
    def test_read_rivers2_02(self):
        """
        Testing read_rivers2, collect_values1, collect_values2 and collect_values4.
        """
        print("current work directory: ", os.getcwd())
        rivers = {}
        rivers['branches'] = ['Branch1', 'Branch2']
        rivers['reaches'] = [['Branch1 R1'], ['Branch2 R1', 'Branch2 R2']]
        rivers['qlocations'] = ['L1', 'L2']
        rivers['normal_width'] = [[250.0], [250.0, 100.0]]
        rivers['ucritical'] = [[0.3], [0.3, 0.3]]
        rivers['qstagnant'] = [[50.0], [0.0, 1500.0]]
        rivers['qfit'] = [[(10.0, 20.0)], [(800.0, 1280.0), (800.0, 1280.0)]]
        
        rivers['version'] = '2.0'
        
        rivers['autotime'] = [[False], [False, False]]
        rivers['cdisch'] = [[(11.0, 21.0)], [(11.0, 21.0), (11.0, 21.0)]]
        rivers['cform'] = [[2], [2, 2]]
        rivers['hydro_q'] = [[()], [(), ()]]
        rivers['hydro_t'] = [[()], [(), ()]]
        rivers['prop_c'] = [[()], [(), ()]]
        rivers['prop_q'] = [[()], [(), ()]]
        rivers['tide'] = [[True], [True, True]]
        rivers['tide_bc'] = [[()], [(), ()]]

        self.maxDiff = None
        assert dfastmi.RiversObject.read_rivers("tests/files/read_riversv2_test.ini") == rivers
    
            
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
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        data = [[2.0, 1.0], [3.0, 0.0, 4.0]]
        self.maxDiff = None
        assert dfastmi.RiversObject.collect_values1(config, branches, nreaches, key) == data

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
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        with pytest.raises(Exception) as cm:
            dfastmi.RiversObject.collect_values1(config, branches, nreaches, key)
        expected_Message = 'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                            "A", 2, "Branch2", "0.0 0.1", 1
                        )
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
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        data = [[(2.0, 0.2), (1.0, 0.1)], [(3.0, 0.3), (0.0, 0.0), (4.0, 0.4)]]
        self.maxDiff = None
        assert dfastmi.RiversObject.collect_values2(config, branches, nreaches, key) == data

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
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        with pytest.raises(Exception) as cm:
            dfastmi.RiversObject.collect_values2(config, branches, nreaches, key)
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
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        data = [[(2.0, 0.2, 0.02, 0.0), (1.0, 0.1, 0.0, 0.01)], [(3.0, 0.3, -0.03, 0.0), (0.0, 0.0, 0.0, 0.1), (4.0, 0.4, 0.0, -0.04)]]
        self.maxDiff = None
        assert dfastmi.RiversObject.collect_values4(config, branches, nreaches, key) == data

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
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        with pytest.raises(Exception) as cm:
            dfastmi.RiversObject.collect_values4(config, branches, nreaches, key)
        assert str(cm.value) == 'Reading A for reach 3 on Branch2 returns "4.0 0.4 -0.04". Expecting 4 values.'
