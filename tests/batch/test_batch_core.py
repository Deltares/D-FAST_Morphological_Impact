import os
import sys
from contextlib import contextmanager
from io import StringIO

import netCDF4
import numpy as np
import pytest

import dfastmi.batch.core
from dfastmi.config.ConfigFileOperations import ConfigFileOperations
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import Vector


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def compare_text_files(dir1, dir2, file1, file2=None, prefixes=None):
    result = open(dir1 + os.sep + file1, "r").read().splitlines()
    if file2 is None:
        file2 = file1
    refstr = open(dir2 + os.sep + file2, "r").read().splitlines()
    if not prefixes is None:
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
    assert result == refstr


def compare_netcdf_fields(dir1, dir2, file, fields, tol=1e-8):
    ncRes = netCDF4.Dataset(dir1 + os.sep + file)
    ncRef = netCDF4.Dataset(dir2 + os.sep + file)
    for f in fields:
        result = ncRes.variables[f][...]
        refdat = ncRef.variables[f][...]

        if not np.allclose(result, refdat, atol=tol, equal_nan=True):
            diff = np.abs(result - refdat)
            max_diff = np.nanmax(diff)
            raise AssertionError(
                f"Field '{f}' differs between files. Max difference: {max_diff} exceeds tolerance {tol}."
            )
    ncRes.close()
    ncRef.close()


class Test_batch_mode:
    def test_batch_mode_00(self):
        """
        Testing batch_mode: missing configuration file.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        with captured_output() as (out, err):
            dfastmi.batch.core.batch_mode("config.cfg", rivers, False)
        outstr = out.getvalue().splitlines()
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == ["[Errno 2] No such file or directory: 'config.cfg'"]

    @pytest.mark.parametrize(
        "tstdir, cfgfile",
        [
            ("tests/c01 - GendtseWaardNevengeul", "c01.cfg"),
            ("tests/c02 - DeLymen", "c02.cfg"),
        ],
    )
    def test_batch_mode_01(self, tstdir, cfgfile):
        """
        Testing batch_mode: running configuration file - Dutch report.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        outdir = tstdir + os.sep + "output"
        refdir = tstdir
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode(cfgfile, rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        compare_text_files(
            outdir, refdir, "verslag.run", "ref_verslag.run", prefixes=("Dit is versie")
        )
        #
        compare_text_files(outdir, refdir, "jaargem.out", "ref_jaargem.out")
        compare_text_files(outdir, refdir, "maxmorf.out", "ref_maxmorf.out")
        compare_text_files(outdir, refdir, "minmorf.out", "ref_minmorf.out")

    def test_batch_mode_02(self):
        """
        Testing batch_mode: running configuration file - English report.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        outdir = tstdir + os.sep + "output"
        refdir = tstdir
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode("c01.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        compare_text_files(
            outdir, refdir, "report.txt", "ref_report.txt", prefixes=("This is version")
        )
        #
        compare_text_files(outdir, refdir, "yearavg_dzb.out", "ref_jaargem.out")
        compare_text_files(outdir, refdir, "max_dzb.out", "ref_maxmorf.out")
        compare_text_files(outdir, refdir, "min_dzb.out", "ref_minmorf.out")

    def test_batch_mode_03(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        Version 1 configuration files.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        outdir = tstdir + os.sep + "output"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode("Qmin_4000.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        self.maxDiff = None
        print(outstr)
        assert outstr == []
        #
        compare_text_files(outdir, refdir, "report.txt", prefixes=("This is version"))
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "dfastmi_results.nc",
            ["mesh2d_node_x", "mesh2d_node_y", "avgdzb", "mindzb", "maxdzb"],
        )

    def test_batch_mode_04(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        Version 2 configuration files ... special backward consistent river configuration.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        outdir = tstdir + os.sep + "output"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000_special_backward_case"
        try:
            os.chdir(tstdir)
            rivers = RiversObject("rivers_Q4000_v2.ini")
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode("Qmin_4000_v2.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        self.maxDiff = None
        print(outstr)
        assert outstr == []
        #
        compare_text_files(outdir, refdir, "report.txt", prefixes=("This is version"))
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "dfastmi_results.nc",
            ["mesh2d_node_x", "mesh2d_node_y", "avgdzb", "mindzb", "maxdzb"],
        )

    def test_batch_mode_05(self):
        """
        Same as test_batch_mode_04 but includes centreline snapping.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        outdir = tstdir + os.sep + "output_rkm"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000_rkm"
        try:
            os.chdir(tstdir)
            rivers = RiversObject("rivers_Q4000_v2.ini")
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode("Qmin_4000_v2_rkm.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)

        compare_text_files(outdir, refdir, "report.txt", prefixes=("This is version"))

        compare_netcdf_fields(
            outdir,
            refdir,
            "dfastmi_results.nc",
            ["mesh2d_node_x", "mesh2d_node_y", "avgdzb", "mindzb", "maxdzb"],
        )

        compare_netcdf_fields(
            outdir,
            refdir,
            "projected_mesh.nc",
            ["mesh2d_node_x", "mesh2d_node_y", "avgdzb"],
        )
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "sedimentation_weights.nc",
            [
                "mesh2d_node_x",
                "mesh2d_node_y",
                "interest_region",
                "sed_area",
                "ero_area",
                "wght_estimate1",
                "wbin",
            ],
        )
        #
        compare_text_files(outdir, refdir, "sedimentation_volumes.xyz")

    def test_batch_mode_06(self):
        """
        Same as test_batch_mode_05 but sets Tide = True and uses 2 time steps.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        outdir = tstdir + os.sep + "output_tide"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000_rkm"
        try:
            os.chdir(tstdir)
            rivers = RiversObject("rivers_Q4000_v3_tide.ini")
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode("Qmin_4000_v3_tide.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        compare_text_files(outdir, refdir, "report.txt", prefixes=("This is version"))
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "dfastmi_results.nc",
            ["mesh2d_node_x", "mesh2d_node_y", "avgdzb", "mindzb", "maxdzb"],
        )
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "projected_mesh.nc",
            ["mesh2d_node_x", "mesh2d_node_y", "avgdzb"],
        )
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "sedimentation_weights.nc",
            [
                "mesh2d_node_x",
                "mesh2d_node_y",
                "interest_region",
                "sed_area",
                "ero_area",
                "wght_estimate1",
                "wbin",
            ],
        )
        #
        compare_text_files(outdir, refdir, "sedimentation_volumes.xyz")

    @pytest.mark.parametrize(
        "case, config",
        [
            ("01 - Palmerswaard", "example1.cfg"),
            ("02 - Pannerdensch Kanaal", "example2.cfg"),
            ("03 - Gendtse Waard", "GendtseWaard_v3.cfg"),
        ],
    )
    def test_batch_examples(self, case, config):
        """
        Testing batch_mode: example cases user manual
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v3.ini")
        cwd = os.getcwd()
        tstdir = "examples" + os.sep + case
        outdir = tstdir + os.sep + "output"
        refdir = "examples_references" + os.sep + case + os.sep + "output"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.core.batch_mode(config, rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        compare_text_files(outdir, refdir, "report.txt", prefixes=("This is version"))
        #
        compare_netcdf_fields(
            outdir,
            refdir,
            "dfastmi_results.nc",
            ["avgdzb", "mindzb", "maxdzb"],
        )

    def given_configuration_file_version_different_as_river_file_version_when_running_batch_mode_core_then_throw_exception_version_mis_match(
        self,
    ):
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
            config = ConfigFileOperations.load_configuration_file(config_file)
            rootdir = os.path.dirname(config_file)
            with pytest.raises(Exception) as cm:
                dfastmi.batch.core.batch_mode_core(rivers, False, config, rootdir)
            assert (
                str(cm.value)
                == "Version number of configuration file (2.0) must match version number of rivers file (1.0)"
            )
        finally:
            os.chdir(cwd)


class Test_batch_countq:
    @pytest.mark.parametrize(
        "vector_data, expected_true_flags_count",
        [
            ([True, False, True, True, False], 3),
            ([True, True, True, True, True], 5),
            ([False, False, False, False, False], 0),
        ],
    )
    def given_vector_with_flags_when_countq_then_return_expected_amount_of_true_flags(
        self, vector_data: Vector, expected_true_flags_count: int
    ):
        assert (
            dfastmi.batch.core.count_discharges(vector_data)
            == expected_true_flags_count
        )


class Test_batch_write_report:
    @pytest.mark.parametrize("slength", [0.2, 1.2])
    def given_input_data_with_varying_slength_when_write_report_then_expect_messages_written_in_report(
        self, slength: float
    ):
        report = StringIO()
        reach = "reach"
        q_location = "location"
        q_threshold = 0.1
        q_bankfull = 0.4
        q_stagnant = 0.7
        tstag = 0.1
        q_fit = [0.1, 0.1]
        Q = [0.2, 0.2, 0.2]
        apply_q = [True, True, True]
        T = [0.3, 0.3, 0.3]

        ApplicationSettingsHelper.PROGTEXTS = None

        dfastmi.batch.core.write_report(
            report,
            reach,
            q_location,
            q_threshold,
            q_bankfull,
            q_stagnant,
            tstag,
            q_fit,
            Q,
            apply_q,
            T,
            slength,
        )

        report_lines = report.getvalue().split("\n")

        prefix = "No message found for "
        assert prefix + "reach" in report_lines
        assert prefix + "report_qthreshold" in report_lines
        assert prefix + "report_qbankfull" in report_lines
        assert prefix + "closed_barriers" in report_lines
        assert prefix + "char_discharge" in report_lines
        assert report_lines.count(prefix + "char_discharge") == 3
        assert prefix + "char_period" in report_lines
        assert report_lines.count(prefix + "char_period") == 3
        assert prefix + "need_multiple_input" in report_lines
        assert prefix + "lowwater" in report_lines
        assert prefix + "transition" in report_lines
        assert prefix + "highwater" in report_lines
        assert prefix + "length_estimate" in report_lines
        assert prefix + "prepare_input" in report_lines
