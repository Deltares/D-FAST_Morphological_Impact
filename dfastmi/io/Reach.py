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
"""
from typing import List
from dfastmi.io.AReach import AReach

from dfastmi.io.CelerObject import ICelerObject


class Reach(AReach):
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
