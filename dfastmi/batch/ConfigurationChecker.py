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
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.Reach import Reach

from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

class ConfigurationChecker(AConfigurationCheckerBase):
    """
        Check if a version 2 analysis configuration is valid.
    """
    def check_configuration(self,
                            rivers: RiversObject,
                            config: configparser.ConfigParser) -> bool:
        """
        Check if a version 2 analysis configuration is valid.

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
            reach = self._get_reach(rivers, config, Reach)
        except LookupError:
            return False
        except ValueError:
            return False

        hydro_q = reach.hydro_q
        q_stagnant = reach.qstagnant
        if config.has_section("General") and config.has_option("General", "Qthreshold") :
            try:
                q_threshold = config.getfloat("General", "Qthreshold")
            except ValueError:
                q_threshold_str = config.get("General", "Qthreshold", fallback="")
                ApplicationSettingsHelper.log_text(f"Please this configuration has in the General section an option for Qthreshold"
                                                   f"but is not float but : {q_threshold_str}!" 
                                                   f"Using q_stagnant as q_threshold : {q_stagnant}")
                q_threshold = q_stagnant
        else:
            q_threshold = q_stagnant        
        n_cond = len(hydro_q)

        return_value = False
        for i in range(n_cond):
            if hydro_q[i] > q_threshold : 
                success = self._check_configuration_cond(config, hydro_q[i])
                if success and not return_value:
                    return_value = True
        return return_value

    def _check_configuration_cond(self, 
                                 config: configparser.ConfigParser,
                                 discharge: float) -> bool:
        """
        Check if a version 2 analysis condition configuration is valid for a discharge.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.
        
        discharge : float
            Discharge (q) [m3/s]

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration condition is valid for this discharge.
        
        """
        return_value = True
        has_condition_section_for_this_discharge = False
        condition_sections = [section for section in config.sections() if section[0] == "C"]
        if len(condition_sections) == 0:
            ApplicationSettingsHelper.log_text("No condition sections found in conditions configurations file!")
            return False

        for condition in condition_sections:
            if config.has_option(condition, "Discharge"):
                try:
                    discharge_cond = config.getfloat(condition, "Discharge")
                except ValueError:
                    discharge_cond_str = config.get(condition, "Discharge", fallback="")
                    ApplicationSettingsHelper.log_text(f"Please this is a condition ({condition}), "
                        f"but discharge in condition cfg file is not float but has value : {discharge_cond_str}!")
                    continue

                if abs(discharge - discharge_cond) <= 0.001:
                    has_condition_section_for_this_discharge = True
                    
                    # we found the correct condition
                    return_value = self._check_key_with_file_value_and_set_return_value_if_needed(config, return_value, condition, "Reference")
                    return_value = self._check_key_with_file_value_and_set_return_value_if_needed(config, return_value, condition, "WithMeasure")
            else:
                ApplicationSettingsHelper.log_text(f"Please this is a condition : {condition}, but 'Discharge' key is not set!")
                if return_value:
                    return_value = False

        return return_value and has_condition_section_for_this_discharge

    def _check_key_with_file_value_and_set_return_value_if_needed(self,
               config : configparser.ConfigParser,
               return_value : bool,
               condition : str,
               key : str) -> bool:
        """
        Check if key exist as option in the section of this condition.
        If exist check if file which is the key value is representing exist.        
        """
        if not self._check_key_with_file_value(config, condition, key) and return_value:
            return_value = False
        return return_value
