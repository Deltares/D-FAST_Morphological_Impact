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
    Reach
    ReachLegacy
    ReachAdvanced

"""
from abc import ABC
from typing import List

from dfastmi.io.CelerObject import ICelerObject
from dfastmi.io.IBranch import IBranch

class Reach(ABC):
    """
    Abstract base class with reach data information. Should never be instantiated.
    """
    name : str
    config_key_index : int
    normal_width : float
    ucritical : float
    qstagnant : float
    parent_branch : IBranch

    def __init__(self, reach_name : str = "Reach", reach_config_key_index:int = 1):
        self.name = reach_name
        self.config_key_index = reach_config_key_index


class ReachLegacy(Reach):
    """
    Derived class with reach data information used with legacy river configuration files.
    """
    proprate_high : float
    proprate_low : float
    qbankfull : float
    qmin : float
    qfit : tuple[float,float]
    qlevels : List[float]
    dq : tuple[float,float]


class ReachAdvanced(Reach):
    """
    Derived class with reach data information used with current (AKA v2) river configuration files.
    """
    hydro_q : List[float]
    hydro_t : List[float]
    auto_time : bool
    qfit : tuple[float,float]

    use_tide : bool
    tide_boundary_condition : List[float]

    celer_form : int
    celer_object : ICelerObject = None
