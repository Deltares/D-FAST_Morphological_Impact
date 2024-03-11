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
import pathlib
from abc import ABC, abstractmethod
from typing import Tuple, Type, TypeVar
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.IReach import IReach
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import BoolVector, Vector

T = TypeVar('T', bound=IReach)

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
            An object containing the river data.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.        
        """

    def _get_reach(self,
                   rivers : RiversObject,
                   config : configparser.ConfigParser,
                   reach_type: Type[T]) -> T:
        """
        Get the General branch reach, used in derived classes
        """
        branch_name = config.get("General", "Branch", fallback="")
        if len(branch_name) <= 0:
            raise ValueError("Branch name cannot be empty")
        branch = rivers.get_branch(branch_name)

        if branch is None:
            raise LookupError(f"Branch not in file {branch_name}!")

        reach_name = config.get("General","Reach", fallback="")
        if len(reach_name) <= 0:
            raise ValueError("Reach name cannot be empty")        
        reach = branch.get_reach(reach_name)

        if reach is None:
            raise LookupError(f"Reach not in file {reach_name}!")
        
        if not isinstance(reach, reach_type) :
            raise TypeError(f"Created Reach {reach_name} in river configuration is not of type {reach_type}")

        return reach

    def _check_key_with_file_value(
            self,
            config : configparser.ConfigParser,
            cond : str,
            key: str
            ) -> bool:
        if not config.has_option(cond, key):
            ApplicationSettingsHelper.log_text(f"Please this condition {cond} is found, but '{key}' key is not set!")
            return False

        file = config.get(cond, key)
        if not pathlib.Path(file).exists():
            ApplicationSettingsHelper.log_text(f"Please this condition {cond} is found, but '{key}' value (file = {file}) does not exist!")
            return False
        return True
