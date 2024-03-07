from unittest.mock import create_autospec
from configparser import ConfigParser
import pytest

from dfastmi.batch.ConfigurationCheckerLegacy import DFLOWFM_MAP, WAQUA_EXPORT, ConfigurationCheckerLegacy
from dfastmi.io.Branch import Branch
from dfastmi.io.ReachLegacy import ReachLegacy
from dfastmi.io.RiversObject import RiversObject


class Test_configuration_checker_legacy():
    @pytest.fixture
    def configuration_checker(self):
        return ConfigurationCheckerLegacy()
    
    @pytest.fixture
    def rivers(self):
        mock_reach = create_autospec(ReachLegacy)
        mock_reach.name = "myReach"
        mock_reach.normal_width = 340
        mock_reach.qstagnant = 800
        mock_reach.proprate_high = 3.65
        mock_reach.proprate_low = 0.89

        mock_reach.qfit = (800, 1280)
        mock_reach.qlevels = (1000, 2000, 3000, 4000)
        mock_reach.dq = (1000.0, 1000.0)
        mock_reach.qmin = 1000

        mock_branch = create_autospec(spec=Branch)
        mock_branch.name = "myBranch"
        mock_branch.reaches = [mock_reach]
        mock_branch.get_reach.return_value = mock_reach

        rivers = create_autospec(spec=RiversObject)
        rivers.branches = [mock_branch]
        # Set the return value of the 'get_branch' method
        rivers.get_branch.return_value = mock_branch       
        return rivers

    @pytest.fixture
    def config(self):
        return  ConfigParser()

    def given_version_1_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        assert not configuration_checker.check_configuration(rivers, config)
    
    def given_general_section_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section(config)
    
        assert not configuration_checker.check_configuration(rivers, config)

    def given_general_section_with_qthreshold_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section(config)
        config.set("General", "Qthreshold", "100")

        assert not configuration_checker.check_configuration(rivers, config)

    def given_general_section_with_qthreshold_and_qbankfull_when_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)

        assert not configuration_checker.check_configuration(rivers, config)

    def given_q_sections_with_discharge_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        self.add_q_section_waqua(config)

        assert not configuration_checker.check_configuration(rivers, config)

    def given_mode_specific_test_with_discharge_check_configuration_then_return_true(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        self.add_q_section_fm(config)
        config.set("General", "mode", "test")

        assert not configuration_checker.check_configuration(rivers, config)
    
    def given_mode_DFLOWFM_MAP_with_discharge_check_configuration_then_return_true(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        self.add_q_section_fm(config)
        config.set("General", "mode", DFLOWFM_MAP)

        assert configuration_checker.check_configuration(rivers, config)
    
    def given_mode_DFLOWFM_MAP_with_empty_discharge_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        config.set("General", "mode", DFLOWFM_MAP)
        config.add_section("Q2")
        config.set("Q2", "Discharge", "")
        
        assert not configuration_checker.check_configuration(rivers, config)
    
    def given_mode_DFLOWFM_MAP_with_valid_discharge_check_with_valid_reference_check_but_with_invalid_with_measure_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        config.set("General", "mode", DFLOWFM_MAP)
        config.add_section("Q2")
        config.set("Q2", "Discharge", "80.1")
        config.set("Q2", "Reference", "my_file.nc")
        
        assert not configuration_checker.check_configuration(rivers, config)
    
    def given_mode_WAQUA_export_with_discharge_check_configuration_then_return_true(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        self.add_q_section_waqua(config)
        config.set("General", "mode", WAQUA_EXPORT)

        assert configuration_checker.check_configuration(rivers, config)

    def given_mode_WAQUA_export_without_discharge_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        config.set("General", "mode", WAQUA_EXPORT)

        assert not configuration_checker.check_configuration(rivers, config)
    
    def given_mode_WAQUA_export_with_empty_discharge_check_configuration_then_return_false(self, configuration_checker: ConfigurationCheckerLegacy, rivers : RiversObject, config : ConfigParser):
        self.set_valid_general_section_with_q_values(config)
        config.set("General", "mode", WAQUA_EXPORT)
        config.add_section("Q2")
        config.set("Q2", "Discharge", "")
        
        assert not configuration_checker.check_configuration(rivers, config)

    def set_valid_general_section(self, config : ConfigParser):
        config.add_section("General")
        config.set("General", "Version", "1.0")
        config.set("General", "Branch", "myBranch")
        config.set("General", "Reach", 'myReach')

    def set_valid_general_section_with_q_values(self, config : ConfigParser):
        self.set_valid_general_section(config)
        config.set("General", "Qthreshold", "100")
        config.set("General", "Qbankfull", "100")

    def add_q_section_waqua(self, config : ConfigParser):
        config.add_section("Q1")
        config.set("Q1", "Discharge", "1300.0")
        config.add_section("Q2")
        config.set("Q2", "Discharge", "1300.0")
        config.add_section("Q3")
        config.set("Q3", "Discharge", "1300.0")
    
    def add_q_section_fm(self, config : ConfigParser):
        config.add_section("Q1")
        config.set("Q1", "Discharge", "1300.0")
        config.set("Q1", "Reference", "")
        config.set("Q1", "WithMeasure", "")
        config.add_section("Q2")
        config.set("Q2", "Discharge", "1300.0")
        config.set("Q2", "Reference", "")
        config.set("Q2", "WithMeasure", "")
        config.add_section("Q3")
        config.set("Q3", "Discharge", "1300.0")
        config.set("Q3", "Reference", "")
        config.set("Q3", "WithMeasure", "")
        