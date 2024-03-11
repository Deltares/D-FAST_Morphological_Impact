# -*- coding: utf-8 -*-
"""
Copyright (C) 2024 Stichting Deltares.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation version 2.1.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see <http://www.gnu.org/licenses/>.

contact: delft3d.support@deltares.nl
Stichting Deltares
P.O. Box 177
2600 MH Delft, The Netherlands

All indications and logos of, and references to, "Delft3D" and "Deltares"
are registered trademarks of Stichting Deltares, and remain the property of
Stichting Deltares. All rights reserved.

INFORMATION
This file is part of D-FAST Morphological Impact: https://github.com/Deltares/D-FAST_Morphological_Impact
"""
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
