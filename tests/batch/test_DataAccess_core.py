import os
import pytest
import dfastmi.batch.core

from dfastmi.io.RiversObject import RiversObject
from configparser import ConfigParser

class Test_batch_save_configuration_file():      
    def given_configuration_file_when_save_configuration_file_then_file_is_saved_with_expected_data(self, tmp_path):
        expected_lines = [
        "[General]\n",
        "  riverkm     = RiverKM\n",
        "  figuredir   = FigureDir\n",
        "  outputdir   = OutputDir\n",
        "\n",
        "[SomeSection]\n",
        "  reference   = reference\n",
        "  withmeasure = with_measure\n",
        ]
        
        file_path = tmp_path / "test_file.cfg"
        config = self.sample_config(tmp_path)
        
        dfastmi.batch.core.save_configuration_file(file_path, config)
        
        assert os.path.exists(file_path)
        with open(file_path, 'r') as file:
            file_lines = file.readlines()
            
        assert len(file_lines) == len(expected_lines)
        assert file_lines == expected_lines
        
    def sample_config(self, tmp_path):
        config = ConfigParser()
        config["General"] = {
            "RiverKM": tmp_path / "RiverKM",
            "FigureDir": tmp_path / "FigureDir",
            "OutputDir": tmp_path / "OutputDir"
        }
        config["SomeSection"] = {
            "Reference": tmp_path / "reference",
            "WithMeasure": tmp_path / "with_measure"
        }
        return config
    
class Test_batch_check_configuration():
    @pytest.fixture
    def rivers(self):
        return  RiversObject("dfastmi/Dutch_rivers_v1.ini")
    
    @pytest.fixture
    def config(self):
        return  ConfigParser()
    
    def given_version_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):       
        assert not dfastmi.batch.core.check_configuration(rivers, config)
        
    def given_version_with_no_matching_version_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):       
        config.add_section("General")
        config.set("General", "Version", "0.0")
        
        assert not dfastmi.batch.core.check_configuration(rivers, config)
    
    class Test_check_configuration_v1():
        @pytest.fixture
        def rivers(self):
            return  RiversObject("dfastmi/Dutch_rivers_v1.ini")
        
        @pytest.fixture
        def config(self):
            return  ConfigParser()
                    
        def given_version_1_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_general_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config)
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_general_section_with_qthreshold_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config)
            config.set("General", "Qthreshold", "100")
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_general_section_with_qthreshold_and_qbankfull_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section_with_q_values(config)
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_q_sections_with_discharge_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):           
            self.set_valid_general_section_with_q_values(config)
            self.add_q_section(config)
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_mode_specific_test_with_discharge_check_configuration_then_return_true(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section_with_q_values(config)
            self.add_q_section(config)
            config.set("General", "mode", "test")
            
            assert dfastmi.batch.core.check_configuration(rivers, config)
            
        def set_valid_general_section(self, config : ConfigParser):
            config.add_section("General")
            config.set("General", "Version", "1.0")
            config.set("General", "Branch", "Bovenrijn & Waal")
            config.set("General", "Reach", 'Bovenrijn                    km  859-867')
            
        def set_valid_general_section_with_q_values(self, config : ConfigParser):
            self.set_valid_general_section(config)
            config.set("General", "Qthreshold", "100")
            config.set("General", "Qbankfull", "100")
            
        def add_q_section(self, config : ConfigParser):
            config.add_section("Q1")
            config.set("Q1", "Discharge", "1300.0")
            config.add_section("Q2")
            config.set("Q2", "Discharge", "1300.0")
            config.add_section("Q3")
            config.set("Q3", "Discharge", "1300.0")
    
    class Test_check_configuration_v2():
        @pytest.fixture
        def rivers(self):
            return  RiversObject("dfastmi/Dutch_rivers_v2.ini")
        
        @pytest.fixture
        def config(self):
            config = ConfigParser()
            self.set_valid_general_section(config)
            return  config
        
        def given_version_2_when_check_configuration_then_return_false(self, rivers : RiversObject):
            assert not dfastmi.batch.core.check_configuration(rivers, ConfigParser())
        
        def given_general_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):           
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_general_section_and_c_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            config.add_section("C1")
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_only_discharge_in_c_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            config.add_section("C1")
            config.set("C1", "Discharge", "1300.0")
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)
            
        def given_partial_c_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            config.add_section("C1")
            config.set("C1", "Discharge", "1300.0")
            config.set("C1", "Reference", "1300.0")
            
            assert not dfastmi.batch.core.check_configuration(rivers, config)

        def given_c_sections_with_incorrect_values_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.add_c_section(config, "C1", "1300.0")
            self.add_c_section(config, "C2", "1300.0")
            self.add_c_section(config, "C3", "1300.0")
            self.add_c_section(config, "C4", "1300.0")
            self.add_c_section(config, "C5", "1300.0")
            self.add_c_section(config, "C6", "1300.0")
                
            assert not dfastmi.batch.core.check_configuration(rivers, config)     
                
        def given_correct_c_sections_when_check_configuration_then_return_true(self, rivers : RiversObject, config : ConfigParser):
            self.add_c_section(config, "C1", "1300.0")
            self.add_c_section(config, "C2", "2000.0")
            self.add_c_section(config, "C3", "3000.0")
            self.add_c_section(config, "C4", "4000.0")
            self.add_c_section(config, "C5", "6000.0")
            self.add_c_section(config, "C6", "8000.0")
                
            assert dfastmi.batch.core.check_configuration(rivers, config)
        
        def set_valid_general_section(self, config : ConfigParser):
            config.add_section("General")
            config.set("General", "Version", "2.0")
            config.set("General", "Branch", "Bovenrijn & Waal")
            config.set("General", "Reach", 'Bovenrijn                    km  859-867')
            
        def add_c_section(self, config: ConfigParser, name: str, value : str):
            config.add_section(name)
            config.set(name, "Discharge",   value)
            config.set(name, "Reference",   value)
            config.set(name, "WithMeasure", value)