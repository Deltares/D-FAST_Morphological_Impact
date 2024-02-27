import pytest
import dfastmi.batch.FileNameRetriever
from configparser import ConfigParser

class Test_FileNameRetriever():
    @pytest.mark.parametrize("imode, config", [
        (0, ConfigParser()),
        (1, None),
    ])
    def given_values_for_unsupported_retriever_when_get_filename_retriever_then_return_expected_retriever_unsupported(self, imode, config):
        file_name_retriever = dfastmi.batch.FileNameRetriever.get_filename_retriever(imode, config, False)
        
        assert isinstance(file_name_retriever, dfastmi.batch.FileNameRetriever.FileNameRetrieverUnsupported)
        
    def given_values_for_legacy_retriever_when_get_filename_retriever_then_return_expected_retriever_legacy(self):
        imode = 1
        config = ConfigParser()
        config.add_section("General")
        config.set("General", "Version", "1")
        
        file_name_retriever = dfastmi.batch.FileNameRetriever.get_filename_retriever(imode, config, False)
        
        assert isinstance(file_name_retriever, dfastmi.batch.FileNameRetriever.FileNameRetrieverLegacy)
    
    @pytest.mark.parametrize("use_tide", [
        True,
        False
    ])
    def given_values_for_retriever_when_get_filename_retriever_then_return_expected_retriever(self, use_tide):
        imode = 1
        config = ConfigParser()
        config.add_section("General")
        config.set("General", "Version", "2")
        file_name_retriever = dfastmi.batch.FileNameRetriever.get_filename_retriever(imode, config, use_tide)
        
        assert isinstance(file_name_retriever, dfastmi.batch.FileNameRetriever.FileNameRetriever)
    
    class Test_FileNameRetriever_Unsupported():
        def given_config_parser_when_get_file_names_unsupported_then_return_no_file_names(self):
            config = ConfigParser()
            fnrvu = dfastmi.batch.FileNameRetriever.FileNameRetrieverUnsupported()
            
            filenames = fnrvu.get_file_names(config)
            
            assert len(filenames) == 0
    
    class Test_FileNameRetriever_legacy():
        def given_partial_setup_config_parser_when_get_file_names_legacy_then_throw_exception_with_expected_message(self):
            fnr_legacy = dfastmi.batch.FileNameRetriever.FileNameRetrieverLegacy()
            
            key = "Reference"
            chap = "Q1"
            expected_exception_message = 'Keyword "{}" is not specified in group "{}" of analysis configuration file.'.format(key, chap)
            
            config = ConfigParser()
            config.add_section(chap)
            
            with pytest.raises(Exception) as e:
                fnr_legacy.get_file_names(config)
            assert str(e.value) == expected_exception_message
        
        def given_empty_config_parser_when_get_file_names_legacy_then_return_no_file_names(self):
            config = ConfigParser()
            fnr_legacy = dfastmi.batch.FileNameRetriever.FileNameRetrieverLegacy()
            
            filenames = fnr_legacy.get_file_names(config)
            
            assert len(filenames) == 0
        
        def given_config_parser_with_data_when_get_file_names_legacy_then_return_expected_file_names(self):
            config = ConfigParser()
            fnr_legacy = dfastmi.batch.FileNameRetriever.FileNameRetrieverLegacy()
            
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
        
    class Test_FileNameRetriever():
        @pytest.mark.parametrize("use_tide", [
            True,
            False
        ])
        def given_partial_setup_config_parser_when_get_file_names_then_throw_exception_with_expected_message(self, use_tide):
            file_name_retriever = dfastmi.batch.FileNameRetriever.FileNameRetriever(use_tide)
            
            key = "Discharge"
            chap = "C1"
            expected_exception_message = 'Keyword "{}" is not specified in group "{}" of analysis configuration file.'.format(key, chap)
            
            config = ConfigParser()
            config.add_section(chap)
            
            with pytest.raises(Exception) as e:
                file_name_retriever.get_file_names(config)
            assert str(e.value) == expected_exception_message
            
        @pytest.mark.parametrize("not_a_float_string", [
            "not a float",
            "1,0",
            "#"
            "--=+"
        ])
        def given_config_parser_with_not_a_float_for_discharge_when_get_file_names_then_throw_type_error_with_expected_message(self, not_a_float_string):
            file_name_retriever = dfastmi.batch.FileNameRetriever.FileNameRetriever(False)
            
            key = "Discharge"
            chap = "C1"
            expected_exception_message = f'{not_a_float_string} from Discharge could now be handled as a float.'
            
            config = ConfigParser()
            config.add_section(chap)
            config.set(chap, key, not_a_float_string)
            
            with pytest.raises(TypeError) as e:
                file_name_retriever.get_file_names(config)
            assert str(e.value) == expected_exception_message
        
        @pytest.mark.parametrize("use_tide", [
            True,
            False
        ])
        def given_empty_config_parser_when_get_file_names_then_return_no_file_names(self, use_tide):
            config = ConfigParser()
            file_name_retriever = dfastmi.batch.FileNameRetriever.FileNameRetriever(use_tide)
            
            filenames = file_name_retriever.get_file_names(config)
            
            assert len(filenames) == 0
        
        def given_config_parser_with_data_when_get_file_names_then_return_expected_file_names(self):
            config = ConfigParser()
            file_name_retriever = dfastmi.batch.FileNameRetriever.FileNameRetriever(False)
            
            q1_expected_filename= self.get_expected_q_filename_and_update_config(config, "C1", "1.0")
            q2_expected_filename= self.get_expected_q_filename_and_update_config(config, "C2", "2.0")
            q3_expected_filename= self.get_expected_q_filename_and_update_config(config, "C3", "3.0")
            
            filenames = file_name_retriever.get_file_names(config)
            
            assert filenames[1.0] == q1_expected_filename
            assert filenames[2.0] == q2_expected_filename
            assert filenames[3.0] == q3_expected_filename
            
        def given_config_parser_with_data_and_need_of_tide_enable_when_get_file_names_then_return_expected_file_names_including_tide(self):
            config = ConfigParser()
            file_name_retriever = dfastmi.batch.FileNameRetriever.FileNameRetriever(True)
            
            q1_expected_filename= self.get_expected_q_filename_and_update_config(config, "C1", "1.0", True)
            q2_expected_filename= self.get_expected_q_filename_and_update_config(config, "C2", "2.0", True)
            q3_expected_filename= self.get_expected_q_filename_and_update_config(config, "C3", "3.0", True)
            
            filenames = file_name_retriever.get_file_names(config)
            
            assert filenames[(1.0,"C1-TideBC")] == q1_expected_filename
            assert filenames[(2.0,"C2-TideBC")] == q2_expected_filename
            assert filenames[(3.0,"C3-TideBC")] == q3_expected_filename
            
        def get_expected_q_filename_and_update_config(self, config : ConfigParser, q : str, discharge_value, tide = False):
            reference = "Reference"
            with_measure = "WithMeasure"
            discharge = "Discharge"
            
            q_reference_filename = q + "-" + reference
            q_with_measure_filename = q + "-" + with_measure
            
            config.add_section(q)
            config.set(q, reference, q_reference_filename)
            config.set(q, with_measure, q_with_measure_filename)
            config.set(q, discharge, discharge_value)
            
            if tide:
                tide = "TideBC"
                q_tide = q + "-" + tide
                config.set(q, tide, q_tide)     
            
            return (q_reference_filename,q_with_measure_filename)