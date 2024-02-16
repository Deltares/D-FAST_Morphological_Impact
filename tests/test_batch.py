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
    
    @pytest.mark.parametrize("vector_data, expected_non_empty_discharges_count", [
        ([0.123, None, 0.456, 0.789, None], 3),
        ([0.123, 0.123, 0.456, 0.789, 0.123], 5),
        ([None, None, None, None, None], 0),
    ])    
    def given_vector_with_discharges_when_countq_then_return_amount_of_non_empty_discharges(self, vector_data: Vector, expected_non_empty_discharges_count: int):
        assert dfastmi.batch.countQ(vector_data) == expected_non_empty_discharges_count
        