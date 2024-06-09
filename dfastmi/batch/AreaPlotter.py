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
from typing import List

import numpy
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import dfastmi.batch.plotting
import dfastmi.kernel.core
from dfastmi.batch.AreaDetector import AreaData
from dfastmi.batch.PlotOptions import PlotOptions


class AreaPlotter(ABC):
    """
    Abstract class used to plot the area.
    """

    _graph_title_of_the_total_area: str
    _template_graph_title_of_the_sub_areas: str
    _positive_up: bool

    def __init__(
        self,
        plotting_options: PlotOptions,
        plot_n: int,
        area_data: AreaData,
    ):
        """
        Arguments
        ---------
        plotting_options : PlotOptions
            Options for plotting.
        plot_n : int
            n for plotting.
        area_data: AreaData
            Class which holds the information regarding detected areas.
        """
        self._plotting_options = plotting_options
        self._plot_n = plot_n
        self._area_data = area_data

    def plot_areas(
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
        binvol: List[numpy.ndarray],
    ):
        """
        Plot the area data.

        Arguments
        ---------
        dzgemi : numpy.ndarray
            Yearly mean bed level change [m].
        areai : numpy.ndarray
            Array of length M containing the grid cell area [m2].
        wbin: numpy.ndarray
            Array of length N containing the index of the target width bin [-].
        wbin_labels: list[str]
            Array of length N containing the index of the target width bin [-].
        wthresh : numpy.ndarray
            Array containing the cross-stream coordinate boundaries between the width bins [m].
        siface : numpy.ndarray
            Array of length N containing the index of the source cell (range 0 to M-1) [-].
        afrac : numpy.ndarray
            Array of length N containing the fraction of the source cell associated with the target chainage bin [-].
        sbin : numpy.ndarray
            Array of length N containing the index of the target chainage bin [-].
        sthresh : numpy.ndarray
            Array containing the along-stream coordinate boundaries between the streamwise bins [m].
        kmid: numpy.ndarray
            Array of length N containing the location of points expressed as chainage.
        binvol : List[numpy.ndarray]
            List of arrays containing the total volume per streamwise bin [m3]. List length corresponds to number of width bins.
        """

        sbin_length: float = sthresh[1] - sthresh[0]

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
            sbin_length,
            binvol,
        )

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
        sbin_length: float,
        binvol: List[numpy.ndarray],
    ):
        if not self._plotting_options.plotting:
            return

        fig, ax = dfastmi.batch.plotting.plot_sedimentation(
            kmid,
            "chainage [km]",
            binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            self._graph_title_of_the_total_area,
            wbin_labels,
            positive_up=self._positive_up,
        )

        figure_base_name = self._graph_title_of_the_total_area.replace(" ", "_")
        self._save_figure(fig, ax, figure_base_name)

        if self._plot_n > 0:
            self._plot_figures_with_details_for_n_areas_with_largest_volumes(
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
            )

    def _plot_figures_with_details_for_n_areas_with_largest_volumes(
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
    ):
        volume_mean = self._area_data.volume[1:, :].mean(axis=0)
        sorted_list = numpy.argsort(volume_mean)[::-1]
        if len(sorted_list) <= self._plot_n:
            vol_thresh = 0.0
        else:
            vol_thresh = volume_mean[sorted_list[self._plot_n]]

        self._plot_certain_areas(
            volume_mean > vol_thresh,
            dzgemi,
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

    def _plot_certain_areas(
        self,
        condition: bool,
        dzgemi: numpy.ndarray,
        areai: numpy.ndarray,
        wbin: numpy.ndarray,
        wbin_labels: list[str],
        siface: numpy.ndarray,
        afrac: numpy.ndarray,
        sbin: numpy.ndarray,
        wthresh: numpy.ndarray,
        sthresh: numpy.ndarray,
        kmid: numpy.ndarray,
    ):
        indices = numpy.nonzero(condition)[0]
        sbin_length = sthresh[1] - sthresh[0]
        for ia in indices:
            dzgemi_filtered = dzgemi.copy()
            dzgemi_filtered[numpy.invert(self._area_data.area_list[ia])] = 0.0

            area_binvol = self._comp_binned_volumes(
                dzgemi_filtered, areai, wbin, siface, afrac, sbin, wthresh, sthresh
            )

            fig, ax = dfastmi.batch.plotting.plot_sedimentation(
                kmid,
                "chainage [km]",
                area_binvol,
                "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
                self._template_graph_title_of_the_sub_areas.format(ia + 1),
                wbin_labels,
                positive_up=self._positive_up,
            )

            figure_base_name = (
                self._template_graph_title_of_the_sub_areas.replace(" ", "_").format(
                    ia + 1
                )
                + "_volumes"
            )
            self._save_figure(fig, ax, figure_base_name)

    def _save_figure(self, fig: Figure, ax: Axes, figure_base_name: str):
        if not self._plotting_options.saveplot:
            return

        figbase = self._plotting_options.figure_save_directory / figure_base_name
        if self._plotting_options.saveplot_zoomed:
            dfastmi.batch.plotting.zoom_x_and_save(
                fig,
                ax,
                figbase,
                self._plotting_options.plot_extension,
                self._plotting_options.kmzoom,
            )
        figfile = figbase.with_suffix(self._plotting_options.plot_extension)
        dfastmi.batch.plotting.savefig(fig, figfile)

    def _comp_binned_volumes(
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


class SedimentationAreaPlotter(AreaPlotter):
    """
    Class used to plot the sedimentation area.
    """

    def __init__(
        self,
        plotting_options: PlotOptions,
        plot_n: int,
        area_data: AreaData,
    ):
        super().__init__(plotting_options, plot_n, area_data)
        self._template_graph_title_of_the_sub_areas = "sedimentation area {}"
        self._graph_title_of_the_total_area = "total sedimentation volume"
        self._positive_up = True


class ErosionAreaPlotter(AreaPlotter):
    """
    Class used to plot the erosion area.
    """

    def __init__(
        self,
        plotting_options: PlotOptions,
        plot_n: int,
        area_data: AreaData,
    ):
        super().__init__(plotting_options, plot_n, area_data)
        self._template_graph_title_of_the_sub_areas = "erosion area {}"
        self._graph_title_of_the_total_area = "total erosion volume"
        self._positive_up = False
