# -*- coding: utf-8 -*-
"""
Copyright (C) 2020 Stichting Deltares.

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

import numpy


class OutputDataWaqua:
    """
    Class that holds the output data that is written to the report for waqua.
    """

    def __init__(
        self,
        first_min_velocity_m: int,
        first_min_velocity_n: int,
        data_zgem: numpy.ndarray,
        data_zmax: numpy.ndarray,
        data_zmin: numpy.ndarray,
    ):
        """
        Init of the OutputDataWaqua.

        Arguments
        ---------
        first_min_velocity_m : int
            first minimum M index read (0 if reduced_output is False).
        first_min_velocity_n : int
            first minimum N index read (0 if reduced_output is False).
        dzgem : numpy.ndarray
            Yearly mean bed level change.
        dzmax : numpy.ndarray
            Maximum bed level change.
        dzmin : numpy.ndarray
            Minimum bed level change.
        """
        self.first_min_velocity_m = first_min_velocity_m
        self.first_min_velocity_n = first_min_velocity_n
        self.data_zgem = data_zgem
        self.data_zmax = data_zmax
        self.data_zmin = data_zmin
