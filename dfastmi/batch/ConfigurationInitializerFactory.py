from typing import Callable, TypeVar
from configparser import ConfigParser
from packaging.version import Version

from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.batch.ConfigurationInitializerLegacy import ConfigurationInitializerLegacy
from dfastmi.batch.ConfigurationInitializer import ConfigurationInitializer
from dfastmi.io.IReach import IReach

T = TypeVar('T')  # Define a type variable

class ConfigurationInitializerFactory:
    """
    Class is used to register and get creation of AConfigurationChecker Objects
    """
    _creators = {}
    """Contains the AConfigurationChecker Objects creators to be used"""

    @staticmethod
    def register_creator(configuration_version: Version, creator: Callable[[IReach,ConfigParser], AConfigurationInitializerBase]):
        """Register creator function to create a AConfigurationInitializerBase object."""
        if configuration_version not in ConfigurationInitializerFactory._creators:
            ConfigurationInitializerFactory._creators[configuration_version] = creator

    @staticmethod
    def generate(configuration_version: Version, reach : IReach, config:ConfigParser) -> AConfigurationInitializerBase:
        """
        Call the Constructor function to generate Configuration Initializer object.

        Arguments
        ---------
        configuration_version: version
            Version to retrieve the Configuration Initializer for.

        Returns
        -------
        ConfigurationInitializer : AConfigurationInitializerBase
            AConfigurationInitializerBase object based on the given version, if no valid AConfigurationInitializerBase can be found exception is thrown.
        """
        constructor = ConfigurationInitializerFactory._creators.get(configuration_version)
        if constructor:
            return constructor(reach, config)
        raise ValueError(f"No AConfigurationInitializerBase constructor registered for version {configuration_version}")
    
legacy_version = Version("1.0")
ConfigurationInitializerFactory.register_creator(legacy_version, ConfigurationInitializerLegacy)

correct_version = Version("2.0")
ConfigurationInitializerFactory.register_creator(correct_version, ConfigurationInitializer)
