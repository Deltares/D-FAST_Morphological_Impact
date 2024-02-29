import pytest
from dfastmi.batch.ConfigurationChecker import ConfigurationChecker
from dfastmi.batch.ConfigurationCheckerFactory import ConfigurationCheckerFactory
from dfastmi.batch.ConfigurationCheckerLegacy import ConfigurationCheckerLegacy


from packaging import version


class Test_configuration_checker_factory():
    def given_legacy_when_then(self):
        legacy_version = version.parse("1.0")
        legacy_configuration_checker = ConfigurationCheckerFactory.generate(legacy_version)
        assert isinstance(legacy_configuration_checker, ConfigurationCheckerLegacy)
    
    def given_when_then(self):
        correct_version = version.parse("2.0")
        legacy_configuration_checker = ConfigurationCheckerFactory.generate(correct_version)
        assert isinstance(legacy_configuration_checker, ConfigurationChecker)
    
    def given_unknown_when_then(self):
        unknown_version = version.parse("0.0")
        with pytest.raises(Exception) as cm:
            ConfigurationCheckerFactory.generate(unknown_version)
        assert str(cm.value) == f"No ConfigurationChecker constructor registered for version {unknown_version}"
        
    def given_None_when_then(self):
        with pytest.raises(Exception) as cm:
            ConfigurationCheckerFactory.generate(None)
        assert str(cm.value) == f"No ConfigurationChecker constructor registered for version {None}"
        