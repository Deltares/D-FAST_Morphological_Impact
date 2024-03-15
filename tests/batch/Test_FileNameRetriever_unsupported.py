from configparser import ConfigParser

from dfastmi.batch.FileNameRetrieverUnsupported import FileNameRetrieverUnsupported


class Test_FileNameRetriever_unsupported:
    def given_config_parser_when_get_file_names_unsupported_then_return_no_file_names(
        self,
    ):
        """
        given : config parser
        when :  get file names unsupported
        then  : return no file names
        """
        config = ConfigParser()
        fnrvu = FileNameRetrieverUnsupported()

        filenames = fnrvu.get_file_names(config)

        assert len(filenames) == 0
