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

from typing import List

import numpy

from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from dfastmi.kernel.typehints import Vector


class OutputDataDflowfm:

    def __init__(
        self,
        rsigma: Vector,
        one_fm_filename: str,
        xn: numpy.ndarray,
        face_node_connectivity: numpy.ndarray,
        dzq: List[numpy.ndarray],
        dzgemi: numpy.ndarray,
        dzmaxi: numpy.ndarray,
        dzmini: numpy.ndarray,
        dzbi: List[numpy.ndarray],
        zmax_str: str,
        zmin_str: str,
        xykm_data: XykmData,
        sedimentation_data: SedimentationData,
    ):
        """
        Arguments
        ---------
            rsigma : Vector
                Array of relaxation factors; one per forcing condition.
            one_fm_filename : str
                First fm data filename.
            xn : numpy.ndarray
                X-coordinates of the mesh nodes.
            face_node_connectivity : numpy.ndarray
                Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
                Node indices are 0-based, hence the maximum node index is K-1.
            dzq : List[numpy.ndarray]
                Array containing equilibrium bed level change.
            dzgemi : numpy.ndarray
                Yearly mean bed level change.
            dzmaxi : numpy.ndarray
                Maximum bed level change.
            dzmini : numpy.ndarray
                Minimum bed level change.
            dzbi : List[numpy.ndarray]
                List of arrays containing the bed level change at the beginning of each respective discharge period.
            zmax_str : str
                maximum value of bed level change with or without dredging.
            zmin_str : str
                minimum value of bed level change with or without dredging.
            xykm_data : XykmData
                DTO of the XykmData.
            sedimentation_data : SedimentationData
                DTO of the SedimentationData.

        """
        self._rsigma: Vector = rsigma
        self._one_fm_filename: str = one_fm_filename
        self._xn: numpy.ndarray = xn
        self._face_node_connectivity: numpy.ndarray = face_node_connectivity
        self._dzq: List[numpy.ndarray] = dzq
        self._dzgemi: numpy.ndarray = dzgemi
        self._dzmaxi: numpy.ndarray = dzmaxi
        self._dzmini: numpy.ndarray = dzmini
        self._dzbi: List[numpy.ndarray] = dzbi
        self._zmax_str: str = zmax_str
        self._zmin_str: str = zmin_str
        self._xykm_data: XykmData = xykm_data
        self._sedimentation_data: SedimentationData = sedimentation_data

    @property
    def rsigma(self) -> Vector:
        """
        Array of relaxation factors; one per forcing condition.
        """
        return self._rsigma

    @property
    def one_fm_filename(self) -> str:
        """
        First fm data filename.
        """
        return self._one_fm_filename

    @property
    def xn(self) -> numpy.ndarray:
        """
        X-coordinates of the mesh nodes.
        """
        return self._xn

    @property
    def face_node_connectivity(self) -> numpy.ndarray:
        """
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
        Node indices are 0-based, hence the maximum node index is K-1.
        """
        return self._face_node_connectivity

    @property
    def dzq(self) -> List[numpy.ndarray]:
        """
        Array containing equilibrium bed level change.
        """
        return self._dzq

    @property
    def dzgemi(self) -> numpy.ndarray:
        """
        Yearly mean bed level change.
        """
        return self._dzgemi

    @property
    def dzmaxi(self) -> numpy.ndarray:
        """
        Maximum bed level change.
        """
        return self._dzmaxi

    @property
    def dzmini(self) -> numpy.ndarray:
        """
        Minimum bed level change.
        """
        return self._dzmini

    @property
    def dzbi(self) -> List[numpy.ndarray]:
        """
        List of arrays containing the bed level change at the beginning of each respective discharge period.
        """
        return self._dzbi

    @property
    def zmax_str(self) -> str:
        """
        maximum value of bed level change with or without dredging.
        """
        return self._zmax_str

    @property
    def zmin_str(self) -> str:
        """
        minimum value of bed level change with or without dredging.
        """
        return self._zmin_str

    @property
    def xykm_data(self) -> XykmData:
        """
        DTO of the XykmData.
        """
        return self._xykm_data

    @property
    def sedimentation_data(self) -> SedimentationData:
        """
        DTO of the SedimentationData.
        """
        return self._sedimentation_data
