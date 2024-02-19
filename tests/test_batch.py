import os
import sys
import netCDF4
import pytest
import context
import dfastmi.batch

from contextlib import contextmanager
from io import StringIO
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.Reach import ReachAdvanced
from dfastmi.io.CelerObject import CelerProperties, CelerDischarge
from dfastmi.kernel.typehints import Vector
from configparser import ConfigParser

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_batch_mode():
    def test_batch_mode_00(self):
        """
        Testing batch_mode: missing configuration file.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        with captured_output() as (out, err):
            dfastmi.batch.batch_mode("config.cfg", rivers, False)
        outstr = out.getvalue().splitlines()
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == ["[Errno 2] No such file or directory: 'config.cfg'"]

    def test_batch_mode_01(self):
        """
        Testing batch_mode: running configuration file - Dutch report.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("c01.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = ('Dit is versie')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "verslag.run", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_verslag.run", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "jaargem.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "maxmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "minmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_batch_mode_02(self):
        """
        Testing batch_mode: running configuration file - English report.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("c01.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = ('This is version')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "yearavg_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "max_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "min_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_batch_mode_03(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        Version 1 configuration files.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("Qmin_4000.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        self.maxDiff = None
        print(outstr)
        assert outstr == []
        #
        prefixes = ('This is version')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(refdir + os.sep + "report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        ncRes = netCDF4.Dataset(tstdir + os.sep + "output" + os.sep + "dfastmi_results.nc")
        ncRef = netCDF4.Dataset(refdir + os.sep + "dfastmi_results.nc")
        
        fields = ["avgdzb", "mindzb", "maxdzb"]
        for f in fields:
            result = ncRes.variables[f]
            refdat = ncRef.variables[f]
            assert (result[...] == refdat[...]).all()

    def test_batch_mode_04(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        Version 2 configuration files ... special backward consistent river configuration.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000"
        try:
            os.chdir(tstdir)
            rivers = RiversObject("rivers_Q4000_v2.ini")
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("Qmin_4000_v2.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        self.maxDiff = None
        print(outstr)
        assert outstr == []
        #
        prefixes = ('This is version')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(refdir + os.sep + "report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        ncRes = netCDF4.Dataset(tstdir + os.sep + "output" + os.sep + "dfastmi_results.nc")
        ncRef = netCDF4.Dataset(refdir + os.sep + "dfastmi_results.nc")
        
        fields = ["avgdzb", "mindzb", "maxdzb"]
        for f in fields:
            result = ncRes.variables[f]
            refdat = ncRef.variables[f]
            assert (result[...] == refdat[...]).all()

    def given_configuration_file_version_different_as_river_file_version_when_running_batch_mode_core_then_throw_exception_version_mis_match(self):
        """
        Testing is exception is thrown correctly when version number in configuration file mismatches with the river configuration file
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")            
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            config_file = "Qmin_4000_v2.cfg"
            config = dfastmi.batch.load_configuration_file(config_file)
            rootdir = os.path.dirname(config_file)
            with pytest.raises(Exception) as cm:
                dfastmi.batch.batch_mode_core(rivers, False, config, rootdir)
            assert str(cm.value) == 'Version number of configuration file (2.0) must match version number of rivers file (1.0)'
        finally:
            os.chdir(cwd)
            
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
        
        dfastmi.batch.save_configuration_file(file_path, config)
        
        assert os.path.exists(file_path)
        with open(file_path, 'r') as file:
            file_lines = file.readlines()
            
        assert len(file_lines) == len(expected_lines)
        assert file_lines == expected_lines
        
    def sample_config(self, tmp_path):
        # Create a sample configuration
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
    
class Test_batch_countq():       
    @pytest.mark.parametrize("vector_data, expected_non_empty_discharges_count", [
        ([0.123, None, 0.456, 0.789, None], 3),
        ([0.123, 0.123, 0.456, 0.789, 0.123], 5),
        ([None, None, None, None, None], 0),
    ])    
    def given_vector_with_discharges_when_countq_then_return_amount_of_non_empty_discharges(self, vector_data: Vector, expected_non_empty_discharges_count: int):
        assert dfastmi.batch.countQ(vector_data) == expected_non_empty_discharges_count
 
class Test_batch_write_report():   
    @pytest.mark.parametrize("slength", [
        0.202122,
        1.202122
    ])       
    def given_input_data_with_varying_slength_when_write_report_then_expect_messages_written_in_report(self, slength :float):
        report = StringIO()
        reach = "reach"
        q_location = "location"
        q_threshold = 0.123
        q_bankfull = 0.456
        q_stagnant = 0.789
        tstag = 0.101112
        q_fit = [0.131415, 0.171819]
        Q = [0.232425, 0.262728, 0.293031]
        T = [0.323334, 0.353637, 0.383940]
        
        ApplicationSettingsHelper.PROGTEXTS.clear()
        
        dfastmi.batch.write_report(report, reach, q_location, q_threshold, q_bankfull, q_stagnant, tstag, q_fit, Q, T, slength)

        report_lines = report.getvalue().split('\n')
                
        prefix = 'No message found for '
        assert prefix + 'reach' in report_lines
        assert prefix + 'report_qthreshold' in report_lines
        assert prefix + 'report_qbankfull' in report_lines
        assert prefix + 'closed_barriers' in report_lines
        assert prefix + 'char_discharge' in report_lines
        assert report_lines.count(prefix + 'char_discharge') is 3
        assert prefix + 'char_period' in report_lines
        assert report_lines.count(prefix + 'char_period') is 3
        assert prefix + 'need_multiple_input' in report_lines
        assert prefix + 'lowwater' in report_lines
        assert prefix + 'transition' in report_lines
        assert prefix + 'highwater' in report_lines
        assert prefix + 'length_estimate' in report_lines
        assert prefix + 'prepare_input' in report_lines
        
class Test_batch_check_configuration():
    
    def given_version_when_check_configuration_then_return_false(self):
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        config = ConfigParser()
        
        assert dfastmi.batch.check_configuration(rivers, config) is False
        
    def given_version_with_no_matching_version_when_check_configuration_then_return_false(self):
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        config = ConfigParser()
        
        config.add_section("General")
        config.set("General", "Version", "0.0")
        
        assert dfastmi.batch.check_configuration(rivers, config) is False
    
    class Test_check_configuration_v1():
        @pytest.fixture
        def rivers(self):
            return  RiversObject("dfastmi/Dutch_rivers_v1.ini")
        
        @pytest.fixture
        def config(self):
            return  ConfigParser()
                    
        def given_version_1_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_general_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "1.0")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_general_section_with_qthreshold_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "1.0")
            config.set("General", "Qthreshold", "100")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_general_section_with_qthreshold_and_qbankfull_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section_with_q_values(config, "1.0")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_q_sections_with_discharge_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):           
            self.set_valid_general_section_with_q_values(config, "1.0")
            self.add_q_section(config)
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_mode_specific_test_with_discharge_check_configuration_then_return_true(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section_with_q_values(config, "1.0")
            self.add_q_section(config)
            config.set("General", "mode", "test")
            
            assert dfastmi.batch.check_configuration(rivers, config) is True
            
        def set_valid_general_section(self, config : ConfigParser, version : str):
            config.add_section("General")
            config.set("General", "Version", version)
            config.set("General", "Branch", "Bovenrijn & Waal")
            config.set("General", "Reach", 'Bovenrijn                    km  859-867')
            
        def set_valid_general_section_with_q_values(self, config : ConfigParser, version : str):
            self.set_valid_general_section(config, version)
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
            return  ConfigParser()
        
        def given_version_2_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            assert dfastmi.batch.check_configuration(rivers, config) is False
        
        def given_general_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "2.0")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_general_section_and_c_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "2.0")
            config.add_section("C1")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_only_discharge_in_c_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "2.0")
            config.add_section("C1")
            config.set("C1", "Discharge", "1300.0")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False
            
        def given_partial_c_section_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "2.0")
            config.add_section("C1")
            config.set("C1", "Discharge", "1300.0")
            config.set("C1", "Reference", "1300.0")
            
            assert dfastmi.batch.check_configuration(rivers, config) is False

        def given_c_sections_with_incorrect_values_when_check_configuration_then_return_false(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "2.0")
            self.add_c_section(config, "C1", "1300.0")
            self.add_c_section(config, "C2", "1300.0")
            self.add_c_section(config, "C3", "1300.0")
            self.add_c_section(config, "C4", "1300.0")
            self.add_c_section(config, "C5", "1300.0")
            self.add_c_section(config, "C6", "1300.0")
                
            assert dfastmi.batch.check_configuration(rivers, config) is False        
                
        def given_correct_c_sections_when_check_configuration_then_return_true(self, rivers : RiversObject, config : ConfigParser):
            self.set_valid_general_section(config, "2.0")
            self.add_c_section(config, "C1", "1300.0")
            self.add_c_section(config, "C2", "2000.0")
            self.add_c_section(config, "C3", "3000.0")
            self.add_c_section(config, "C4", "4000.0")
            self.add_c_section(config, "C5", "6000.0")
            self.add_c_section(config, "C6", "8000.0")
                
            assert dfastmi.batch.check_configuration(rivers, config) is True
        
        def set_valid_general_section(self, config : ConfigParser, version : str):
            config.add_section("General")
            config.set("General", "Version", version)
            config.set("General", "Branch", "Bovenrijn & Waal")
            config.set("General", "Reach", 'Bovenrijn                    km  859-867')
            
        def add_c_section(self, config: ConfigParser, name: str, value : str):
            config.add_section(name)
            config.set(name, "Discharge",   value)
            config.set(name, "Reference",   value)
            config.set(name, "WithMeasure", value)
            
    class Test_get_levels_v2():
    
        @pytest.fixture    
        def reach(self):
            reach = ReachAdvanced()
            reach.hydro_q = [6.7, 8.9, 10.1]
            reach.autotime = True
            reach.qfit = [11.11, 12.12]
            reach.celer_form = 1
            reach.celer_object = CelerProperties()
            reach.celer_object.prop_q = [13.13, 14.14]
            reach.celer_object.prop_c = [15.13, 16.14]
            return reach

        def given_auto_time_true_when_get_levels_v2_then_return_expected_values(self, reach : ReachAdvanced):
            reach.qstagnant = 4.5
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, time_mi, tstag, T, rsigma, celerity = dfastmi.batch.get_levels_v2(reach, q_threshold, nwidth)

            assert Q == [6.7, 8.9, 10.1]
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 0.0, 1.0)
            assert tstag == 0
            assert T == (0.0, 0.0, 1.0)
            assert rsigma == (1.0, 1.0, 0.0)
            assert celerity == (15.13, 15.13, 15.13)

        def given_auto_time_true_with_qstagnant_above_one_Q_when_get_levels_v2_then_return_expected_values_with_one_celerity_zero(self, reach : ReachAdvanced):
            reach.qstagnant = 7.8
            q_threshold = 7.3
            nwidth = 3.4

            Q, apply_q, time_mi, tstag, T, rsigma, celerity = dfastmi.batch.get_levels_v2(reach, q_threshold, nwidth)

            assert Q == [6.7, 8.9, 10.1]
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 0.0, 1.0)
            assert tstag == 0
            assert T == (0.0, 0.0, 1.0)
            assert rsigma == (1.0, 1.0, 0.0)
            assert celerity == (0.0, 15.13, 15.13)

        def given_auto_time_true_with_multiple_qstagnant_above_Q_when_get_levels_v2_then_return_expected_values_with_multiple_celerity_zero(self, reach : ReachAdvanced):
            reach.qstagnant = 9.0
            q_threshold = 7.3
            nwidth = 3.4

            Q, apply_q, time_mi, tstag, T, rsigma, celerity = dfastmi.batch.get_levels_v2(reach, q_threshold, nwidth)

            assert Q == [6.7, 8.9, 10.1]
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 0.0, 1.0)
            assert tstag == 0
            assert T == (0.0, 0.0, 1.0)
            assert rsigma == (1.0, 1.0, 0.0)
            assert celerity == (0.0, 0.0, 15.13)
            
        def given_auto_time_false_when_get_levels_v2_then_return_expected_values(self, reach : ReachAdvanced):
            reach.qstagnant = 4.5
            reach.autotime = False
            reach.hydro_t = [0.0, 1.0, 0.0]
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, time_mi, tstag, T, rsigma, celerity = dfastmi.batch.get_levels_v2(reach, q_threshold, nwidth)

            assert Q == [6.7, 8.9, 10.1]
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 1.0, 0.0)
            assert tstag == 0
            assert T == (0.0, 1.0, 0.0)
            assert rsigma == (1.0, 0.0, 1.0)
            assert celerity == (15.13, 15.13, 15.13)
            
        def given_auto_time_false_and_celer_discharge_when_get_levels_v2_then_return_expected_values(self, reach : ReachAdvanced):
            reach.qstagnant = 4.5
            reach.autotime = False
            reach.celer_form = 2
            reach.celer_object = CelerDischarge()
            reach.celer_object.cdisch = [1.0, 1.0]
            reach.hydro_t = [0.0, 1.0, 0.0]
            q_threshold = 1.2
            nwidth = 3.4

            Q, apply_q, time_mi, tstag, T, rsigma, celerity = dfastmi.batch.get_levels_v2(reach, q_threshold, nwidth)

            assert Q == [6.7, 8.9, 10.1]
            assert apply_q == (True, True, True)
            assert time_mi == (0.0, 1.0, 0.0)
            assert tstag == 0
            assert T == (0.0, 1.0, 0.0)
            assert rsigma == (1.0, 0.0, 1.0)
            assert celerity == (6.7, 8.9, 10.1)