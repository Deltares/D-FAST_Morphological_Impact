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

from typing import Optional, Tuple
from dfastmi.io.Reach import ReachLegacy
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import Vector, BoolVector, QRuns
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

import dfastmi.kernel.core
import dfastmi.kernel.legacy
import dfastmi.plotting
import configparser
from typing import Tuple
from dfastmi.batch.AConfigurationChecker import AConfigurationCheckerBase
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.Reach import Reach

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
            A dictionary containing the river data.
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

        hydro_q = reach.hydro_q
        n_cond = len(hydro_q)
        
        found = [False]*n_cond
        
        for i in range(n_cond):
            success, found[i] = self._check_configuration_cond(config, hydro_q[i])
            if not success:
                return False
        
        if not all(found):
            return False
            
        return True

    def _check_configuration_cond(self, 
                                 config: configparser.ConfigParser,
                                 q: float) -> Tuple[bool, bool]:
        """
        Check if a version 2 analysis configuration is valid.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        found : bool
            Flag indicating whether the condition has been found.
        """
        qstr = str(q)
        found = False
        
        for cond in config.keys():
            if cond[0] != "C":
                # not a condition block
                continue
            
            if "Discharge" not in config[cond]:
                return False, found
            
            qstr_cond = config.get(cond, "Discharge")
            if qstr != qstr_cond:
                continue

            found = True

            if "Reference" not in config[cond]:
                return False, found
            
            if "WithMeasure" not in config[cond]:
                return False, found

        return True, found