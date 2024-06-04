# -*- coding: utf-8 -*-
"""
Copyright © 2024 Stichting Deltares.

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
from typing import Callable

from packaging.version import Version

from dfastmi.batch.AConfigurationChecker import AConfigurationCheckerBase
from dfastmi.batch.ConfigurationChecker import ConfigurationChecker
from dfastmi.batch.ConfigurationCheckerLegacy import ConfigurationCheckerLegacy


class ConfigurationCheckerFactory:
    """
    Class is used to register and get creation of AConfigurationChecker Objects
    """

    _creators = {}
    """Contains the AConfigurationChecker Objects creators to be used"""

    @staticmethod
    def register_creator(
        configuration_version: Version, creator: Callable[[], AConfigurationCheckerBase]
    ):
        """Register creator function to create a AConfigurationChecker object."""
        if configuration_version not in ConfigurationCheckerFactory._creators:
            ConfigurationCheckerFactory._creators[configuration_version] = creator

    @staticmethod
    def generate(configuration_version: Version) -> AConfigurationCheckerBase:
        """
        Call the Constructor function to generate AConfigurationChecker object.

        Arguments
        ---------
        configuration_version: version
            Version to retrieve the ConfigurationChecker for.

        Returns
        -------
        ConfigurationChecker : AConfigurationChecker
            AConfigurationChecker object based on the given version, if no valid ConfigurationChecker can be found exception is thrown.
        """
        constructor = ConfigurationCheckerFactory._creators.get(configuration_version)
        if constructor:
            return constructor()
        raise ValueError(
            f"No ConfigurationChecker constructor registered for version {configuration_version}"
        )


ConfigurationCheckerFactory.register_creator(Version("1.0"), ConfigurationCheckerLegacy)

ConfigurationCheckerFactory.register_creator(Version("2.0"), ConfigurationChecker)
ConfigurationCheckerFactory.register_creator(Version("3.0"), ConfigurationChecker)
