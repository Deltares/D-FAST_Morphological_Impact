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
from abc import ABC, abstractmethod

from dfastmi.io.RiversObject import RiversObject


class AConfigurationCheckerBase(ABC):
    """
    Abstract base class ConfigurationChecker.
    """

    @abstractmethod
    def check_configuration(self, rivers: RiversObject, config: configparser.ConfigParser) -> bool:
        """
        Abstract method to check a D-FAST MI analysis configuration is valid

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

    def _get_reach(self,
                   rivers : RiversObject,
                   config : configparser.ConfigParser):
        """
        Get the General branch reach, used in derived classes
        """
        branch_name = config.get("General","Branch", fallback="")

        if not any(branch.name == branch_name for branch in rivers.branches):
            raise LookupError(f"Branch not in file {branch_name}!")

        ibranch = next((i for i, branch in enumerate(rivers.branches) if branch.name == branch_name), -1)

        reach_name = config.get("General","Reach", fallback="")

        if not any(reach.name == reach_name for reach in rivers.branches[ibranch].reaches):
            raise LookupError(f"Reach not in file {reach_name}!")

        ireach = next((i for i, reach in enumerate(rivers.branches[ibranch].reaches) if reach.name == reach_name), -1)
        reach = rivers.branches[ibranch].reaches[ireach]
        return reach