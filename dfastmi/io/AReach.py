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
"""
Module for Reach implementation

Classes:
    AReach   

"""
from dfastmi.io.IBranch import IBranch
from dfastmi.io.IReach import IReach


class AReach(IReach):
    """
    Abstract base class with reach data information. Should never be instantiated.
    """
    _name : str
    _config_key_index : int

    normal_width : float = 0.0
    ucritical : float = 0.0
    qstagnant : float = 0.0
    parent_branch : IBranch = None

    def __init__(self, reach_name : str = "Reach", reach_config_key_index:int = 1):
        super().__init__(_name=reach_name, _config_key_index = reach_config_key_index)
        self._name = reach_name
        self._config_key_index = reach_config_key_index

    @property
    def name(self) -> str:
        """Name of the reach"""
        return self._name

    @property
    def config_key_index(self) -> int:
        """Index of the Reach in the branch"""
        return self._config_key_index
