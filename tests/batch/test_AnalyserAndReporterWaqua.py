from typing import Tuple
import os
import pytest
import numpy
from unittest.mock import MagicMock, patch
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.batch.AnalyserAndReporterWaqua import analyse_and_report_waqua
from dfastmi.batch.AnalyserAndReporterWaqua import ReporterWaqua, OutputDataWaqua
from dfastmi.batch.AnalyserAndReporterWaqua import AnalyzerWaqua
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
import dfastmi.kernel.core

class Test_analyse_and_report_waqua_mode():
    @pytest.mark.parametrize("display, reduced_output, old_zmin_zmax", [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (True, True, True),
        (False, True, False),
        (False, True, True),
        (False, False, True),
        (True, False, True),
    ])   
    def given_varying_boolean_inputs_with_tstag_zero_when_analyse_and_report_waqua_then_return_expected_succes(self, tmp_path, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        tstag = 0.0
        Q = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        
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
            outputdir)
        finally:
            os.chdir(cwd)

        assert succes
        
        files_in_tmp = os.listdir(tmp_path)
        assert "jaargem.out" in files_in_tmp
        assert "maxmorf.out" in files_in_tmp
        assert "minmorf.out" in files_in_tmp
        
    @pytest.mark.parametrize("display, reduced_output, old_zmin_zmax", [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (True, True, True),
        (False, True, False),
        (False, True, True),
        (False, False, True),
        (True, False, True),
    ])   
    def given_varying_boolean_inputs_with_tstag_above_zero_when_analyse_and_report_waqua_then_return_expected_succes(self, tmp_path, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        tstag = 1.0
        Q = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        
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
            outputdir)
        finally:
            os.chdir(cwd)

        assert succes
        
        files_in_tmp = os.listdir(tmp_path)
        assert "jaargem.out" in files_in_tmp
        assert "maxmorf.out" in files_in_tmp
        assert "minmorf.out" in files_in_tmp
        
class Test_ReporterWaqua():
    def given_output_data_and_mocked_write_files_when_write_report_then_expect_3_calls_for_writing_report(self):
        reporter = ReporterWaqua("filepath")
        firstm = 0
        firstn = 0
        data_zgem = numpy.array([1, 2, 3, 4, 5])
        data_zmax = numpy.array([1, 2, 3, 4, 5])
        data_zmin = numpy.array([1, 2, 3, 4, 5])
        output_data = OutputDataWaqua(firstm, firstn, data_zgem, data_zmax, data_zmin)
        with patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.get_filename') as mocked_get_file_name:
            with patch('dfastmi.batch.AnalyserAndReporterWaqua.DataTextFileOperations.write_simona_box') as mocked_write_simona_box:
                mocked_get_file_name.return_value = "filename.file"
                mocked_get_file_name.side_effect = "file.file"
        
                reporter.write_report(output_data)
                
                assert mocked_write_simona_box.call_count == 3
                assert mocked_get_file_name.call_count == 3

class Test_AnalyzerWaqua():
    
    @pytest.mark.parametrize("display, reduced_output, old_zmin_zmax", [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (True, True, True),
        (False, True, False),
        (False, True, True),
        (False, False, True),
        (True, False, True),
    ])   
    def given_data_and_mocked_classes_when_analyze_then_return_success_and_empty_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        tstag = 0.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        report = False
        waqua = AnalyzerWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)
        
        ApplicationSettingsHelper.log_text = MagicMock()
        ApplicationSettingsHelper.get_text = MagicMock(return_value = "description")
        DataTextFileOperations.read_waqua_xyz = MagicMock(return_value = numpy.array([1, 2, 3, 4, 5]))
        dfastmi.kernel.core.dzq_from_du_and_h = MagicMock(return_value = numpy.array([1, 2, 3, 4, 5]))

        success, output_data = waqua.analyze(fraction_of_year, rsigma)
        
        assert success
        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.firstm == 0
        assert output_data.firstn == 0
