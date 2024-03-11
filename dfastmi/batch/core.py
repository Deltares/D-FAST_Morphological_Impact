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

from configparser import ConfigParser
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, TextIO
import sys
import os
import math
import numpy
import matplotlib
from packaging.version import Version

from dfastmi.batch.ConfigurationInitializerFactory import ConfigurationInitializerFactory
from dfastmi.batch.DFastUtils import get_zoom_extends
from dfastmi.io.ConfigFileOperations import ConfigFileOperations
from dfastmi.io.IBranch import IBranch
from dfastmi.io.IReach import IReach

from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import Vector
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser
from dfastmi.io.DataTextFileOperations import DataTextFileOperations

from dfastmi.batch import AnalyserAndReporterDflowfm
from dfastmi.batch import AnalyserAndReporterWaqua

from dfastmi.batch.FileNameRetrieverFactory import FileNameRetrieverFactory
from dfastmi.batch.FileNameRetriever import FileNameRetriever
from dfastmi.batch.FileNameRetrieverLegacy import FileNameRetrieverLegacy

import dfastmi.kernel.core
import dfastmi.plotting


WAQUA_EXPORT = "WAQUA export"
DFLOWFM_MAP = "D-Flow FM map"

def batch_mode(config_file: str, rivers: RiversObject, reduced_output: bool) -> None:
    """
    Run the program in batch mode.

    Load the configuration file and run the analysis.

    Arguments
    ---------
    config_file : str
        Name of the configuration file.
    rivers : RiversObject
        An object containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    """
    if reduced_output:
        ApplicationSettingsHelper.log_text("reduce_output")

    try:
        config = ConfigFileOperations.load_configuration_file(config_file)
        rootdir = os.path.dirname(config_file)
    except:
        print(sys.exc_info()[1])
    else:
        batch_mode_core(rivers, reduced_output, config, rootdir = rootdir)

def batch_mode_core(
    rivers: RiversObject, reduced_output: bool, config: ConfigParser, rootdir: str = "", gui: bool = False
) -> bool:
    """
    Run the analysis for a given configuration in batch mode.

    Arguments
    ---------
    rivers : RiversObject
        An object containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    config : configparser.ConfigParser
        Configuration of the analysis to be run.
    rootdir : str
        Reference directory for default output folders.
    gui : bool
        Flag indicating whether this routine is called from the GUI.

    Return
    ------
    success : bool
        Flag indicating whether the analysis could be completed successfully.
    """
    display = False
    data = DFastMIConfigParser(config)

    # check outputdir
    rootdir = _get_root_dir(rootdir)
    outputdir = _get_output_dir(rootdir, display, data)
    report = outputdir.joinpath(ApplicationSettingsHelper.get_filename("report.out")).open(mode="w", encoding="utf-8")

    _core_initialize(report)

    cfg_version = _get_verion(rivers, config)

    branch_name = config.get("General", "Branch", fallback="")
    branch = rivers.get_branch(branch_name)
    if not branch:
        ApplicationSettingsHelper.log_text("invalid_branch", dict={"branch": branch_name}, file=report)
        success = False
    else:
        reach_name = config.get("General", "Reach", fallback="")
        reach = branch.get_reach(reach_name)
        if not reach:
            ApplicationSettingsHelper.log_text(
                "invalid_reach", dict={"reach": reach_name, "branch": branch_name}, file=report
            )
            success = False
        else:
            success = _analyse_and_report(
                config,
                data,
                cfg_version,
                branch,
                reach,
                display,
                report,
                reduced_output,
                rootdir,
                outputdir,
                gui
            )

    ApplicationSettingsHelper.log_text("end", file=report)
    report.close()

    return success

def _get_riverkm_options(display : bool, data: DFastMIConfigParser):
    xykline = numpy.ndarray(shape=(3,0))
    kmbounds = (-math.inf, math.inf)
    xykm = None
    kmfile = data.config_get(str, "General", "RiverKM", "")
    if len(kmfile)>0:
        xykm = DataTextFileOperations.get_xykm(kmfile)
        xykline = numpy.array(xykm.coords)
        kline = xykline[:,2]
        kmbounds = data.config_get_range("General", "Boundaries", (min(kline), max(kline)))
        if display:
            ApplicationSettingsHelper.log_text("clip_interest", dict={"low": kmbounds[0], "high": kmbounds[1]})
    return xykline,kmfile,xykm,kmbounds

def _set_plotting_flags(rootdir:str, display:bool, data:DFastMIConfigParser, kmfile:str, xykline:numpy.ndarray, kmbounds:Tuple[float,float]):
    saveplot = False
    saveplot_zoomed = False
    zoom_km_step = 1.0
    kmzoom = []
    xyzoom = []
    closeplot = False

    plotting = data.config_get(bool, "General", "Plotting", False)
    if plotting:
        saveplot = data.config_get(bool, "General", "SavePlots", True)
        if kmfile != "":
            saveplot_zoomed = data.config_get(bool, "General", "SaveZoomPlots", False)
            zoom_km_step = max(1.0, math.floor((kmbounds[1]-kmbounds[0])/10.0))
            zoom_km_step = data.config_get(float, "General", "ZoomStepKM", zoom_km_step)

        if zoom_km_step < 0.01:
            saveplot_zoomed = False

        if saveplot_zoomed:
            kmzoom, xyzoom = get_zoom_extends(kmbounds[0], kmbounds[1], zoom_km_step, xykline)

        closeplot = data.config_get(bool, "General", "ClosePlots", False)

    # as appropriate check output dir for figures and file format
    figdir = _set_output_figure_dir(rootdir, display, data, saveplot)
    plot_ext = _get_figure_ext(data, saveplot)

    plotops = {'plotting': plotting, 'saveplot':saveplot, 'saveplot_zoomed':saveplot_zoomed, 'closeplot':closeplot, 'figdir': figdir, 'plot_ext': plot_ext, 'kmzoom': kmzoom, 'xyzoom': xyzoom}
    return plotops

def _set_output_figure_dir(rootdir, display, data, saveplot):
    if saveplot:
        figdir = Path(data.config_get(str,
                    "General", "FigureDir", Path(rootdir).joinpath("figure")))
        if display:
            ApplicationSettingsHelper.log_text("figure_dir", dict={"dir": str(figdir)})
        if figdir.exists():
            if display:
                ApplicationSettingsHelper.log_text("overwrite_dir", dict={"dir": str(figdir)})
        else:
            figdir.mkdir()
    else:
        figdir = ''
    return str(figdir)

def _get_figure_ext(data, saveplot):
    if saveplot:
        plot_ext = data.config_get(str, "General", "FigureExt", ".png")
    else:
        plot_ext = ''
    return plot_ext

def _log_report_mode_usage(config:ConfigParser, report:TextIO) -> int:
    """

    Return
    ------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).

    """
    mode_str = config.get("General", "Mode", fallback=DFLOWFM_MAP)
    if mode_str == WAQUA_EXPORT:
        imode = 0
        ApplicationSettingsHelper.log_text(
                    "results_with_input_waqua",
                    file=report,
                    dict={
                        "avgdzb": ApplicationSettingsHelper.get_filename("avgdzb.out"),
                        "maxdzb": ApplicationSettingsHelper.get_filename("maxdzb.out"),
                        "mindzb": ApplicationSettingsHelper.get_filename("mindzb.out"),
                    },
                )
    else:
        imode = 1
        ApplicationSettingsHelper.log_text(
                    "results_with_input_dflowfm",
                    file=report,
                    dict={"netcdf": ApplicationSettingsHelper.get_filename("netcdf.out")},
                )
    return imode

def _get_verion(rivers, config):
    cfg_version = config.get("General", "Version", fallback="")
    if Version(cfg_version) != rivers.version:
        raise LookupError(f"Version number of configuration file ({cfg_version}) must match version number of rivers file ({rivers.version})")
    cfg_version = Version(cfg_version)
    return cfg_version

def _core_initialize(report):
    prog_version = dfastmi.__version__
    ApplicationSettingsHelper.log_text("header", dict={"version": prog_version}, file=report)
    ApplicationSettingsHelper.log_text("limits", file=report)
    ApplicationSettingsHelper.log_text("===", file=report)

def _get_output_dir(rootdir, display, data):
    outputdir = Path(data.config_get(str, "General", "OutputDir", Path(rootdir).joinpath("output")))
    if outputdir.exists():
        if display:
            ApplicationSettingsHelper.log_text("overwrite_dir", dict={"dir": outputdir})
    else:
        outputdir.mkdir()
    return outputdir

def _get_root_dir(rootdir):
    if rootdir == "":
        rootdir = os.getcwd()
    return rootdir

def _count_discharges(discharges: Vector) -> int:
    """
    Count the number of non-empty discharges.

    Arguments
    ---------
    discharges : Vector
        Tuple of (at most) three characteristic discharges (Q).

    Returns
    -------
    n : int
        Number of non-empty discharges.
    """
    return sum([not q is None for q in discharges])


def _initialize_file_name_retriever_factory() -> FileNameRetrieverFactory:
    factory = FileNameRetrieverFactory()
    factory.register_creator(Version("1.0"), lambda needs_tide: FileNameRetrieverLegacy())
    factory.register_creator(Version("2.0"), FileNameRetriever)
    return factory

def get_filenames(
    imode: int,
    needs_tide: bool,
    config: Optional[ConfigParser] = None,
) -> Dict[Any, Tuple[str,str]]:
    """
    Extract the list of six file names from the configuration.

    Arguments
    ---------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).

    needs_tide : bool
        Specifies whether the tidal boundary is needed.

    config : Optional[configparser.ConfigParser]
        The variable containing the configuration (may be None for imode = 0).

    Returns
    -------
    filenames : Dict[Any, Tuple[str,str]]
        Dictionary of string tuples representing the D-Flow FM file names for
        each reference/with measure pair. The keys of the dictionary vary. They
        can be the discharge index, discharge value or a tuple of forcing
        conditions, such as a Discharge and Tide forcing tuple.
    """
    factory = _initialize_file_name_retriever_factory()

    if imode != 0:
        general_version = config.get("General", "Version", fallback= None)
    else:
        general_version = None

    if general_version:
        file_name_retriever_version = Version(general_version)
    else:
        file_name_retriever_version = None

    file_name_retriever = factory.generate(file_name_retriever_version, needs_tide)
    return file_name_retriever.get_file_names(config)

def _analyse_and_report(
    config : ConfigParser,
    data : DFastMIConfigParser,
    cfg_version : Version,
    branch : IBranch,
    reach: IReach,
    display: bool,
    report: TextIO,
    reduced_output: bool,
    rootdir: str,
    outputdir: str,
    gui : bool
) -> bool:
    """
    Perform analysis for any model.

    Depending on the mode select the appropriate analysis runner.

    Arguments
    ---------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).
    display : bool
        Flag indicating text output to stdout.
    report : TextIO
        Text stream for log file.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    reach : str
        Name of the reach.
    q_location : str
        Name of the location at which the discharge is defined.
    q_threshold : float
        Threshold discharge above which the measure is active.
    tstag : float
        Fraction of year that the river is stagnant.
    Q : Vector
        Array of discharges; one for each forcing condition.
    apply_q : BoolVector
        A tuple of 3 flags indicating whether each value should be used or not.
    T : Vector
        Fraction of year represented by each forcing condition.
    rsigma : Vector
        Array of relaxation factors; one per forcing condition.
    slength : float
        The expected yearly impacted sedimentation length.
    ucrit : float
        Critical flow velocity [m/s].
    filenames : Dict[Any, Tuple[str,str]]
        Dictionary of the names of the data file containing the simulation
        results to be processed. The conditions (discharge, wave conditions,
        ...) are the key in the dictionary. Per condition a tuple of two file
        names is given: a reference file and a file with measure.
    xykm : shapely.geometry.linestring.LineString
        Original river chainage line.
    needs_tide : bool
        Specifies whether the tidal boundary is needed.
    n_fields : int
        Number of fields to process (e.g. to cover a tidal period).
    tide_bc : Tuple[str, ...]
        Array of tidal boundary condition; one per forcing condition.
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.
    kmbounds : Tuple[float,float]
        Minimum and maximum chainage values indicating range of interest.
    outputdir : str
        Name of the output directory.
    plotops : Dict
        Dictionary of plot settings

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out.
    """
    initialized_config = ConfigurationInitializerFactory.generate(cfg_version, reach, config)

    xykline, kmfile, xykm, kmbounds = _get_riverkm_options(display, data)
    old_zmin_zmax = False

    # set plotting flags
    plotops = _set_plotting_flags(rootdir, display, data, kmfile, xykline, kmbounds)

    imode = _log_report_mode_usage(config, report)
    filenames = get_filenames(imode, initialized_config.needs_tide, config)
    success = False
    if imode == 0:
        success = AnalyserAndReporterWaqua.analyse_and_report_waqua(
            display,
            report,
            reduced_output,
            initialized_config.tstag,
            initialized_config.discharges,
            initialized_config.apply_q,
            initialized_config.time_fractions_of_the_year,
            initialized_config.rsigma,
            initialized_config.ucrit,
            old_zmin_zmax,
            outputdir,
        )
    else:
        success = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
            display,
            report,
            reach,
            branch.qlocation,
            initialized_config.q_threshold,
            initialized_config.tstag,
            initialized_config.discharges,
            initialized_config.apply_q,
            initialized_config.time_fractions_of_the_year,
            initialized_config.rsigma,
            initialized_config.slength,
            reach.normal_width,
            initialized_config.ucrit,
            filenames,
            xykm,
            initialized_config.needs_tide,
            initialized_config.n_fields,
            initialized_config.tide_bc,
            old_zmin_zmax,
            kmbounds,
            outputdir,
            plotops,
        )

    _log_length_estimate(report, initialized_config.slength)

    _finalize_plotting(plotops, gui)

    return success

def _finalize_plotting(plotops: dict[str,any], gui: bool):
    if plotops['plotting']:
        if plotops['closeplot']:
            matplotlib.pyplot.close("all")
        else:
            matplotlib.pyplot.show(block=not gui)

def _log_length_estimate(report, slength):
    if slength > 1:
        nlength = f"{int(slength)}"
    else:
        nlength = f"{slength}"
    ApplicationSettingsHelper.log_text(
        "length_estimate", dict={"nlength": nlength}, file=report
    )

def write_report(
    report: TextIO,
    reach: str,
    q_location: str,
    q_threshold: Optional[float],
    q_bankfull: float,
    q_stagnant: float,
    tstag: float,
    q_fit: Tuple[float, float],
    discharges: Vector,
    t: Vector,
    slength: float,
) -> None:
    """
    Write the analysis report to file.

    Arguments
    ---------
    report : TextIO
        Text stream for log file.
    reach : str
        The name of the selected reach.
    q_location : str
        The name of the discharge location.
    q_threshold : Optional[float]
        The discharge below which the measure is not flow-carrying (None if always flowing above 1000 m3/s or when barriers are opened).
    q_bankull : float
        The discharge at which the measure is bankfull.
    q_stagnant : float
        Discharge below which the river flow is negligible.
    tstag : float
        Fraction of year during which the flow velocity is negligible.
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    discharges : Vector
        A tuple of 3 discharges (Q) for which simulation results are (expected to be) available.
    t : Vector
        A tuple of 3 values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q.
    slength : float
        The expected yearly impacted sedimentation length.

    Returns
    -------
    None
    """
    ApplicationSettingsHelper.log_text("", file=report)
    ApplicationSettingsHelper.log_text("reach", dict={"reach": reach}, file=report)
    ApplicationSettingsHelper.log_text("", file=report)
    if not q_threshold is None:
        ApplicationSettingsHelper.log_text(
            "report_qthreshold",
            dict={"q": q_threshold, "border": q_location},
            file=report,
        )
    ApplicationSettingsHelper.log_text(
        "report_qbankfull", dict={"q": q_bankfull, "border": q_location}, file=report,
    )
    ApplicationSettingsHelper.log_text("", file=report)
    if q_stagnant > q_fit[0]:
        ApplicationSettingsHelper.log_text(
            "closed_barriers", dict={"ndays": int(365 * tstag)}, file=report
        )
        ApplicationSettingsHelper.log_text("", file=report)
    for i in range(3):
        if not discharges[i] is None:
            ApplicationSettingsHelper.log_text(
                "char_discharge",
                dict={"n": i + 1, "q": discharges[i], "border": q_location},
                file=report,
            )
            if i < 2:
                tdays = int(365 * t[i])
            else:
                tdays = max(
                    0, 365 - int(365 * t[0]) - int(365 * t[1]) - int(365 * tstag)
                )
            ApplicationSettingsHelper.log_text(
                "char_period", dict={"n": i + 1, "ndays": tdays}, file=report
            )
            if i < 2:
                ApplicationSettingsHelper.log_text("", file=report)
            else:
                ApplicationSettingsHelper.log_text("---", file=report)
    number_of_discharges = _count_discharges(discharges)
    if number_of_discharges == 1:
        ApplicationSettingsHelper.log_text("need_single_input", dict={"reach": reach}, file=report)
    else:
        ApplicationSettingsHelper.log_text(
            "need_multiple_input", dict={"reach": reach, "numq": number_of_discharges}, file=report,
        )

    stagenames = ["lowwater", "transition", "highwater"]
    # Code name of the discharge level.

    for i in range(3):
        if not discharges[i] is None:
            ApplicationSettingsHelper.log_text(
                stagenames[i], dict={"q": discharges[i], "border": q_location}, file=report
            )
    ApplicationSettingsHelper.log_text("---", file=report)
    if slength > 1:
        nlength = int(slength)
    else:
        nlength = slength
    ApplicationSettingsHelper.log_text("length_estimate", dict={"nlength": nlength}, file=report)
    ApplicationSettingsHelper.log_text("prepare_input", file=report)
