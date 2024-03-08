from unittest.mock import create_autospec, patch
from pathlib import Path
from configparser import ConfigParser
import pytest

from dfastmi.io.Branch import Branch
from dfastmi.batch.ConfigurationChecker import ConfigurationChecker
from dfastmi.io.CelerObject import CelerDischarge, CelerProperties
from dfastmi.io.Reach import Reach

from dfastmi.io.RiversObject import RiversObject

class Test_configuration_checker():
    @pytest.fixture
    def configuration_checker(self):
        return ConfigurationChecker()
    
    @pytest.fixture
    def rivers(self):
        mock_reach = create_autospec(Reach)
        mock_reach.name = "myReach1"
        mock_reach.hydro_q = (80.1, 80.2)        

        mock_branch = create_autospec(Branch)
        mock_branch.name = "myBranch"
        mock_branch.reaches = [mock_reach]
        mock_branch.get_reach.return_value = None

        rivers = create_autospec(RiversObject)
        rivers.branches = [mock_branch]
        # Set the return value of the 'get_branch' method
        rivers.get_branch.return_value = mock_branch       

        return rivers

    @pytest.fixture
    def config(self):
        config = ConfigParser()
        self.set_valid_general_section(config)
        return  config

    def given_correct_branch_but_invalid_reach_when_get_reach_then_throw_lookup_exception(self, configuration_checker: ConfigurationChecker, rivers : RiversObject, config : ConfigParser):
        with pytest.raises(LookupError) as cm:
            configuration_checker._get_reach(rivers, config, Reach)
        assert str(cm.value) == "Reach not in file myReach!"

    def set_valid_general_section(self, config : ConfigParser):
        config.add_section("General")
        config.set("General", "Version", "2.0")
        config.set("General", "Branch", "myBranch")
        config.set("General", "Reach", 'myReach')

    class Test_check_configuration():
        @pytest.fixture
        def rivers(self):
            mock_reach = create_autospec(Reach)
            mock_reach.name = "myReach"
            mock_reach.hydro_q = (80.1, 80.2)
            mock_reach.qstagnant = 80.1

            mock_branch = create_autospec(Branch)
            mock_branch.name = "myBranch"
            mock_branch.reaches = [mock_reach]

            # Set the return value of the 'get_reach' method
            mock_branch.get_reach.return_value = mock_reach

            rivers = create_autospec(RiversObject)
            rivers.branches = [mock_branch]
            # Set the return value of the 'get_branch' method
            rivers.get_branch.return_value = mock_branch       

            return rivers        

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
            with patch.object(Path, 'exists') as mock_exists:
                mock_exists.return_value = True
                assert configuration_checker.check_configuration(rivers, config)

        # def set_valid_general_section(self, config : ConfigParser):
        #     config.add_section("General")
        #     config.set("General", "Version", "2.0")
        #     config.set("General", "Branch", "myBranch")
        #     config.set("General", "Reach", 'myReach')

        def add_c_section(self, config: ConfigParser, name: str, value : str):
            config.add_section(name)
            config.set(name, "Discharge",   value)
            config.set(name, "Reference",   value)
            config.set(name, "WithMeasure", value)

    class Test_get_levels():
        @pytest.fixture    
        def reach(self):
            mock_reach = create_autospec(Reach)
            mock_reach.name = "myReach"
            mock_reach.hydro_q = (6.7, 8.9, 10.1)
            mock_reach.use_tide = False
            mock_reach.autotime = True
            mock_reach.qfit = [11.11, 12.12]
            mock_reach.celer_form = 1

            mock_reach.celer_object = CelerProperties()
            mock_reach.celer_object.prop_q = [13.13, 14.14]
            mock_reach.celer_object.prop_c = [15.13, 16.14]
            return mock_reach
        
        def given_auto_time_true_when_get_levels_v2_then_return_expected_values(self, configuration_checker: ConfigurationChecker, config : ConfigParser, reach : Reach):
            reach.qstagnant = 4.5
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, _, _ = configuration_checker.get_levels(reach, config, nwidth)

            assert Q == (6.7, 8.9, 10.1)
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 0.0, 1.0)
            assert tstag == 0
            assert T == (0.0, 0.0, 1.0)
            assert rsigma == (1.0, 1.0, 0.0)
            assert celerity == (15.13, 15.13, 15.13)
            
        def given_auto_time_true_when_get_levels_v2_then_return_values_have_expected_length(self, configuration_checker: ConfigurationChecker, config : ConfigParser, reach : Reach):
            reach.qstagnant = 4.5
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, _, _ = configuration_checker.get_levels(reach, config, nwidth)

            assert len(Q) == len(reach.hydro_q)
            assert len(apply_q) == len(reach.hydro_q)
            assert len(time_mi) == len(reach.hydro_q)
            assert tstag == 0
            assert len(T) == len(reach.hydro_q)
            assert len(rsigma) == len(reach.hydro_q)
            assert len(celerity) == len(reach.hydro_q)

        def given_auto_time_true_with_qstagnant_above_one_Q_when_get_levels_v2_then_return_expected_values_with_one_celerity_zero(self, configuration_checker: ConfigurationChecker, config : ConfigParser, reach : Reach):
            reach.qstagnant = 7.8
            q_threshold = 7.3
            nwidth = 3.4

            Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, _, _ = configuration_checker.get_levels(reach, config, nwidth)

            assert Q == (6.7, 8.9, 10.1)
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 0.0, 1.0)
            assert tstag == 0
            assert T == (0.0, 0.0, 1.0)
            assert rsigma == (1.0, 1.0, 0.0)
            assert celerity == (0.0, 15.13, 15.13)

        def given_auto_time_true_with_multiple_qstagnant_above_Q_when_get_levels_v2_then_return_expected_values_with_multiple_celerity_zero(self, configuration_checker: ConfigurationChecker, config : ConfigParser, reach : Reach):
            reach.qstagnant = 9.0
            q_threshold = 7.3
            nwidth = 3.4

            Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, _, _ = configuration_checker.get_levels(reach, config, nwidth)

            assert Q == (6.7, 8.9, 10.1)
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 0.0, 1.0)
            assert tstag == 0
            assert T == (0.0, 0.0, 1.0)
            assert rsigma == (1.0, 1.0, 0.0)
            assert celerity == (0.0, 0.0, 15.13)
            
        def given_auto_time_false_when_get_levels_v2_then_return_expected_values(self, configuration_checker: ConfigurationChecker, config : ConfigParser, reach : Reach):
            reach.qstagnant = 4.5
            reach.autotime = False
            reach.hydro_t = [0.0, 1.0, 0.0]
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, _, _ = configuration_checker.get_levels(reach, config, nwidth)

            assert Q == (6.7, 8.9, 10.1)
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 1.0, 0.0)
            assert tstag == 0
            assert T == (0.0, 1.0, 0.0)
            assert rsigma == (1.0, 0.0, 1.0)
            assert celerity == (15.13, 15.13, 15.13)
            
        def given_auto_time_false_and_celer_discharge_when_get_levels_v2_then_return_expected_values(self, configuration_checker: ConfigurationChecker, config : ConfigParser, reach : Reach):
            reach.qstagnant = 4.5
            reach.autotime = False
            reach.celer_form = 2
            reach.celer_object = CelerDischarge()
            reach.celer_object.cdisch = [1.0, 1.0]
            reach.hydro_t = [0.0, 1.0, 0.0]
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, _, _ = configuration_checker.get_levels(reach, config, nwidth)

            assert Q == (6.7, 8.9, 10.1)
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 1.0, 0.0)
            assert tstag == 0
            assert T == (0.0, 1.0, 0.0)
            assert rsigma == (1.0, 0.0, 1.0)
            assert celerity == (6.7, 8.9, 10.1)