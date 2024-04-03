import os

import pytest

from dfastmi.batch.AnalyserAndReporterWaqua import analyse_and_report_waqua
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper


class Test_analyse_and_report_waqua_mode:
    def setup_and_execute_analyse_and_report_waqua(
        self, tmp_path, display, reduced_output, old_zmin_zmax, tstag
    ):
        Q = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = tmp_path

        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            succes = analyse_and_report_waqua(
                display,
                None,
                reduced_output,
                tstag,
                Q,
                apply_q,
                T,
                rsigma,
                ucrit,
                old_zmin_zmax,
                outputdir,
            )
        finally:
            os.chdir(cwd)
        return succes

    @pytest.mark.parametrize(
        "display, reduced_output, old_zmin_zmax",
        [
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
            (False, True, False),
            (False, True, True),
            (False, False, True),
            (True, False, True),
        ],
    )
    def given_varying_boolean_inputs_with_tstag_zero_when_analyse_and_report_waqua_then_return_expected_succes(
        self, tmp_path, display: bool, reduced_output: bool, old_zmin_zmax: bool
    ):
        """
        given : varying boolean inputs with tstag zero
        when :  analyse and report waqua
        then  : return expected succes
        """

        tstag = 0.0

        succes = self.setup_and_execute_analyse_and_report_waqua(
            tmp_path, display, reduced_output, old_zmin_zmax, tstag
        )

        assert succes

        files_in_tmp = os.listdir(tmp_path)
        assert "jaargem.out" in files_in_tmp
        assert "maxmorf.out" in files_in_tmp
        assert "minmorf.out" in files_in_tmp

    @pytest.mark.parametrize(
        "display, reduced_output, old_zmin_zmax",
        [
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
            (False, True, False),
            (False, True, True),
            (False, False, True),
            (True, False, True),
        ],
    )
    def given_varying_boolean_inputs_with_tstag_above_zero_when_analyse_and_report_waqua_then_return_expected_succes(
        self, tmp_path, display: bool, reduced_output: bool, old_zmin_zmax: bool
    ):
        """
        given : varying boolean inputs with tstag above zero
        when :  analyse and report waqua
        then  : return expected succes
        """
        tstag = 1.0

        succes = self.setup_and_execute_analyse_and_report_waqua(
            tmp_path, display, reduced_output, old_zmin_zmax, tstag
        )

        assert succes

        files_in_tmp = os.listdir(tmp_path)
        assert "jaargem.out" in files_in_tmp
        assert "maxmorf.out" in files_in_tmp
        assert "minmorf.out" in files_in_tmp
