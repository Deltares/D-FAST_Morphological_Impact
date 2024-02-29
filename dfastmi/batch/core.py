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

from typing import Optional, List, Dict, Any, Tuple, TextIO
import sys
from dfastmi.io.Reach import ReachAdvanced
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.core import Vector, BoolVector, QRuns
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
from dfastmi.io.FileUtils import FileUtils
from dfastmi.io.ConfigFileOperations import ConfigFileOperations

from dfastmi.batch import AnalyserAndReporterDflowfm
from dfastmi.batch import AnalyserAndReporterWaqua
from dfastmi.batch import ConfigurationChecker
from dfastmi.batch import FileNameRetriever

import os
import math
import numpy
import dfastmi.kernel.core
import dfastmi.plotting

import matplotlib
import configparser
import shapely
from packaging import version

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
        A dictionary containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    """
    if reduced_output:
        ApplicationSettingsHelper.log_text("reduce_output")

    try:
        config = load_configuration_file(config_file)
        rootdir = os.path.dirname(config_file)
    except:
        print(sys.exc_info()[1])
    else:
        batch_mode_core(rivers, reduced_output, config, rootdir = rootdir)

def batch_mode_core(
    rivers: RiversObject, reduced_output: bool, config: configparser.ConfigParser, rootdir: str = "", gui: bool = False
) -> bool:
    """
    Run the analysis for a given configuration in batch mode.

    Arguments
    ---------
    rivers : RiversObject
        A dictionary containing the river data.
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
    Q1 : QRuns
    apply_q1 : Tuple[bool, bool, bool]
    Q : Vector
    apply_q : BoolVector

    display = False
    data = DFastMIConfigParser(config)
    
    # check outputdir
    if rootdir == "":
        rootdir = os.getcwd()
    outputdir = data.config_get(str, "General", "OutputDir", rootdir + os.sep + "output")
    if os.path.exists(outputdir):
        if display:
            ApplicationSettingsHelper.log_text("overwrite_dir", dict={"dir": outputdir})
    else:
        os.makedirs(outputdir)
    report = open(outputdir + os.sep + ApplicationSettingsHelper.get_filename("report.out"), "w")

    prog_version = dfastmi.__version__
    ApplicationSettingsHelper.log_text("header", dict={"version": prog_version}, file=report)
    ApplicationSettingsHelper.log_text("limits", file=report)
    ApplicationSettingsHelper.log_text("===", file=report)

    cfg_version = config["General"]["Version"]
    
    if version.parse(cfg_version) != rivers.version:
        raise Exception(
            "Version number of configuration file ({}) must match version number of rivers file ({})".format(
                cfg_version,
                rivers.version
            )
        )
    
    branch_name = config["General"]["Branch"]
    try:
        ibranch = next((i for i, branch in enumerate(rivers.branches) if branch.name == branch_name), -1)
    except:
        ApplicationSettingsHelper.log_text("invalid_branch", dict={"branch": branch_name}, file=report)
        success = False
    else:
        reach_name = config["General"]["Reach"]
        try:
            ireach = next((i for i, reach in enumerate(rivers.branches[ibranch].reaches) if reach.name == reach_name), -1)
            reach = rivers.branches[ibranch].reaches[ireach]
        except:
            ApplicationSettingsHelper.log_text(
                "invalid_reach", dict={"reach": reach_name, "branch": branch_name}, file=report
            )
            success = False
        else:
            nwidth = reach.normal_width
            q_location = rivers.branches[ibranch].qlocation
            tide_bc: Tuple[str, ...] = ()
            
            if version.parse(cfg_version) == version.parse("1"):
                # version 1
                [Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity] = ConfigurationChecker.get_levels_v1(reach, config, nwidth)
                needs_tide = False
                n_fields = 1

            else:
                # version 2
                q_stagnant = reach.qstagnant
                if "Qthreshold" in config["General"]:
                    q_threshold = float(config["General"]["Qthreshold"])
                else:
                    q_threshold = q_stagnant
                [Q, apply_q, time_mi, tstag, T, rsigma, celerity] = get_levels_v2(reach, q_threshold, nwidth)
                needs_tide = reach.tide
                if needs_tide:
                    tide_bc = reach.tide_bc
                    n_fields = int(config["General"]["NFields"])
                    if n_fields == 1:
                        raise Exception("Unexpected combination of tides and NFields = 1!")
                else:
                    n_fields = 1

            slength = dfastmi.kernel.core.estimate_sedimentation_length(time_mi, celerity)
            
            try:
                ucrit = float(config["General"]["Ucrit"])
            except:
                ucrit = reach.ucritical
            ucritMin = 0.01
            ucrit = max(ucritMin, ucrit)
            mode_str = config["General"].get("Mode",DFLOWFM_MAP)
            if mode_str == WAQUA_EXPORT:
                mode = 0
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
                mode = 1
                ApplicationSettingsHelper.log_text(
                    "results_with_input_dflowfm",
                    file=report,
                    dict={"netcdf": ApplicationSettingsHelper.get_filename("netcdf.out")},
                )
            filenames = get_filenames(mode, needs_tide, config)
            old_zmin_zmax = False
            kmfile = data.config_get(str, "General", "RiverKM", "")
            if kmfile != "":
                xykm = DataTextFileOperations.get_xykm(kmfile)
                xykline = numpy.array(xykm)
                kline = xykline[:,2]
                kmbounds = data.config_get_range("General", "Boundaries", (min(kline), max(kline)))
                if display:
                    ApplicationSettingsHelper.log_text("clip_interest", dict={"low": kmbounds[0], "high": kmbounds[1]})
            else:
                kmbounds = (-math.inf, math.inf)
                xykm = None

            # set plotting flags
            
            plotting = data.config_get(bool, "General", "Plotting", False)
            if plotting:
                saveplot = data.config_get(bool, "General", "SavePlots", True)
                if kmfile != "":
                    saveplot_zoomed = data.config_get(bool, "General", "SaveZoomPlots", False)
                    zoom_km_step = max(1.0, math.floor((kmbounds[1]-kmbounds[0])/10.0))
                    zoom_km_step = data.config_get(float, "General", "ZoomStepKM", zoom_km_step)
                else:
                    saveplot_zoomed = False
                    zoom_km_step = 1.0
                if zoom_km_step < 0.01:
                    saveplot_zoomed = False
                if saveplot_zoomed:
                    kmzoom, xyzoom = get_zoom_extends(kmbounds[0], kmbounds[1], zoom_km_step, xykline)
                else:
                    kmzoom = []
                    xyzoom = []
                closeplot = data.config_get(bool, "General", "ClosePlots", False)
            else:
                saveplot = False
                saveplot_zoomed = False
                kmzoom = []
                xyzoom = []
                closeplot = False
    
            # as appropriate check output dir for figures and file format
            if saveplot:
                figdir = data.config_get(str,
                    "General", "FigureDir", rootdir + os.sep + "figure"
                )
                if display:
                    ApplicationSettingsHelper.log_text("figure_dir", dict={"dir": figdir})
                if os.path.exists(figdir):
                    if display:
                        ApplicationSettingsHelper.log_text("overwrite_dir", dict={"dir": figdir})
                else:
                    os.makedirs(figdir)
                plot_ext = data.config_get(str, "General", "FigureExt", ".png")
            else:
                figdir = ''
                plot_ext = ''
            
            plotops = {'plotting': plotting, 'saveplot':saveplot, 'saveplot_zoomed':saveplot_zoomed, 'closeplot':closeplot, 'figdir': figdir, 'plot_ext': plot_ext, 'kmzoom': kmzoom, 'xyzoom': xyzoom}

            success = analyse_and_report(
                mode,
                display,
                report,
                reduced_output,
                reach,
                q_location,
                q_threshold,
                tstag,
                Q,
                apply_q,
                T,
                rsigma,
                slength,
                nwidth,
                ucrit,
                filenames,
                xykm,
                needs_tide,
                n_fields,
                tide_bc,
                old_zmin_zmax,
                kmbounds,
                outputdir,
                plotops,
            )

            if slength > 1:
                nlength = "{}".format(int(slength))
            else:
                nlength = "{}".format(slength)
            ApplicationSettingsHelper.log_text(
                "length_estimate", dict={"nlength": nlength}, file=report
            )

            if plotops['plotting']:
                if plotops['closeplot']:
                    matplotlib.pyplot.close("all")
                else:
                    matplotlib.pyplot.show(block=not gui)

    ApplicationSettingsHelper.log_text("end", file=report)
    report.close()

    return success

def get_levels_v2(
    reach : ReachAdvanced, q_threshold: float, nwidth: float
) -> (Vector, BoolVector, Vector, float, Vector, Vector, Vector):
    """
    Determine discharges, times, etc. for version 2 analysis

    Arguments
    ---------
    rivers : RiversObject
        A dictionary containing the river data.
    ibranch : int
        Number of selected branch.
    ireach : int
        Number of selected reach.
    q_threshold : float
        River discharge at which the measure becomes active [m3/s].
    nwidth : float
        Normal river width (from rivers configuration file) [m].

    Return
    ------
    Q : Vector
        Array of discharges; one for each forcing condition [m3/s].
    apply_q : BoolVector
        A list of flags indicating whether the corresponding entry in Q should be used.
    time_mi : Vector
        A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].
    tstag : float
        Fraction of year during which flow velocity is considered negligible [-].
    T : Vector
        A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
    rsigma : Vector
        A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
    celerity : Vector
        A vector of values each representing the bed celerity for the period given by the corresponding entry in Q [m/s].
    """
    q_stagnant = reach.qstagnant
    Q = reach.hydro_q
    apply_q = (True,) * len(Q)
    if reach.autotime:
        q_fit = reach.qfit
        T, time_mi = batch_get_times(Q, q_fit, q_stagnant, q_threshold)
    else:
        T = reach.hydro_t
        sumT = sum(T)
        T = tuple(t / sumT for t in T)
        time_mi = tuple(0 if Q[i]<q_threshold else T[i] for i in range(len(T)))
    
    # determine the bed celerity based on the input settings
    cform = reach.celer_form
    if cform == 1:
        prop_q = reach.celer_object.prop_q
        prop_c = reach.celer_object.prop_c
        celerity = tuple(dfastmi.kernel.core.get_celerity(q, prop_q, prop_c) for q in Q)
    elif cform == 2:
        cdisch = reach.celer_object.cdisch
        celerity = tuple(cdisch[0]*pow(q,cdisch[1]) for q in Q)
    
    # set the celerity equal to 0 for discharges less or equal to q_stagnant
    celerity = tuple({False:0.0, True:celerity[i]}[Q[i]>q_stagnant] for i in range(len(Q)))
    
    # check if all celerities are equal to 0. If so, the impact would be 0.
    all_zero = True
    for i in range(len(Q)):
        if celerity[i] < 0.0:
            raise Exception("Invalid negative celerity {} m/s encountered for discharge {} m3/s!".format(celerity[i],Q[i]))
        elif celerity[i] > 0.0:
            all_zero = False
    if all_zero:
        raise Exception("The celerities can't all be equal to zero for a measure to have any impact!")
    
    rsigma = dfastmi.kernel.core.relax_factors(Q, T, q_stagnant, celerity, nwidth)
    tstag = 0

    return (Q, apply_q, time_mi, tstag, T, rsigma, celerity)

def countQ(Q: Vector) -> int:
    """
    Count the number of non-empty discharges.

    Arguments
    ---------
    Q : Vector
        Tuple of (at most) three characteristic discharges.

    Returns
    -------
    n : int
        Number of non-empty discharges.
    """
    return sum([not q is None for q in Q])

def batch_get_times(Q: Vector, q_fit: Tuple[float, float], q_stagnant: float, q_threshold: float) -> Vector:
    """
    Get the representative time span for each discharge.

    Arguments
    ---------
    Q : Vector
        a vector of discharges included in hydrograph [m3/s].
    q_fit : float
        A discharge and dicharge change determining the discharge exceedance curve [m3/s].
    q_stagnant : float
        Discharge below which flow conditions are stagnant [m3/s].
    q_threshold : float
        Discharge below which the measure has no effect (due to measure design) [m3/s].

    Results
    -------
    T : Vector
        A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
    time_mi : Vector
        A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].
    """
    
    # make sure that the discharges are sorted low to high
    qvec = numpy.array(Q)
    sorted = numpy.argsort(qvec)
    q = qvec[sorted]
    
    t = numpy.zeros(q.shape)
    tmi = numpy.zeros(q.shape)
    p_do = 1.0
    p_th = math.exp(min(0.0, q_fit[0] - max(q_stagnant, q_threshold))/q_fit[1])
    for i in range(len(q)):
        if q[i] <= q_stagnant:
            # if the current discharge is in the stagnant regime
            if i < len(q)-1 and q[i+1] > q_stagnant:
                # if the next discharge is not in the stagnant regime, then the stagnant discharge is the boundary between the two regimes
                # this will associate the whole stagnant period with this discharge since p_do = 1
                q_up = q_stagnant
                p_up = math.exp(min(0.0, q_fit[0] - q_up)/q_fit[1])
            else:
                # if the next discharge is also in the stagnant regime, keep p_up = p_do = 1
                # this will associate zero time with this discharge
                p_up = 1.0
        elif i < len(q)-1:
            # if the current discharge is above the stagnant regime and more (higher) discharges follow, select the geometric midpoint as transition
            q_up = math.sqrt(q[i] * q[i+1])
            p_up = math.exp(min(0.0, q_fit[0] - q_up)/q_fit[1])
        else:
            # if there are no higher discharges, associate this discharge with the whole remaining range until "infinite discharge"
            # q_up = inf
            p_up = 0.0
        t[i] = p_do - p_up
        
        if q[i] <= q_threshold:
            # if the measure is inactive for the current discharge, this discharge range may still be associated with impact at the high discharge end
            tmi[i] = max(0.0, p_th - p_up)
        else:
            # if the measure is active for the current discharge, the impact of this discharge range may be reduced at the low discharge end
            tmi[i] = min(p_th, p_do) - p_up
        p_do = p_up
    
    # correct in case the sorting of the discharges changed the order
    tvec = numpy.zeros(q.shape)
    tvec[sorted] = t
    T = tuple(ti for ti in tvec)

    tvec_mi = numpy.zeros(q.shape)
    tvec_mi[sorted] = tmi
    time_mi = tuple(ti for ti in tvec_mi)

    return T, time_mi

def _initialize_file_name_retriever_factory() -> FileNameRetriever.FileNameRetrieverFactory:
    factory = FileNameRetriever.FileNameRetrieverFactory()
    factory.register_creator(version.Version("1.0"), lambda needs_tide: FileNameRetriever.FileNameRetrieverLegacy())
    factory.register_creator(version.Version("2.0"), lambda needs_tide: FileNameRetriever.FileNameRetriever(needs_tide))
    return factory

def get_filenames(
    imode: int,
    needs_tide: bool,
    config: Optional[configparser.ConfigParser] = None,
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
        file_name_retriever_version = version.Version(general_version)
    else:
        file_name_retriever_version = None
        
    file_name_retriever = factory.generate(file_name_retriever_version, needs_tide)
    return file_name_retriever.get_file_names(config)

def analyse_and_report(
    imode: int,
    display: bool,
    report: TextIO,
    reduced_output: bool,
    reach: str,
    q_location: str,
    q_threshold: float,
    tstag: float,
    Q: Vector,
    apply_q: BoolVector,
    T: Vector,
    rsigma: Vector,
    slength: float,
    nwidth: float,
    ucrit: float,
    filenames: Dict[Any, Tuple[str,str]],
    xykm: shapely.geometry.linestring.LineString,
    needs_tide: bool,
    n_fields: int,
    tide_bc: Tuple[str, ...],
    old_zmin_zmax: bool,
    kmbounds: Tuple[float,float],
    outputdir: str,
    plotops: Dict,
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
    if imode == 0:
        return AnalyserAndReporterWaqua.analyse_and_report_waqua(
            display,
            report,
            reduced_output,
            reach,
            q_location,
            tstag,
            Q,
            apply_q,
            T,
            rsigma,
            slength,
            ucrit,
            old_zmin_zmax,
            outputdir,
        )
    else:
        return AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
            display,
            report,
            reach,
            q_location,
            q_threshold,
            tstag,
            Q,
            apply_q,
            T,
            rsigma,
            slength,
            nwidth,
            ucrit,
            filenames,
            xykm,
            needs_tide,
            n_fields,
            tide_bc,
            old_zmin_zmax,
            kmbounds,
            outputdir,
            plotops,
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
    Q: Vector,
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
    Q : Vector
        A tuple of 3 discharges for which simulation results are (expected to be) available.
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
        if not Q[i] is None:
            ApplicationSettingsHelper.log_text(
                "char_discharge",
                dict={"n": i + 1, "q": Q[i], "border": q_location},
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
    nQ = countQ(Q)
    if nQ == 1:
        ApplicationSettingsHelper.log_text("need_single_input", dict={"reach": reach}, file=report)
    else:
        ApplicationSettingsHelper.log_text(
            "need_multiple_input", dict={"reach": reach, "numq": nQ}, file=report,
        )
    for i in range(3):
        if not Q[i] is None:
            ApplicationSettingsHelper.log_text(
                stagename(i), dict={"q": Q[i], "border": q_location}, file=report
            )
    ApplicationSettingsHelper.log_text("---", file=report)
    if slength > 1:
        nlength = int(slength)
    else:
        nlength = slength
    ApplicationSettingsHelper.log_text("length_estimate", dict={"nlength": nlength}, file=report)
    ApplicationSettingsHelper.log_text("prepare_input", file=report)

def config_to_absolute_paths(
    rootdir: str, config: configparser.ConfigParser
) -> configparser.ConfigParser:
    """
    Convert a configuration object to contain absolute paths (for editing).

    Arguments
    ---------
    rootdir : str
        The path to be used as base for the absolute paths.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with absolute or relative paths.

    Returns
    -------
    aconfig : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with only absolute paths.
    """
    for key in ("RiverKM", "FigureDir", "OutputDir"):
        if key in config["General"]:
            config["General"][key] = FileUtils.absolute_path(
                rootdir, config["General"][key]
            )
    for qstr in config.keys():
        if "Reference" in config[qstr]:
            config[qstr]["Reference"] = FileUtils.absolute_path(
                rootdir, config[qstr]["Reference"]
            )
        if "WithMeasure" in config[qstr]:
            config[qstr]["WithMeasure"] = FileUtils.absolute_path(
                rootdir, config[qstr]["WithMeasure"]
            )
    return config

def load_configuration_file(filename: str) -> configparser.ConfigParser:
    """
    Open a configuration file and return a configuration object with absolute paths.

    Arguments
    ---------
    filename : str
        The name of the file: all relative paths in the configuration will be assumed relative to this.

    Raises
    ------
    Exception
        If the configuration file does not include version information.
        If the version number in the configuration file is not equal to 1.0.

    Returns
    -------
    aconfig : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with only absolute paths.
    """
    config = configparser.ConfigParser()
    with open(filename, "r") as configfile:
        config.read_file(configfile)
    try:
        file_version = config["General"]["Version"]
    except:
        raise Exception("No version information in the file!")

    if version.parse(file_version) == version.parse("1") or version.parse(file_version) == version.parse("2"):
        section = config["General"]
        branch = section["Branch"]
        reach = section["Reach"]
    else:
        raise Exception("Unsupported version number {} in the file!".format(file_version))

    rootdir = os.path.dirname(filename)
    return config_to_absolute_paths(rootdir, config)

def check_configuration(rivers: RiversObject, config: configparser.ConfigParser) -> bool:
    """
    Check if an analysis configuration is valid.

    Arguments
    ---------
    rivers: RiversObject
        A dictionary containing the river data.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis.

    Returns
    -------
    success : bool
        Boolean indicating whether the D-FAST MI analysis configuration is valid.
    """
    try:
        cfg_version = config["General"]["Version"]
        
        if version.parse(cfg_version) != rivers.version:
            return False
        if version.parse(cfg_version) == version.parse("1.0"):
            return ConfigurationChecker.check_configuration_v1(rivers, config)
        else:
            return ConfigurationChecker.check_configuration_v2(rivers, config)
    except SystemExit as e:
        raise e
    except:
        return False

def config_to_relative_paths(
    rootdir: str, config: configparser.ConfigParser
) -> configparser.ConfigParser:
    """
    Convert a configuration object to contain relative paths (for saving).

    Arguments
    ---------
    rootdir : str
        The path to be used as base for the absolute paths.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with only absolute paths.

    Returns
    -------
    rconfig : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with as much as possible relative paths.
    """
    for key in ("RiverKM", "FigureDir", "OutputDir"):
        if key in config["General"]:
            config["General"][key] = FileUtils.relative_path(
                rootdir, config["General"][key]
            )
    for qstr in config.keys():
        if "Reference" in config[qstr]:
            config[qstr]["Reference"] = FileUtils.relative_path(
                rootdir, config[qstr]["Reference"]
            )
        if "WithMeasure" in config[qstr]:
            config[qstr]["WithMeasure"] = FileUtils.relative_path(
                rootdir, config[qstr]["WithMeasure"]
            )
    return config

def save_configuration_file(filename: str, config):
    """
    Convert a configuration to relative paths and save to file.

    Arguments
    ---------
    filename : str
        The name of the configuration file to be saved.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis to be saved.

    Returns
    -------
    None
    """
    rootdir = os.path.dirname(filename)
    config = config_to_relative_paths(rootdir, config)
    ConfigFileOperations.write_config(filename, config)

def stagename(i: int) -> str:
    """
    Code name of the discharge level.

    Arguments
    ---------
    i : int
        Integer level specification.

    Returns
    -------
    name : str
        Name of the discharge level.
    """
    stagenames = ["lowwater", "transition", "highwater"]
    return stagenames[i]

def get_zoom_extends(km_min: float, km_max: float, zoom_km_step: float, xykline: numpy.ndarray) -> List[Tuple[float, float]]:
    """
    Zoom .

    Arguments
    ---------
    km_min : float
        Minimum value for the chainage range of interest.
    km_max : float
        Maximum value for the chainage range of interest.
    zoom_km_step : float
        Preferred chainage length of zoom box.
    xykline : numpy.ndarray 
        Array containing the x,y and chainage data of a line.

    Returns
    -------
    kmzoom : List[Tuple[float, float]]
        Zoom ranges for plots with chainage along x-axis.
    xyzoom : List[Tuple[float, float, float, float]]
        Zoom ranges for xy-plots.
    """

    zoom_km_bin = (km_min, km_max, zoom_km_step)
    zoom_km_bnd = get_km_bins(zoom_km_bin, type=0, adjust=True)
    eps = 0.1 * zoom_km_step

    kmzoom: List[Tuple[float, float]] = []
    xyzoom: List[Tuple[float, float, float, float]] = []
    for i in range(len(zoom_km_bnd)-1):
        km_min = zoom_km_bnd[i] - eps
        km_max = zoom_km_bnd[i + 1] + eps

        # only append zoom range if there are any chainage points in that range
        # (might be none if there is a chainage discontinuity in the region of
        # interest)
        irange = (xykline[:,2] >= km_min) & (xykline[:,2] <= km_max)
        if any(irange):
           kmzoom.append((km_min, km_max))
           
           range_crds = xykline[irange, :]
           x = range_crds[:, 0]
           y = range_crds[:, 1]
           xmin = min(x)
           xmax = max(x)
           ymin = min(y)
           ymax = max(y)
           xyzoom.append((xmin, xmax, ymin, ymax))

    return kmzoom, xyzoom

def get_km_bins(km_bin: Tuple[float, float, float], type: int = 2, adjust: bool = False) -> numpy.ndarray:
    """
    [identical to dfastbe.kernel.get_km_bins]
    Get an array of representative chainage values.
    
    Arguments
    ---------
    km_bin : Tuple[float, float, float]
        Tuple containing (start, end, step) for the chainage bins
    type : int
        Type of characteristic chainage values returned
            0: all bounds (N+1 values)
            1: lower bounds (N values)
            2: upper bounds (N values) - default
            3: mid points (N values)
    adjust : bool
        Flag indicating whether the step size should be adjusted to include an integer number of steps
    
    Returns
    -------
    km : numpy.ndarray
        Array containing the chainage bin upper bounds
    """
    km_step = km_bin[2]
    nbins = int(math.ceil((km_bin[1] - km_bin[0]) / km_step))
    
    lb = 0
    ub = nbins + 1
    dx = 0.0
    
    if adjust:
        km_step = (km_bin[1] - km_bin[0]) / nbins

    if type == 0:
        # all bounds
        pass
    elif type == 1:
        # lower bounds
        ub = ub - 1
    elif type == 2:
        # upper bounds
        lb = lb + 1
    elif type == 3:
        # midpoint values
        ub = ub - 1
        dx = km_bin[2] / 2

    km = km_bin[0] + dx + numpy.arange(lb, ub) * km_step

    return km