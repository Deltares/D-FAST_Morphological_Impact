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
import math
from typing import Tuple

import numpy


class AreaDetector:

    @property
    def area(self) -> numpy.ndarray:
        """
        area
        """
        return self._area

    @property
    def volume(self) -> numpy.ndarray:
        """
        area volume
        """
        return self._volume

    @property
    def area_list(self) -> list:
        """
        List of sub areas
        """
        return self._area_list

    @property
    def total_area_weigth(self) -> numpy.ndarray:
        """
        total area weigth
        """
        return self._total_area_weigth

    def __init__(self) -> None:
        self._area: numpy.ndarray = numpy.zeros(0)
        self._volume: numpy.ndarray = numpy.zeros(0)
        self._area_list: list = []
        self._total_area_weigth: numpy.ndarray = numpy.zeros(0)

    def detect_areas(
        self,
        dzgemi: numpy.ndarray,
        dzmin: float,
        edgeface_indeces: numpy.ndarray,
        wght_area_tot: numpy.ndarray,
        areai: numpy.ndarray,
        wbin: numpy.ndarray,
        wthresh: numpy.ndarray,
        siface: numpy.ndarray,
        afrac: numpy.ndarray,
        sbin: numpy.ndarray,
        sthresh: numpy.ndarray,
        slength: float,
    ):

        sbin_length = sthresh[1] - sthresh[0]
        nwidth = wthresh[-1] - wthresh[0]
        sub_areai, n_sub_areas = self.detect_connected_regions(
            dzgemi > dzmin, edgeface_indeces
        )
        print("number of areas detected: ", n_sub_areas)

        area = numpy.zeros(n_sub_areas)
        volume = numpy.zeros((3, n_sub_areas))
        sub_area_list = []

        for ia in range(n_sub_areas):
            dzgemi_filtered = dzgemi.copy()
            dzgemi_filtered[sub_areai != ia] = 0.0
            sub_area_list.append(sub_areai == ia)

            volume[1, ia], wght_area_ia = self.comp_sedimentation_volume1(
                dzgemi_filtered,
                dzmin,
                areai,
                wbin,
                siface,
                afrac,
                sbin,
                wthresh,
                slength,
                sbin_length,
            )
            wght_area_tot = wght_area_tot + wght_area_ia

            volume[2, ia], area[ia], volume[0, ia] = self.comp_sedimentation_volume2(
                numpy.maximum(dzgemi_filtered, 0.0), dzmin, areai, slength, nwidth
            )

        sorted_list = numpy.argsort(area)[::-1]
        area = area[sorted_list]
        volume = volume[:, sorted_list]
        sub_area_list = [sub_area_list[ia] for ia in sorted_list]

        self._area = area
        self._volume = volume
        self._area_list = sub_area_list
        self._total_area_weigth = wght_area_tot

    def comp_sedimentation_volume1(
        self,
        dzgem: numpy.ndarray,
        dzmin: float,
        area: numpy.ndarray,
        wbin: numpy.ndarray,
        siface: numpy.ndarray,
        afrac: numpy.ndarray,
        sbin: numpy.ndarray,
        wthresh: numpy.ndarray,
        slength: float,
        sbin_length: float,
    ) -> Tuple[float, numpy.ndarray]:
        """
        Compute the initial year sedimentation volume.
        Algorithm 1.

        Arguments
        ---------
        dzgem : numpy.ndarray
            Array of length M containing the yearly mean bed level change per cell [m].
        dzmin : float
            Bed level changes (per cell) less than this threshold value are ignored [m].
        area : numpy.ndarray
            Array of length M containing the grid cell area [m2].
        wbin: numpy.ndarray
            Array of length N containing the index of the target width bin [-].
        siface : numpy.ndarray
            Array of length N containing the index of the source cell (range 0 to M-1) [-].
        afrac : numpy.ndarray
            Array of length N containing the fraction of the source cell associated with the target chainage bin [-].
        sbin : numpy.ndarray
            Array of length N containing the index of the target chainage bin [-].
        wthresh : numpy.ndarray
            Array containing the cross-stream coordinate boundaries between the width bins [m].
        slength : float
            The expected yearly impacted sedimentation length [m].
        sbin_length : float
            Size of bins in streamwise direction [m].

        Returns
        -------
        dvol : float
            Sedimentation volume [m3].
        """

        dzgem_filtered = dzgem.copy()
        dzgem_filtered[abs(dzgem) < dzmin] = 0.0
        dvol = dzgem_filtered * area

        n_wbin = len(wthresh) - 1
        n_faces = len(dvol)
        tot_dredge_vol = 0
        wght_all_dredge = numpy.zeros(dvol.shape)

        # compute for every width bin the sedimentation volume
        for iw in range(n_wbin):
            lw = wbin == iw

            tot_dredge_vol_wbin, wght_all_dredge_bin = (
                self.comp_sedimentation_volume1_one_width_bin(
                    dvol[siface[lw]],
                    sbin[lw],
                    afrac[lw],
                    siface[lw],
                    sbin_length,
                    slength,
                )
            )

            tot_dredge_vol = tot_dredge_vol + tot_dredge_vol_wbin
            wght_all_dredge = wght_all_dredge + numpy.bincount(
                siface[lw], weights=wght_all_dredge_bin, minlength=n_faces
            )

        return tot_dredge_vol, wght_all_dredge

    def comp_sedimentation_volume1_one_width_bin(
        self,
        dvol: numpy.ndarray,
        sbin: numpy.ndarray,
        afrac: numpy.ndarray,
        siface: numpy.ndarray,
        sbin_length: float,
        slength: float,
    ) -> Tuple[float, numpy.ndarray]:
        """
        Compute the initial year sedimentation volume.
        Algorithm 1.

        Arguments
        ---------


        Returns
        -------
        dvol : float
            Sedimentation volume [m3].
        """
        check_sed = dvol > 0.0
        dvol_sed = dvol[check_sed]
        sbin_sed = sbin[check_sed]
        siface_sed = siface[check_sed]
        afrac_sed = afrac[check_sed]

        tot_dredge_vol, wght_all_dredge_sed = self.comp_sedimentation_volume1_tot(
            dvol_sed, sbin_sed, afrac_sed, siface_sed, sbin_length, slength
        )

        wght_all_dredge = numpy.zeros(dvol.shape)
        wght_all_dredge[check_sed] = wght_all_dredge_sed

        return tot_dredge_vol, wght_all_dredge

    def comp_sedimentation_volume1_tot(
        self,
        sedvol: numpy.ndarray,
        sbin: numpy.ndarray,
        afrac: numpy.ndarray,
        siface: numpy.ndarray,
        sbin_length: float,
        slength: float,
    ) -> Tuple[float, numpy.ndarray]:
        """
        Compute the initial year sedimentation volume.
        Algorithm 1.

        Arguments
        ---------


        Returns
        -------
        dvol : float
            Sedimentation volume [m3].
        sedbinvol : List[Optional[numpy.ndarray]]
            List of arrays containing the total sedimentation volume per streamwise bin [m3]. List length corresponds to number of width bins.
        erobinvol : List[Optional[numpy.ndarray]]
            List of arrays containing the total erosion volume per streamwise bin [m3]. List length corresponds to number of width bins.
        """
        index = numpy.argsort(sbin)

        dredge_vol = 0.0
        wght = numpy.zeros(siface.shape)

        if len(index) > 0:
            ibprev = -999
            slength1 = slength
            for i in range(len(index)):
                ii = index[i]
                ib = sbin[ii]
                if ib == ibprev:  # same index, same weight
                    pass

                else:  # next index
                    frac = max(0.0, min(slength1 / sbin_length, 1.0))
                    ibprev = ib
                    slength1 = slength1 - sbin_length

                if not math.isclose(frac, 0.0):
                    wght[ii] = wght[ii] + frac * afrac[ii]
                    dredge_vol = dredge_vol + frac * sedvol[ii] * afrac[ii]

        return dredge_vol, wght

    def comp_sedimentation_volume2(
        self,
        dzgem: numpy.ndarray,
        dzmin: float,
        area: numpy.ndarray,
        slength: float,
        nwidth: float,
    ) -> Tuple[float, float, float]:
        """
        Compute the initial year sedimentation volume.
        Algorithm 2.

        Arguments
        ---------
        dzgem : numpy.ndarray
            Array of length M containing the yearly mean bed level change per cell [m].
        dzmin : float
            Bed level changes (per cell) less than this threshold value are ignored [m].
        area : numpy.ndarray
            Array of length M containing the grid cell area [m2].
        slength : float
            The expected yearly impacted sedimentation length [m].
        nwidth : float
            Normal river width (from rivers configuration file) [m].

        Returns
        -------
        dvol : float
            Sedimentation volume [m3].
        """
        iface = numpy.nonzero(dzgem > dzmin)
        dzgem_clip = dzgem[iface]
        area_clip = area[iface]

        dvol_eq = (dzgem_clip * area_clip).sum()
        area_eq = area_clip.sum()
        dz_eq = dvol_eq / area_eq
        area_1y = slength * nwidth
        if area_eq < area_1y:
            dvol = dvol_eq
        else:
            dvol = dz_eq * area_1y

        print(dzmin)
        print(
            "dz_mean = {:.6f} m, width = {:.6f} m, length = {:.6f} m, volume = {:.6f} m3".format(
                dz_eq, nwidth, slength, dvol
            )
        )
        return dvol, area_eq, dvol_eq

    def detect_connected_regions(
        self, fcondition: numpy.ndarray, edgeface_indeces: numpy.ndarray
    ) -> Tuple[numpy.ndarray, int]:
        """
        Detect regions of faces for which the fcondition equals True.

        Arguments
        ---------
        fcondition : numpy.ndarray
            Boolean array of length M: one boolean per face.
        edgeface_indeces : numpy.ndarray
            N x 2 array containing the indices of neighbouring faces.
            Maximum face index is M-1.

        Returns
        -------
        partition : numpy.ndarray
            Integer array of length M: for all faces at which fcondition is True, the integer indicates the region that the face assigned to.
            Contains -1 for faces at which fcondition is False.
        nregions : int
            Number of regions detected.
        """
        partition = -numpy.ones(fcondition.shape[0], dtype=numpy.int64)

        ncells = fcondition.sum()
        partition[fcondition] = numpy.arange(ncells)

        efc = edgeface_indeces[fcondition[edgeface_indeces].all(axis=1), :]
        nlinks = efc.shape[0]

        anychange = True
        while anychange:
            anychange = False

            for j in range(nlinks):
                m = partition[efc[j]].min()
                if not (partition[efc[j]] == m).all():
                    anychange = True
                    partition[efc[j]] = m

        parts, ipart = numpy.unique(partition, return_inverse=True)
        ipart = ipart - 1

        return ipart, len(parts) - 1
