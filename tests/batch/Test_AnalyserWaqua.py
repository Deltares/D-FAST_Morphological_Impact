from unittest.mock import patch
import numpy
import pytest
from dfastmi.batch.AnalyserWaqua import AnalyserWaqua

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
    def given_data_and_mocked_classes_with_missing_file_location_when_analyse_then_return_empty_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        """
        given : data and mocked classes with missing filelocation
        when :  analyse 
        then  : return empty output_data
        """
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]

        tstag = 0.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        ucrit = 0.3
        report = False
        waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)

        with patch('dfastmi.batch.AnalyserWaqua.ApplicationSettingsHelper.log_text'), \
        patch('dfastmi.batch.AnalyserWaqua.ApplicationSettingsHelper.get_text') as mocked_get_text, \
        patch('dfastmi.batch.AnalyserWaqua.DataTextFileOperations.read_waqua_xyz') as mocked_read_waqua_xyz, \
        patch('dfastmi.batch.AnalyserWaqua.dfastmi.kernel.core.dzq_from_du_and_h') as mocked_kernel_core:

            mocked_get_text.return_value="description"
            mocked_read_waqua_xyz.return_value=numpy.array([1, 2, 3, 4, 5])
            mocked_kernel_core.return_value=numpy.array([1, 2, 3, 4, 5])

            output_data = waqua.analyse(fraction_of_year, rsigma)

            assert mocked_kernel_core.call_count == 0

        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.first_min_velocity_m == 0
        assert output_data.first_min_velocity_n == 0


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
    def given_data_and_mocked_classes_when_analyse_then_return_expected_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        """
        given : data and mocked classes
        when :  analyse 
        then  : return expected output_data
        """
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]

        tstag = 0.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        ucrit = 0.3
        report = False
        waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)

        with patch('dfastmi.batch.AnalyserWaqua.ApplicationSettingsHelper.log_text'), \
        patch('dfastmi.batch.AnalyserWaqua.ApplicationSettingsHelper.get_text') as mocked_get_text, \
        patch('dfastmi.batch.AnalyserWaqua.DataTextFileOperations.read_waqua_xyz') as mocked_read_waqua_xyz, \
        patch('dfastmi.batch.AnalyserWaqua.dfastmi.kernel.core.dzq_from_du_and_h') as mocked_kernel_core, \
        patch('dfastmi.batch.AnalyserWaqua.os.path.isfile') as mocked_isfile:

            self.setup_mocks(mocked_get_text, mocked_read_waqua_xyz, mocked_isfile)

            output_data = waqua.analyse(fraction_of_year, rsigma)

            assert mocked_kernel_core.call_count == 3

        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.first_min_velocity_m == 0
        assert output_data.first_min_velocity_n == 0

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
    def given_data_and_mocked_classes_with_tstag_above_zero_when_analyse_then_return_expected_output_data(self, display : bool, reduced_output : bool, old_zmin_zmax : bool):
        """
        given : data and mocked classes with tstag above zero
        when :  analyse 
        then  : return expected output_data
        """
        fraction_of_year = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]

        tstag = 1.0
        discharges = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        ucrit = 0.3
        report = False
        waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)

        with patch('dfastmi.batch.AnalyserWaqua.ApplicationSettingsHelper.log_text'), \
            patch('dfastmi.batch.AnalyserWaqua.ApplicationSettingsHelper.get_text') as mocked_get_text, \
            patch('dfastmi.batch.AnalyserWaqua.DataTextFileOperations.read_waqua_xyz') as mocked_read_waqua_xyz, \
            patch('dfastmi.batch.AnalyserWaqua.dfastmi.kernel.core.dzq_from_du_and_h') as mocked_kernel_core, \
            patch('dfastmi.batch.AnalyserWaqua.os.path.isfile') as mocked_isfile:

                self.setup_mocks(mocked_get_text, mocked_read_waqua_xyz, mocked_isfile)

                output_data = waqua.analyse(fraction_of_year, rsigma)

                assert mocked_kernel_core.call_count == 3

        assert len(output_data.data_zgem) == 0
        assert len(output_data.data_zmax) == 0
        assert len(output_data.data_zmin) == 0
        assert output_data.first_min_velocity_m == 0
        assert output_data.first_min_velocity_n == 0

    def setup_mocks(self, mocked_get_text, mocked_read_waqua_xyz, mocked_isfile):
        mocked_isfile.return_value = True
        mocked_get_text.return_value = "description"

        def custom_side_effect(*args, **kwargs):
            if "xyz_velocity-zeta.001." in args[0]:
                return numpy.array([[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]])
            else:
                return numpy.array([1, 1, 1])

        mocked_read_waqua_xyz.side_effect = custom_side_effect