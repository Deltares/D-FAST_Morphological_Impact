from configparser import ConfigParser
import pytest
from dfastmi.batch.FileNameRetrieverLegacy import FileNameRetrieverLegacy

class Test_FileNameRetriever_legacy():
    def given_partial_setup_config_parser_when_get_file_names_legacy_then_throw_key_error_with_expected_message(self):
        """
        given : partial setup config parser
        when :  get file names legacy
        then  : throw key error with expected message
        """
        fnr_legacy = FileNameRetrieverLegacy()

        key = "Reference"
        chap = "Q1"
        expected_exception_message = f'Keyword "{key}" is not specified in group "{chap}" of analysis configuration file.'

        config = ConfigParser()
        config.add_section(chap)

        with pytest.raises(KeyError) as e:
            fnr_legacy.get_file_names(config)
        assert str(e.value.args[0]) == expected_exception_message

    def given_empty_config_parser_when_get_file_names_legacy_then_return_no_file_names(self):
        """
        given : empty config parser
        when :  get file names legacy
        then  : return no file names
        """
        config = ConfigParser()
        fnr_legacy = FileNameRetrieverLegacy()

        filenames = fnr_legacy.get_file_names(config)

        assert len(filenames) == 0

    def given_config_parser_with_data_when_get_file_names_legacy_then_return_expected_file_names(self):
        """
        given : config parser with data
        when :  get file names legacy
        then  : return expected file names
        """
        config = ConfigParser()
        fnr_legacy = FileNameRetrieverLegacy()

        q1_expected_filename= self.get_expected_q_filename_and_update_config(config, "Q1")
        q2_expected_filename= self.get_expected_q_filename_and_update_config(config, "Q2")
        q3_expected_filename= self.get_expected_q_filename_and_update_config(config, "Q3")

        filenames = fnr_legacy.get_file_names(config)

        assert filenames[0] == q1_expected_filename
        assert filenames[1] == q2_expected_filename
        assert filenames[2] == q3_expected_filename

    def get_expected_q_filename_and_update_config(self, config : ConfigParser, q : str):
        reference = "Reference"
        with_measure = "WithMeasure"
        q_reference_filename = q + "-" + reference
        q_with_measure_filename = q + "-" + with_measure

        config.add_section(q)
        config.set(q, reference, q_reference_filename)
        config.set(q, with_measure, q_with_measure_filename)

        return (q_reference_filename,q_with_measure_filename)