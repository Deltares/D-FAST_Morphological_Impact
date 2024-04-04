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

from abc import ABC
from pathlib import Path
from typing import List

import numpy

import dfastmi.kernel.core
import dfastmi.plotting
from dfastmi.batch.PlotOptions import PlotOptions


class AreaReporter(ABC):

    _total_str: str
    _area_str: str
    _positive_up: bool

    def __init__(self, plotting_options: PlotOptions, xyzfil: Path):
        self._xyzfil = xyzfil
        self._plotting_options = plotting_options

    def report_areas(
        self,
        dzgemi: numpy.ndarray,
        areai: numpy.ndarray,
        wbin: numpy.ndarray,
        wbin_labels: list[str],
        wthresh: numpy.ndarray,
        siface: numpy.ndarray,
        afrac: numpy.ndarray,
        sbin: numpy.ndarray,
        sthresh: numpy.ndarray,
        kmid: numpy.ndarray,
        plot_n: int,
        volume: numpy.ndarray,
        sub_area_list: list,
    ):

        sbin_length = sthresh[1] - sthresh[0]
        binvol = self.comp_binned_volumes(
            numpy.maximum(dzgemi, 0.0),
            areai,
            wbin,
            siface,
            afrac,
            sbin,
            wthresh,
            sthresh,
        )

        self._write_xyz_file(wbin_labels, kmid, binvol)
        self._plot_areas(
            dzgemi,
            areai,
            wbin,
            wbin_labels,
            wthresh,
            siface,
            afrac,
            sbin,
            sthresh,
            kmid,
            plot_n,
            sbin_length,
            volume,
            sub_area_list,
            binvol,
        )

    def _write_xyz_file(self, wbin_labels, kmid, binvol):
        if self._xyzfil:
            # write a table of chainage and volume per width bin to file
            binvol2 = numpy.stack(binvol)
            with open(self._xyzfil, "w") as file:
                vol_str = " ".join('"{}"'.format(str) for str in wbin_labels)
                file.write('"chainage" ' + vol_str + "\n")
                for i in range(binvol2.shape[1]):
                    vol_str = " ".join("{:8.2f}".format(j) for j in binvol2[:, i])
                    file.write("{:8.2f} ".format(kmid[i]) + vol_str + "\n")

    def _plot_areas(
        self,
        dzgemi: numpy.ndarray,
        areai: numpy.ndarray,
        wbin: numpy.ndarray,
        wbin_labels: list[str],
        wthresh: numpy.ndarray,
        siface: numpy.ndarray,
        afrac: numpy.ndarray,
        sbin: numpy.ndarray,
        sthresh: numpy.ndarray,
        kmid: numpy.ndarray,
        plot_n: int,
        sbin_length: float,
        volume: numpy.ndarray,
        sub_area_list: list,
        binvol: List[numpy.ndarray],
    ):
        if self._plotting_options.plotting:
            fig, ax = dfastmi.plotting.plot_sedimentation(
                kmid,
                "chainage [km]",
                binvol,
                "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
                self._total_str,
                wbin_labels,
                positive_up=self._positive_up,
            )

            figure_base_name = self._total_str.replace(" ", "_")
            self._save_figure(fig, ax, figure_base_name)

            if plot_n > 0:
                # plot the figures with details for the N areas with largest volumes
                volume_mean = volume[1:, :].mean(axis=0)
                sorted_list = numpy.argsort(volume_mean)[::-1]
                if len(sorted_list) <= plot_n:
                    vol_thresh = 0.0
                else:
                    vol_thresh = volume_mean[sorted_list[plot_n]]
                self.plot_certain_areas(
                    volume_mean > vol_thresh,
                    dzgemi,
                    sub_area_list,
                    areai,
                    wbin,
                    wbin_labels,
                    siface,
                    afrac,
                    sbin,
                    wthresh,
                    sthresh,
                    kmid,
                )

    def plot_certain_areas(
        self,
        condition,
        dzgemi,
        area_list,
        areai,
        wbin,
        wbin_labels,
        siface,
        afrac,
        sbin,
        wthresh,
        sthresh,
        kmid,
    ):
        indices = numpy.nonzero(condition)[0]
        sbin_length = sthresh[1] - sthresh[0]
        for ia in indices:
            dzgemi_filtered = dzgemi.copy()
            dzgemi_filtered[numpy.invert(area_list[ia])] = 0.0

            area_binvol = self.comp_binned_volumes(
                dzgemi_filtered, areai, wbin, siface, afrac, sbin, wthresh, sthresh
            )

            fig, ax = dfastmi.plotting.plot_sedimentation(
                kmid,
                "chainage [km]",
                area_binvol,
                "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
                self._area_str.format(ia + 1),
                wbin_labels,
                positive_up=self._positive_up,
            )

            figure_base_name = (
                self._area_str.replace(" ", "_").format(ia + 1) + "_volumes"
            )
            self._save_figure(fig, ax, figure_base_name)

    def _save_figure(self, fig, ax, figure_base_name):
        if self._plotting_options.saveplot:
            figbase = self._plotting_options.figure_save_directory / figure_base_name
            if self._plotting_options.saveplot_zoomed:
                dfastmi.plotting.zoom_x_and_save(
                    fig,
                    ax,
                    figbase,
                    self._plotting_options.plot_extension,
                    self._plotting_options.kmzoom,
                )
            figfile = figbase.with_suffix(self._plotting_options.plot_extension)
            dfastmi.plotting.savefig(fig, figfile)

    def comp_binned_volumes(
        self,
        dzgem: numpy.ndarray,
        area: numpy.ndarray,
        wbin: numpy.ndarray,
        siface: numpy.ndarray,
        afrac: numpy.ndarray,
        sbin: numpy.ndarray,
        wthresh: numpy.ndarray,
        sthresh: numpy.ndarray,
    ) -> List[numpy.ndarray]:
        """
        Determine the volume per streamwise bin and width bin.

        Arguments
        ---------
        dzgem : numpy.ndarray
            Array of length M containing the bed level change per cell [m].
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
        sthresh : numpy.ndarray
            Array containing the along-stream coordinate boundaries between the streamwise bins [m].

        Returns
        -------
        binvol : List[numpy.ndarray]
            List of arrays containing the total volume per streamwise bin [m3]. List length corresponds to number of width bins.
        """

        dvol = dzgem * area

        n_wbin = len(wthresh) - 1
        n_sbin = len(sthresh) - 1
        sedbinvol: List[numpy.ndarray] = []

        # compute for every width bin the sedimentation volume
        for iw in range(n_wbin):
            lw = wbin == iw

            sbin_lw = sbin[lw]
            dvol_lw = dvol[siface[lw]]
            afrac_lw = afrac[lw]

            sedbinvol.append(
                numpy.bincount(sbin_lw, weights=dvol_lw * afrac_lw, minlength=n_sbin)
            )

        return sedbinvol


class SedimentationAreaReporter(AreaReporter):
    def __init__(self, plotting_options: PlotOptions, xyzfil: Path):
        super().__init__(plotting_options, xyzfil)
        self._area_str = "sedimentation area {}"
        self._total_str = "total sedimentation volume"
        self._positive_up = True


class ErosionAreaReporter(AreaReporter):
    def __init__(self, plotting_options: PlotOptions, xyzfil: Path = None):
        super().__init__(plotting_options, xyzfil)
        self._area_str = "erosion area {}"
        self._total_str = "total erosion volume"
        self._positive_up = False
