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
import configparser
from dfastmi.batch.AConfigurationChecker import AConfigurationCheckerBase
from dfastmi.batch.ConfigurationCheckerValidator import ConfigurationCheckerValidator
from dfastmi.batch.ConfigurationInitializerLegacy import ConfigurationInitializerLegacy
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

from dfastmi.io.ReachLegacy import ReachLegacy
from dfastmi.io.RiversObject import RiversObject

WAQUA_EXPORT = "WAQUA export"
DFLOWFM_MAP = "D-Flow FM map"
class ConfigurationCheckerLegacy(AConfigurationCheckerBase):
    """
        Check if a version 1 / legacy analysis configuration is valid.
    """
    _validator : ConfigurationCheckerValidator

    def __init__(self):
        self._validator = ConfigurationCheckerValidator()
        self._validator.register_validator(WAQUA_EXPORT, self._check_configuration_cond_waqua)
        self._validator.register_validator(DFLOWFM_MAP, self._check_configuration_cond_fm)
    
    def check_configuration(self, rivers: RiversObject, config: configparser.ConfigParser) -> bool:
        """
        Check if a version 1 / legacy analysis configuration is valid.

        Arguments
        ---------
        rivers: RiversObject
            An object containing the river data.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        try:
            reach = self._get_reach(rivers, config, ReachLegacy)
        except LookupError:
            return False
        except ValueError:
            return False

        initialized_config = ConfigurationInitializerLegacy(reach, config)

        mode_str = config.get("General", "Mode", fallback=DFLOWFM_MAP)
        ret_val  = True
        for i in range(3):
            if initialized_config.apply_q[i] and not self._validator.is_valid(mode_str, config, i) and ret_val:
                ret_val = False
        return ret_val

    def _check_configuration_cond_waqua(
            self,
            config: configparser.ConfigParser,
            i : int) -> bool:
        """
        Check validity of one condition of a version 1 analysis configuration using WAQUA results.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.
        i : int
            Flow condition to be checked.            

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        cond = "Q" + str(i+1)
        # condition block to be checked.
        # condition block must be specified since it must contain the Reference and WithMeasure file names
        return self._discharge_check(config, cond)
    
    def _discharge_check(self, config: configparser.ConfigParser, cond: str) -> bool:
        if not config.has_section(cond) :
            ApplicationSettingsHelper.log_text(f"Please this {cond} is not in configuration file!")
            return False
        if not config.has_option(cond, "Discharge"):
            ApplicationSettingsHelper.log_text(f"Please this {cond} is in the config but has no 'Discharge' key set!")
            return False
        try:
            config.getfloat(cond, "Discharge")
        except ValueError:
            discharge_cond_str = config.get(cond, "Discharge", fallback="")
            ApplicationSettingsHelper.log_text(f"Please this is a condition ({cond}), "
                    f"but discharge in condition cfg file is not float but has value : {discharge_cond_str}!")
            return False
        return True

    def _check_configuration_cond_fm(
            self,
            config: configparser.ConfigParser,
            i : int) -> bool:
        """
        Check validity of one condition of a version 1 analysis configuration using D-Flow FM results.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.
        i : int
            Flow condition to be checked.            

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        cond = "Q" + str(i+1)
        # condition block to be checked.
        # condition block must be specified since it must contain the Reference and WithMeasure file names
        return_value = self._discharge_check(config, cond)

        if not self._check_key_with_file_value(config, cond, "Reference") and return_value:
            return_value = False

        if not self._check_key_with_file_value(config, cond, "WithMeasure") and return_value:
            return_value = False

        return return_value
