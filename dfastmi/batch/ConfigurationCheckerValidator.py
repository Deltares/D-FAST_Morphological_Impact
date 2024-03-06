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
import configparser
from typing import Callable


class ConfigurationCheckerValidator:
    """
    Used to register validation methods and 
    validate river configuration by a mode
    """
    _validators = {}
    """Contains the configuration validator be used depending on mode"""

    def register_validator(self, mode: str, validator: Callable[[configparser.ConfigParser,  int], bool]):
        """Register creator function to create a AConfigurationChecker object."""
        if mode not in self._validators:
            self._validators[mode] = validator

    def is_valid(self, mode: str, config: configparser.ConfigParser, i : int ) -> bool:
        """
        Call the Validator function to valdite a ConfigurationCheckerLegacy object.

        Arguments
        ---------
        mode: str
            The mode in the configuration to validate for.

        Returns
        -------
        bool
            calls the existing / registered validator and validates the provided configuration.
        """
        validate_method = self._validators.get(mode, self._unsupported)
        return validate_method(config, i)
    
    def _unsupported(self, config: configparser.ConfigParser, i : int) -> bool:
        return False