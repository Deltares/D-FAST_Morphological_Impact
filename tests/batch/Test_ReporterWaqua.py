from unittest.mock import patch
import numpy
from dfastmi.batch.OutputDataWaqua import OutputDataWaqua
from dfastmi.batch.ReporterWaqua import ReporterWaqua

class Test_ReporterWaqua():
    def given_output_data_and_mocked_write_files_when_write_report_then_expect_3_calls_for_writing_report(self):
        """
        given : output data and mocked write files
        when :  write report  
        then  : expect 3 calls for writing report
        """
        reporter = ReporterWaqua("filepath")
        first_min_velocity_m = 0
        first_min_velocity_n = 0
        data_zgem = numpy.array([1, 2, 3, 4, 5])
        data_zmax = numpy.array([1, 2, 3, 4, 5])
        data_zmin = numpy.array([1, 2, 3, 4, 5])
        output_data = OutputDataWaqua(first_min_velocity_m, first_min_velocity_n, data_zgem, data_zmax, data_zmin)
        with patch('dfastmi.batch.ReporterWaqua.ApplicationSettingsHelper.get_filename') as mocked_get_file_name,\
        patch('dfastmi.batch.ReporterWaqua.DataTextFileOperations.write_simona_box') as mocked_write_simona_box:

            mocked_get_file_name.return_value = "filename.file"
            mocked_get_file_name.side_effect = "file.file"

            reporter.write_report(output_data)

            assert mocked_write_simona_box.call_count == 3
            assert mocked_get_file_name.call_count == 3