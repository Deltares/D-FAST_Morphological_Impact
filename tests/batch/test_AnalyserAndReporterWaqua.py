from unittest.mock import patch
import pytest
import numpy
from dfastmi.batch.AnalyserAndReporterWaqua import ReporterWaqua, OutputDataWaqua
from dfastmi.batch.AnalyserAndReporterWaqua import AnalyserWaqua
        
class Test_ReporterWaqua():
    def given_output_data_and_mocked_write_files_when_write_report_then_expect_3_calls_for_writing_report(self):
        reporter = ReporterWaqua("filepath")
        firstm = 0
        firstn = 0
        data_zgem = numpy.array([1, 2, 3, 4, 5])
        data_zmax = numpy.array([1, 2, 3, 4, 5])
        data_zmin = numpy.array([1, 2, 3, 4, 5])
        output_data = OutputDataWaqua(firstm, firstn, data_zgem, data_zmax, data_zmin)
        with patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.get_filename') as mocked_get_file_name,\
        patch('dfastmi.batch.AnalyserAndReporterWaqua.DataTextFileOperations.write_simona_box') as mocked_write_simona_box:
            
            mocked_get_file_name.return_value = "filename.file"
            mocked_get_file_name.side_effect = "file.file"
    
            reporter.write_report(output_data)
            
            assert mocked_write_simona_box.call_count == 3
            assert mocked_get_file_name.call_count == 3

class Test_AnalyserWaqua():
    
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
    def given_data_and_mocked_classes_with_missing_file_location_when_analyse_then_return_success_and_empty_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        tstag = 0.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        report = False
        waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)

        with patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.log_text'), \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.get_text') as mocked_get_text, \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.DataTextFileOperations.read_waqua_xyz') as mocked_read_waqua_xyz, \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.dfastmi.kernel.core.dzq_from_du_and_h') as mocked_dzq_from_du_and_h:
            
            mocked_get_text.return_value="description"
            mocked_read_waqua_xyz.return_value=numpy.array([1, 2, 3, 4, 5])
            mocked_dzq_from_du_and_h.return_value=numpy.array([1, 2, 3, 4, 5])

            success, output_data = waqua.analyse(fraction_of_year, rsigma)

        assert success
        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.firstm == 0
        assert output_data.firstn == 0
        
        
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
    def given_data_and_mocked_classes_when_analyse_then_return_success_and_expected_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        tstag = 0.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        report = False
        waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)

        with patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.log_text'), \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.get_text') as mocked_get_text, \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.DataTextFileOperations.read_waqua_xyz') as mocked_read_waqua_xyz, \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.dfastmi.kernel.core.dzq_from_du_and_h'), \
        patch('dfastmi.batch.AnalyserAndReporterWaqua.os.path.isfile') as mocked_isfile:
            
            self.setup_mocks(mocked_get_text, mocked_read_waqua_xyz, mocked_isfile)

            success, output_data = waqua.analyse(fraction_of_year, rsigma)

        assert success
        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.firstm == 0
        assert output_data.firstn == 0
        
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
    def given_data_and_mocked_classes_with_tstag_above_zero_when_analyse_then_return_success_and_expected_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        tstag = 1.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        report = False
        waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)

        with patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.log_text'), \
            patch('dfastmi.batch.AnalyserAndReporterWaqua.ApplicationSettingsHelper.get_text') as mocked_get_text, \
            patch('dfastmi.batch.AnalyserAndReporterWaqua.DataTextFileOperations.read_waqua_xyz') as mocked_read_waqua_xyz, \
            patch('dfastmi.batch.AnalyserAndReporterWaqua.dfastmi.kernel.core.dzq_from_du_and_h'), \
            patch('dfastmi.batch.AnalyserAndReporterWaqua.os.path.isfile') as mocked_isfile:
                
                self.setup_mocks(mocked_get_text, mocked_read_waqua_xyz, mocked_isfile)

                success, output_data = waqua.analyse(fraction_of_year, rsigma)

        assert success
        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.firstm == 0
        assert output_data.firstn == 0
        
    def setup_mocks(self, mocked_get_text, mocked_read_waqua_xyz, mocked_isfile):
        mocked_isfile.return_value = True
        mocked_get_text.return_value = "description"
            
        def custom_side_effect(*args, **kwargs):
            if "xyz_velocity-zeta.001." in args[0]:
                return numpy.array([[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]])
            else:
                return numpy.array([1, 1, 1])

        mocked_read_waqua_xyz.side_effect = custom_side_effect