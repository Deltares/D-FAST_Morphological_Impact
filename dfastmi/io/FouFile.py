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

from typing import Optional

import numpy as np

from dfastmi.io.OutputFile import OutputFile


class FouFile(OutputFile):
    def x_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the x-velocity at faces.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.
        """
        u0 = self.read_face_variable(
            "Last 003: U-component of cell-centre velocity, last values",
            time_index_from_last=time_index_from_last,
        )
        return u0

    def y_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the y-velocity at faces.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.
        """
        v0 = self.read_face_variable(
            "Last 004: V-component of cell-centre velocity, last values",
            time_index_from_last=time_index_from_last,
        )
        return v0

    def water_depth(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the y-velocity at faces.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.
        """
        s0 = self.read_face_variable(
            "Last 001: water level, last values",
            time_index_from_last=time_index_from_last,
        )
        zb = self.read_face_variable("flow element center bedlevel (bl)")
        h0 = s0 - zb
        return h0
