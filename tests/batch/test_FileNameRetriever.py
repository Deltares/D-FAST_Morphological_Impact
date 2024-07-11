from configparser import ConfigParser

import pytest

from dfastmi.batch.FileNameRetriever import FileNameRetriever


class Test_FileNameRetriever:
    @pytest.mark.parametrize("use_tide", [True, False])
    def given_partial_setup_config_parser_when_get_file_names_then_throw_key_error_with_expected_message(
        self, use_tide
    ):
        """
        given : partial setup config parser
        when :  get file names
        then  : throw key error with expected message
        """
        file_name_retriever = FileNameRetriever(use_tide)

        key = "Discharge"
        chap = "C1"
        expected_exception_message = f'Keyword "{key}" is not specified in group "{chap}" of analysis configuration file.'

        config = ConfigParser()
        config.add_section(chap)

        with pytest.raises(KeyError) as e:
            file_name_retriever.get_file_names(config)
        assert str(e.value.args[0]) == expected_exception_message

    @pytest.mark.parametrize("not_a_float_string", ["not a float", "1,0", "#" "--=+"])
    def given_config_parser_with_not_a_float_for_discharge_when_get_file_names_then_throw_type_error_with_expected_message(
        self, not_a_float_string
    ):
        """
        given : config parser with not a float for discharge
        when :  get file names
        then  : throw type error with expected message
        """
        file_name_retriever = FileNameRetriever(False)

        key = "Discharge"
        chap = "C1"
        expected_exception_message = (
            f"{not_a_float_string} from Discharge could not be handled as a float."
        )

        config = ConfigParser()
        config.add_section(chap)
        config.set(chap, key, not_a_float_string)

        with pytest.raises(TypeError) as e:
            file_name_retriever.get_file_names(config)
        assert str(e.value) == expected_exception_message

    @pytest.mark.parametrize("use_tide", [True, False])
    def given_empty_config_parser_when_get_file_names_then_return_no_file_names(
        self, use_tide
    ):
        """
        given : empty config parser
        when :  get file names
        then  : return no file names
        """
        config = ConfigParser()
        file_name_retriever = FileNameRetriever(use_tide)

        filenames = file_name_retriever.get_file_names(config)

        assert len(filenames) == 0

    def given_config_parser_with_data_when_get_file_names_then_return_expected_file_names(
        self,
    ):
        """
        given : config parser with data
        when :  get file names
        then  : return expected file names
        """
        config = ConfigParser()
        file_name_retriever = FileNameRetriever(False)

        q1_expected_filename = self.get_expected_q_filename_and_update_config(
            config, "C1", "1.0"
        )
        q2_expected_filename = self.get_expected_q_filename_and_update_config(
            config, "C2", "2.0"
        )
        q3_expected_filename = self.get_expected_q_filename_and_update_config(
            config, "C3", "3.0"
        )

        filenames = file_name_retriever.get_file_names(config)

        assert filenames[1.0] == q1_expected_filename
        assert filenames[2.0] == q2_expected_filename
        assert filenames[3.0] == q3_expected_filename

    def given_config_parser_with_data_and_need_of_tide_enable_when_get_file_names_then_return_expected_file_names_including_tide(
        self,
    ):
        """
        given : config parser with data and need of tide enable
        when :  get file names
        then  : return expected file names including tide
        """
        config = ConfigParser()
        file_name_retriever = FileNameRetriever(True)

        q1_expected_filename = self.get_expected_q_filename_and_update_config(
            config, "C1", "1.0", True
        )
        q2_expected_filename = self.get_expected_q_filename_and_update_config(
            config, "C2", "2.0", True
        )
        q3_expected_filename = self.get_expected_q_filename_and_update_config(
            config, "C3", "3.0", True
        )

        filenames = file_name_retriever.get_file_names(config)

        assert filenames[(1.0, "C1-TideBC")] == q1_expected_filename
        assert filenames[(2.0, "C2-TideBC")] == q2_expected_filename
        assert filenames[(3.0, "C3-TideBC")] == q3_expected_filename

    def get_expected_q_filename_and_update_config(
        self, config: ConfigParser, q: str, discharge_value, tide=False
    ):
        reference = "Reference"
        with_intervention = "WithIntervention"
        discharge = "Discharge"

        q_reference_filename = q + "-" + reference
        q_with_intervention_filename = q + "-" + with_intervention

        config.add_section(q)
        config.set(q, reference, q_reference_filename)
        config.set(q, with_intervention, q_with_intervention_filename)
        config.set(q, discharge, discharge_value)

        if tide:
            tide = "TideBC"
            q_tide = q + "-" + tide
            config.set(q, tide, q_tide)

        return (q_reference_filename, q_with_intervention_filename)
