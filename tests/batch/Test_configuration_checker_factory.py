import pytest
from dfastmi.batch.ConfigurationChecker import ConfigurationChecker
from dfastmi.batch.ConfigurationCheckerFactory import ConfigurationCheckerFactory
from dfastmi.batch.ConfigurationCheckerLegacy import ConfigurationCheckerLegacy


from packaging.version import Version


class Test_configuration_checker_factory():
    def given_legacy_configuration_version_when_generating_ConfigurationChecker_then_validate_generated_ConfigurationChecker_is_a_ConfigurationCheckerLegacy(self):
        legacy_version = Version("1.0")
        legacy_configuration_checker = ConfigurationCheckerFactory.generate(legacy_version)
        assert isinstance(legacy_configuration_checker, ConfigurationCheckerLegacy)
    
    def given_valid_configuration_version_when_generating_ConfigurationChecker_then_validate_generated_ConfigurationChecker_is_a_ConfigurationChecker(self):
        correct_version = Version("2.0")
        legacy_configuration_checker = ConfigurationCheckerFactory.generate(correct_version)
        assert isinstance(legacy_configuration_checker, ConfigurationChecker)
    
    def given_invalid_configuration_version_when_generating_ConfigurationChecker_then_throw_exception_unknown_version(self):
        unknown_version = Version("0.0")
        with pytest.raises(Exception) as cm:
            ConfigurationCheckerFactory.generate(unknown_version)
        assert str(cm.value) == f"No ConfigurationChecker constructor registered for version {unknown_version}"
        
    def given_no_configuration_version_when_generating_ConfigurationChecker_then_throw_exception_unknown_version(self):
        with pytest.raises(Exception) as cm:
            ConfigurationCheckerFactory.generate(None)
        assert str(cm.value) == f"No ConfigurationChecker constructor registered for version {None}"
        