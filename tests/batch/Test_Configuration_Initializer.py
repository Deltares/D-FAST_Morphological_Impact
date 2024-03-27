from dfastmi.batch.ConfigurationInitializer import ConfigurationInitializer
from dfastmi.io.CelerObject import CelerDischarge, CelerProperties
from dfastmi.io.Reach import Reach


import pytest


from configparser import ConfigParser
from unittest.mock import create_autospec


class Test_Configuration_Initializer():
    @pytest.fixture
    def reach(self):
        mock_reach = create_autospec(Reach)
        mock_reach.name = "myReach"
        mock_reach.hydro_q = (6.7, 8.9, 10.1)
        mock_reach.use_tide = False
        mock_reach.auto_time = True
        mock_reach.qfit = [11.11, 12.12]
        mock_reach.celer_form = 1
        mock_reach.ucritical = 1
        mock_reach.normal_width = 3.4

        mock_reach.celer_object = CelerProperties()
        mock_reach.celer_object.prop_q = [13.13, 14.14]
        mock_reach.celer_object.prop_c = [15.13, 16.14]
        return mock_reach
    
    @pytest.fixture
    def config(self):
        config = ConfigParser()
        self.set_valid_general_section(config)
        return  config

    def set_valid_general_section(self, config : ConfigParser):
        config.add_section("General")
        config.set("General", "Version", "2.0")
        config.set("General", "Branch", "myBranch")
        config.set("General", "Reach", 'myReach')

    def given_auto_time_true_when_get_levels_v2_then_return_expected_values(self, config : ConfigParser, reach : Reach):
        reach.qstagnant = 4.5
        configuration_initialized = ConfigurationInitializer(reach, config)

        assert configuration_initialized.discharges == (6.7, 8.9, 10.1)
        assert configuration_initialized.apply_q == (True, True, True)
        assert configuration_initialized.time_mi == (0.0, 0.0, 1.0)
        assert configuration_initialized.tstag == 0
        assert configuration_initialized.time_fractions_of_the_year == (0.0, 0.0, 1.0)
        assert configuration_initialized.rsigma == (1.0, 1.0, 0.0)
        assert configuration_initialized.celerity == (15.13, 15.13, 15.13)

    def given_auto_time_true_when_get_levels_v2_then_return_values_have_expected_length(self, config : ConfigParser, reach : Reach):
        reach.qstagnant = 4.5
        configuration_initialized = ConfigurationInitializer(reach, config)

        assert len(configuration_initialized.discharges) == len(reach.hydro_q)
        assert len(configuration_initialized.apply_q) == len(reach.hydro_q)
        assert len(configuration_initialized.time_mi) == len(reach.hydro_q)
        assert configuration_initialized.tstag == 0
        assert len(configuration_initialized.time_fractions_of_the_year) == len(reach.hydro_q)
        assert len(configuration_initialized.rsigma) == len(reach.hydro_q)
        assert len(configuration_initialized.celerity) == len(reach.hydro_q)

    def given_auto_time_true_with_qstagnant_above_one_Q_when_get_levels_v2_then_return_expected_values_with_one_celerity_zero(self, config : ConfigParser, reach : Reach):
        reach.qstagnant = 7.8
        configuration_initialized = ConfigurationInitializer(reach, config)

        assert configuration_initialized.discharges == (6.7, 8.9, 10.1)
        assert configuration_initialized.apply_q == (True, True, True)
        assert configuration_initialized.time_mi == (0.0, 0.0, 1.0)
        assert configuration_initialized.tstag == 0
        assert configuration_initialized.time_fractions_of_the_year == (0.0, 0.0, 1.0)
        assert configuration_initialized.rsigma == (1.0, 1.0, 0.0)
        assert configuration_initialized.celerity == (0.0, 15.13, 15.13)

    def given_auto_time_true_with_multiple_qstagnant_above_Q_when_get_levels_v2_then_return_expected_values_with_multiple_celerity_zero(self, config : ConfigParser, reach : Reach):
        reach.qstagnant = 9.0
        configuration_initialized = ConfigurationInitializer(reach, config)

        assert configuration_initialized.discharges == (6.7, 8.9, 10.1)
        assert configuration_initialized.apply_q == (True, True, True)
        assert configuration_initialized.time_mi == (0.0, 0.0, 1.0)
        assert configuration_initialized.tstag == 0
        assert configuration_initialized.time_fractions_of_the_year == (0.0, 0.0, 1.0)
        assert configuration_initialized.rsigma == (1.0, 1.0, 0.0)
        assert configuration_initialized.celerity == (0.0, 0.0, 15.13)

    def given_auto_time_false_when_get_levels_v2_then_return_expected_values(self, config : ConfigParser, reach : Reach):
        reach.qstagnant = 4.5
        reach.auto_time = False
        reach.hydro_t = [0.0, 1.0, 0.0]

        configuration_initialized = ConfigurationInitializer(reach, config)

        assert configuration_initialized.discharges == (6.7, 8.9, 10.1)
        assert configuration_initialized.apply_q == (True, True, True)
        assert configuration_initialized.time_mi == (0.0, 1.0, 0.0)
        assert configuration_initialized.tstag == 0
        assert configuration_initialized.time_fractions_of_the_year == (0.0, 1.0, 0.0)
        assert configuration_initialized.rsigma == (1.0, 0.0, 1.0)
        assert configuration_initialized.celerity == (15.13, 15.13, 15.13)


    def given_auto_time_false_and_celer_discharge_when_get_levels_v2_then_return_expected_values(self, config : ConfigParser, reach : Reach):
        reach.qstagnant = 4.5
        reach.auto_time = False
        reach.celer_form = 2
        reach.celer_object = CelerDischarge()
        reach.celer_object.cdisch = [1.0, 1.0]
        reach.hydro_t = [0.0, 1.0, 0.0]
        
        configuration_initialized = ConfigurationInitializer(reach, config)

        assert configuration_initialized.discharges == (6.7, 8.9, 10.1)
        assert configuration_initialized.apply_q == (True, True, True)
        assert configuration_initialized.time_mi == (0.0, 1.0, 0.0)
        assert configuration_initialized.tstag == 0
        assert configuration_initialized.time_fractions_of_the_year == (0.0, 1.0, 0.0)
        assert configuration_initialized.rsigma == (1.0, 0.0, 1.0)
        assert configuration_initialized.celerity == (6.7, 8.9, 10.1)
