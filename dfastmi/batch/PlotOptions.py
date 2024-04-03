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
from pathlib import Path
from typing import List, Optional, Tuple

import numpy
from pydantic import BaseModel, ConfigDict
from shapely.geometry.linestring import LineString

from dfastmi.batch.DFastUtils import get_zoom_extends
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser


class PlotOptions(BaseModel):
    """Option data object used to determine the plot possibilities"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    plotting: bool = False
    saveplot: bool = False
    saveplot_zoomed: bool = False
    closeplot: bool = False
    figure_save_directory: Path = None
    plot_extension: str = ".png"
    xykm: LineString = None
    kmbounds: Tuple[float, float] = (-math.inf, math.inf)
    kmzoom: List[Tuple[float, float]] = []
    xyzoom: List[Tuple[float, float, float, float]] = []

    def set_plotting_flags(
        self, rootdir: Path, display: bool, data: DFastMIConfigParser
    ):
        """
        Set dictionary key values to be used in the analysis runner.

        Arguments
        ---------
        rootdir : Path
            Reference directory for default output folders.
        display : bool
            Flag indicating text output to stdout.
        data : DFastMIConfigParser
            DFast MI application config file.
        """
        zoom_km_step = 1.0

        kmfile = self._get_riverkm_file(data)
        self.xykm = self._get_riverkm_linestring(kmfile)
        xykline = self._get_riverkm_coordinates(kmfile, self.xykm)
        self.kmbounds = self._get_riverkm_boundaries(
            display, data, len(kmfile) > 0, xykline
        )

        self.plotting = data.config_get(bool, "General", "Plotting", False)
        if self.plotting:
            self.saveplot = data.config_get(bool, "General", "SavePlots", True)
            if kmfile != "":
                self.saveplot_zoomed = data.config_get(
                    bool, "General", "SaveZoomPlots", False
                )
                zoom_km_step = max(
                    1.0, math.floor((self.kmbounds[1] - self.kmbounds[0]) / 10.0)
                )
                zoom_km_step = data.config_get(
                    float, "General", "ZoomStepKM", zoom_km_step
                )

            if zoom_km_step < 0.01:
                self.saveplot_zoomed = False

            if self.saveplot_zoomed:
                self.kmzoom, self.xyzoom = get_zoom_extends(
                    self.kmbounds[0], self.kmbounds[1], zoom_km_step, xykline
                )

            self.closeplot = data.config_get(bool, "General", "ClosePlots", False)

        # as appropriate check output dir for figures and file format
        self.figure_save_directory = self._set_output_figure_dir(
            rootdir, display, data, self.saveplot
        )
        self.plot_extension = self._get_figure_ext(data, self.saveplot)

    def _get_riverkm_file(self, data: DFastMIConfigParser) -> str:
        """
        Get the file specifying chainage along the reach of
        interest is needed for estimating the initial year dredging volumes.

        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        data : DFastMIConfigParser
            DFast MI application config file.

        Return
        ------
        kmfile : str
            A string to the RiverKM file location.
        """
        kmfile = data.config_get(str, "General", "RiverKM", "")
        return kmfile

    def _get_riverkm_linestring(self, kmfile: str) -> LineString:
        """
        Get the chainage in a LineString along the reach of interest is needed for estimating the initial year dredging volumes.

        Arguments
        ---------
        kmfile : str
            A string to the RiverKM file location.

        Return
        ------
        xykm : shapely.geometry.linestring.LineString
            LineString describing the chainage along the reach.
        """
        xykm = None
        if len(kmfile) > 0:
            xykm = DataTextFileOperations.get_xykm(kmfile)
        return xykm

    def _get_riverkm_coordinates(self, kmfile: str, xykm: LineString) -> numpy.ndarray:
        """
        Get the chainage in coordinates along the reach of interest is needed for estimating the initial year dredging volumes.

        Arguments
        ---------
        kmfile : str
            A string to the RiverKM file location.
        xykm : shapely.geometry.linestring.LineString
            LineString describing the chainage along the reach.

        Return
        ------
        xykline : numpy.ndarray
            Array with coordinates describing the chainage along the reach.
        """
        xykline = numpy.empty((0, 3))
        if len(kmfile) > 0:
            xykline = numpy.array(xykm.coords)
        return xykline

    def _get_riverkm_boundaries(
        self,
        display: bool,
        data: DFastMIConfigParser,
        kmfile_exists: bool,
        xykline: numpy.ndarray,
    ) -> Tuple[float, float]:
        """
        Get the chainage boundaries along the reach of interest
        is needed for estimating the initial year dredging volumes.

        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        data : DFastMIConfigParser
            DFast MI application config file.
        kmfile_exists : bool
            A boolean stating a RiverKM file is provided in the dfast mi configuration.
        xykline : numpy.ndarray
            Array with coordinates describing the chainage along the reach.

        Return
        ------
        kmbounds : Tuple[float, float]
            interest area clipped to the range low ([0]) to high ([1]) km
        """
        kmbounds = (-math.inf, math.inf)
        if kmfile_exists:
            kline = xykline[:, 2]
            kmbounds = data.config_get_range(
                "General", "Boundaries", (min(kline), max(kline))
            )
            if display:
                ApplicationSettingsHelper.log_text(
                    "clip_interest", dict={"low": kmbounds[0], "high": kmbounds[1]}
                )
        return kmbounds

    def _set_output_figure_dir(
        self, rootdir: Path, display: bool, data: DFastMIConfigParser, saveplot: bool
    ) -> Optional[Path]:
        """
        Read from the dfast mi configuration the output directory
        create when it doesn't exist or feedback that the content
        in the directory will be overwritten.

        Arguments
        ---------
        rootdir : Path
            Reference directory for default output folders.
        display : bool
            Flag indicating text output to stdout.
        data : DFastMIConfigParser
            DFast MI application config file.

        Return
        ------
        figdir : str
            The location where the plotted results will be stored.
        """
        if saveplot:
            default_figure_dir = rootdir.joinpath("figure")
            figdir = Path(
                data.config_get(str, "General", "FigureDir", default_figure_dir)
            )
            if display:
                ApplicationSettingsHelper.log_text(
                    "figure_dir", dict={"dir": str(figdir)}
                )
            if figdir.exists():
                if display:
                    ApplicationSettingsHelper.log_text(
                        "overwrite_dir", dict={"dir": str(figdir)}
                    )
            else:
                figdir.mkdir()
            return figdir
        return None

    def _get_figure_ext(self, data: DFastMIConfigParser, saveplot: bool) -> str:
        """
        Return expected file extensions for plotted figures.

        Arguments
        ---------
        data : DFastMIConfigParser
            Configuration of the analysis to be run.
        report : TextIO
            Text stream for log file.

        Return
        ------
        plot_ext : str
        """

        if saveplot:
            plot_ext = data.config_get(str, "General", "FigureExt", ".png")
        else:
            plot_ext = ".png"
        return plot_ext
