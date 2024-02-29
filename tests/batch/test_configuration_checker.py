from unittest.mock import MagicMock
from configparser import ConfigParser
import pytest

from dfastmi.io.Branch import Branch
from dfastmi.batch.ConfigurationChecker import ConfigurationChecker
from dfastmi.io.Reach import ReachAdvanced

from dfastmi.io.RiversObject import RiversObject

class Test_configuration_checker():
    @pytest.fixture
    def configuration_checker(self):
        return ConfigurationChecker()
    
    @pytest.fixture
    def rivers(self):
        mock_reach = MagicMock(spec=ReachAdvanced)
        mock_reach.name = "myReach"
        mock_reach.hydro_q = (80.1, 80.2)        

        mock_branch = MagicMock(spec=Branch)
        mock_branch.name = "myBranch"
        mock_branch.reaches = [mock_reach]
        
        rivers = MagicMock(spec=RiversObject)
        rivers.branches = [mock_branch]
        return rivers

    @pytest.fixture
    def config(self):
        config = ConfigParser()
        self.set_valid_general_section(config)
        return  config

    def given_version_2_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationChecker, rivers : RiversObject):
        assert not configuration_checker.check_configuration(rivers, ConfigParser())

    def given_general_section_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        assert not configuration_checker.check_configuration(rivers, config)

    def given_general_section_and_c_section_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        config.add_section("C1")

        assert not configuration_checker.check_configuration(rivers, config)

    def given_only_discharge_in_c_section_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        config.add_section("C1")
        config.set("C1", "Discharge", "80.1")

        assert not configuration_checker.check_configuration(rivers, config)

    def given_partial_c_section_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        config.add_section("C1")
        config.set("C1", "Discharge", "80.1")
        config.set("C1", "Reference", "80.1")

        assert not configuration_checker.check_configuration(rivers, config)

    def given_c_sections_with_incorrect_values_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        self.add_c_section(config, "C1", "27.0")
        self.add_c_section(config, "C2", "2.14")
       
        assert not configuration_checker.check_configuration(rivers, config)

    def given_correct_c_sections_when_check_configuration_then_return_true(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        self.add_c_section(config, "C1", "80.1")
        self.add_c_section(config, "C2", "80.2")
        
        assert configuration_checker.check_configuration(rivers, config)

    def set_valid_general_section(self, config : ConfigParser):
        config.add_section("General")
        config.set("General", "Version", "2.0")
        config.set("General", "Branch", "myBranch")
        config.set("General", "Reach", 'myReach')

    def add_c_section(self, config: ConfigParser, name: str, value : str):
        config.add_section(name)
        config.set(name, "Discharge",   value)
        config.set(name, "Reference",   value)
        config.set(name, "WithMeasure", value)