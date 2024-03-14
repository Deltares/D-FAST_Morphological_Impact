import pytest
from packaging import version

from dfastmi.batch.FileNameRetriever import FileNameRetriever
from dfastmi.batch.FileNameRetrieverFactory import FileNameRetrieverFactory
from dfastmi.batch.FileNameRetrieverLegacy import FileNameRetrieverLegacy
from dfastmi.batch.FileNameRetrieverUnsupported import FileNameRetrieverUnsupported


class Test_FileNameRetrieverFactory:
    @pytest.fixture
    def factory(self) -> FileNameRetrieverFactory:
        factory = FileNameRetrieverFactory()
        factory.register_creator(
            version.Version("1.0"), lambda needs_tide: FileNameRetrieverLegacy()
        )
        factory.register_creator(
            version.Version("2.0"), lambda needs_tide: FileNameRetriever(needs_tide)
        )
        return factory

    @pytest.mark.parametrize("string_version", ["1", "1.0", "1.0.0", "1.0.0.0"])
    def given_varying_version_1_when_generate_then_return_FileNameRetrieverLegacy(
        self, factory: FileNameRetrieverFactory, string_version: str
    ):
        """
        given : varying version 1
        when :  generate
        then  : return FileNameRetrieverLegacy
        """
        file_name_retriever_version = version.Version(string_version)
        needs_tide = True
        file_name_retriever = factory.generate(file_name_retriever_version, needs_tide)
        assert isinstance(file_name_retriever, FileNameRetrieverLegacy)

    @pytest.mark.parametrize("needs_tide", [True, False])
    def given_version_2_with_varying_needs_tide_when_generate_then_return_FileNameRetriever(
        self, factory: FileNameRetrieverFactory, needs_tide: bool
    ):
        """
        given : version 2 with varying needs tide
        when :  generate
        then  : return FileNameRetriever
        """
        file_name_retriever_version = version.Version("2.0")
        file_name_retriever = factory.generate(file_name_retriever_version, needs_tide)
        assert isinstance(file_name_retriever, FileNameRetriever)

    @pytest.mark.parametrize("string_version", ["2", "2.0", "2.0.0", "2.0.0.0"])
    def given_varying_version_2_when_generate_then_return_FileNameRetrieverLegacy(
        self, factory: FileNameRetrieverFactory, string_version: str
    ):
        """
        given : varying version 2
        when :  generate
        then  : return FileNameRetrieverLegacy
        """
        file_name_retriever_version = version.Version(string_version)
        file_name_retriever = factory.generate(file_name_retriever_version, True)
        assert isinstance(file_name_retriever, FileNameRetriever)

    @pytest.mark.parametrize("string_version", ["0.0", "999.0"])
    def given_unsupported_version_when_generate_then_return_FileNameRetrieverUnsupported(
        self, factory: FileNameRetrieverFactory, string_version: str
    ):
        """
        given : unsupported version
        when :  generate
        then  : return FileNameRetrieverUnsupported
        """
        needs_tide = True
        file_name_retriever_version = version.Version(string_version)
        file_name_retriever = factory.generate(file_name_retriever_version, needs_tide)
        assert isinstance(file_name_retriever, FileNameRetrieverUnsupported)
