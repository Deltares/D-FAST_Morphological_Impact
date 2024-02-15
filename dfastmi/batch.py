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

from typing import Optional, List, Union, Dict, Any, Tuple, TextIO
import sys
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.core import Vector, BoolVector, QRuns
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.RiverParameterData import RiverParameterData
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
from dfastmi.io.GridOperations import GridOperations
from dfastmi.io.FileUtils import FileUtils
from dfastmi.io.ConfigFileOperations import ConfigFileOperations

import os
import math
import numpy
import dfastmi.kernel.core
import dfastmi.plotting
import matplotlib
import configparser
import shapely
from packaging import version
import netCDF4

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
    data = RiverParameterData(config)
    
    # check outputdir
    if rootdir == "":
        rootdir = os.getcwd()
    outputdir = data.config_get_str("General", "OutputDir", rootdir + os.sep + "output")
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
                rvr_version
            )
        )
    
    branch = config["General"]["Branch"]
    try:
        ibranch = rivers.branches.index(branch)
    except:
        ApplicationSettingsHelper.log_text("invalid_branch", dict={"branch": branch}, file=report)
        success = False
    else:
        reach = config["General"]["Reach"]
        try:
            ireach = rivers.allreaches[ibranch].index(reach)
        except:
            ApplicationSettingsHelper.log_text(
                "invalid_reach", dict={"reach": reach, "branch": branch}, file=report
            )
            success = False
        else:
            nwidth = rivers.normal_width[ibranch][ireach]
            q_location = rivers.qlocations[ibranch]
            tide_bc: Tuple[str, ...] = ()
            
            if version.parse(cfg_version) == version.parse("1"):
                # version 1
                [Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity] = get_levels_v1(rivers, ibranch, ireach, config, nwidth)
                needs_tide = False
                n_fields = 1

            else:
                # version 2
                q_stagnant = rivers.qstagnant[ibranch][ireach]
                if "Qthreshold" in config["General"]:
                    q_threshold = float(config["General"]["Qthreshold"])
                else:
                    q_threshold = q_stagnant
                [Q, apply_q, time_mi, tstag, T, rsigma, celerity] = get_levels_v2(rivers, ibranch, ireach, q_threshold, nwidth)
                needs_tide = rivers.tide[ibranch][ireach]
                if needs_tide:
                    tide_bc = rivers.tide_bc[ibranch][ireach]
                    n_fields = int(config["General"]["NFields"])
                    if n_fields == 1:
                        raise Exception("Unexpected combination of tides and NFields = 1!")
                else:
                    n_fields = 1

            slength = dfastmi.kernel.core.estimate_sedimentation_length(time_mi, celerity)

            reach = rivers.allreaches[ibranch][ireach]
            try:
                ucrit = float(config["General"]["Ucrit"])
            except:
                ucrit = rivers.ucritical[ibranch][ireach]
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
            kmfile = data.config_get_str("General", "RiverKM", "")
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
            
            plotting = data.config_get_bool("General", "Plotting", False)
            if plotting:
                saveplot = data.config_get_bool("General", "SavePlots", True)
                if kmfile != "":
                    saveplot_zoomed = data.config_get_bool("General", "SaveZoomPlots", False)
                    zoom_km_step = max(1.0, math.floor((kmbounds[1]-kmbounds[0])/10.0))
                    zoom_km_step = data.config_get_float("General", "ZoomStepKM", zoom_km_step)
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
                closeplot = data.config_get_bool("General", "ClosePlots", False)
            else:
                saveplot = False
                saveplot_zoomed = False
                kmzoom = []
                xyzoom = []
                closeplot = False
    
            # as appropriate check output dir for figures and file format
            if saveplot:
                figdir = data.config_get_str(
                    "General", "FigureDir", rootdir + os.sep + "figure"
                )
                if display:
                    ApplicationSettingsHelper.log_text("figure_dir", dict={"dir": figdir})
                if os.path.exists(figdir):
                    if display:
                        ApplicationSettingsHelper.log_text("overwrite_dir", dict={"dir": figdir})
                else:
                    os.makedirs(figdir)
                plot_ext = data.config_get_str("General", "FigureExt", ".png")
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


def get_levels_v1(
    rivers: RiversObject, ibranch: int, ireach: int, config: configparser.ConfigParser, nwidth: float
) -> (Vector, BoolVector, float, Vector, float, Vector, Vector, Vector):
    """
    Determine discharges, times, etc. for version 1 analysis

    Arguments
    ---------
    rivers : RiversObject
        A dictionary containing the river data.
    ibranch : int
        Number of selected branch.
    ireach : int
        Number of selected reach.
    config : configparser.ConfigParser
        Configuration of the analysis to be run.
    nwidth : float
        Normal river width (from rivers configuration file) [m].

    Return
    ------
    Q : Vector
        Array of discharges; one for each forcing condition [m3/s].
    apply_q : BoolVector
        A list of flags indicating whether the corresponding entry in Q should be used.
    q_threshold : float
        River discharge at which the measure becomes active [m3/s].
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
    q_stagnant = rivers.qstagnant[ibranch][ireach]
    celerity_hg = rivers.proprate_high[ibranch][ireach]
    celerity_lw = rivers.proprate_low[ibranch][ireach]

    (
        all_q,
        q_threshold,
        q_bankfull,
        q_fit,
        Q1,
        apply_q1,
        tstag,
        T,
        rsigma,
    ) = batch_get_discharges(
        rivers, ibranch, ireach, config, q_stagnant, celerity_hg, celerity_lw, nwidth
    )
    Q = Q1
    apply_q = apply_q1
    time_mi = tuple(0 if Q[i] is None or Q[i]<=q_stagnant else T[i] for i in range(len(T)))
    celerity = (celerity_lw, celerity_hg, celerity_hg)
    
    return (Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity)


def get_levels_v2(
    rivers: RiversObject, ibranch: int, ireach: int, q_threshold: float, nwidth: float
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
    q_stagnant = rivers.qstagnant[ibranch][ireach]
    Q = rivers.hydro_q[ibranch][ireach]
    apply_q = (True,) * len(Q)
    if rivers.autotime[ibranch][ireach]:
        q_fit = rivers.qfit[ibranch][ireach]
        T, time_mi = batch_get_times(Q, q_fit, q_stagnant, q_threshold)
    else:
        T = rivers.hydro_t[ibranch][ireach]
        sumT = sum(T)
        T = tuple(t / sumT for t in T)
        time_mi = tuple(0 if Q[i]<q_threshold else T[i] for i in range(len(T)))
    
    # determine the bed celerity based on the input settings
    cform = rivers.cform[ibranch][ireach]
    if cform == 1:
        prop_q = rivers.prop_q[ibranch][ireach]
        prop_c = rivers.prop_c[ibranch][ireach]
        celerity = tuple(dfastmi.kernel.core.get_celerity(q, prop_q, prop_c) for q in Q)
    elif cform == 2:
        cdisch = rivers.cdisch[ibranch][ireach]
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


def batch_get_discharges(
    rivers: RiversObject,
    ibranch: int,
    ireach: int,
    config: configparser.ConfigParser,
    q_stagnant: float,
    celerity_hg: float,
    celerity_lw: float,
    nwidth: float,
) -> Tuple[
    bool,
    Optional[float],
    float,
    Tuple[float, float],
    QRuns,
    Tuple[bool, bool, bool],
    float,
    Vector,
    Vector,
]:
    """
    Get the simulation discharges in batch mode (no user interaction).

    Arguments
    ---------
    rivers : RiversObject
        A dictionary containing the river data.
    ibranch : int
        Number of selected branch.
    ireach : int
        Number of selected reach.
    config : configparser.ConfigParser
        Configuration of the analysis to be run.
    q_stagnant : float
        Discharge below which the river flow is negligible [m3/s].
    celerity_hg : float
        Bed celerity during transitional and flood periods (from rivers configuration file) [m/s].
    celerity_lw : float
        Bed celerity during low flow period (from rivers configuration file) [m/s].
    nwidth : float
        Normal river width (from rivers configuration file) [m].

    Results
    -------
    all_q : bool
        Flag indicating whether simulation data for all discharges is available.
    q_threshold : Optional[float]
        River discharge at which the measure becomes active [m3/s].
    q_bankfull : float
        River discharge at which the measure is bankfull [m3/s].
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file) [m3/s].
    Q : QRuns
        Tuple of (at most) three characteristic discharges [m3/s].
    apply_q : Tuple[bool, bool, bool]
        A list of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.
    tstag : float
        Fraction of year during which flow velocity is considered negligible [-].
    T : Vector
        A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
    rsigma : Vector
        A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
    """
    q_threshold: Optional[float]

    stages = ApplicationSettingsHelper.get_text("stage_descriptions")

    q_stagnant = rivers.qstagnant[ibranch][ireach]
    q_fit = rivers.qfit[ibranch][ireach]
    q_levels = rivers.qlevels[ibranch][ireach]
    dq = rivers.dq[ibranch][ireach]

    q_min = rivers.qmin[ibranch][ireach]
    try:
        q_threshold = float(config["General"]["Qthreshold"])
    except:
        q_threshold = None

    if q_threshold is None or q_threshold < q_levels[1]:
        q_bankfull = float(config["General"]["Qbankfull"])
    else:
        q_bankfull = 0

    Q, apply_q = dfastmi.kernel.core.char_discharges(q_levels, dq, q_threshold, q_bankfull)

    tstag, T, rsigma = dfastmi.kernel.core.char_times(
        q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
    )

    QList = list(Q)
    for iq in range(3):
        if apply_q[iq]:
            QList[iq] = float(config["Q{}".format(iq + 1)]["Discharge"])
        else:
            QList[iq] = None
    Q = (QList[0], QList[1], QList[2])

    all_q = True
    return (
        all_q,
        q_threshold,
        q_bankfull,
        q_fit,
        Q,
        apply_q,
        tstag,
        T,
        rsigma,
    )


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
    filenames: Dict[Any, Tuple[str,str]]
    if imode == 0 or config is None:
        filenames = {}
    elif version.parse(config["General"]["Version"]) == version.parse("1"):
        filenames = get_filenames_version1(config)
    else:
        filenames = get_filenames_version2(needs_tide, config)

    return filenames


def get_filenames_version1(
    config: Optional[configparser.ConfigParser] = None,
) -> Dict[Any, Tuple[str,str]]:
    """
    Extract the list of six file names from the configuration.
    This routine is valid for version 1 configuration files.

    Arguments
    ---------
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
    filenames: Dict[Any, Tuple[str,str]]
    key: Union[Tuple[float, int], float]
    filenames = {}
    for i in range(3):
        qstr = "Q{}".format(i + 1)
        if qstr in config:
            reference = cfg_get(config, qstr, "Reference")
            measure = cfg_get(config, qstr, "WithMeasure")
            filenames[i] = (reference, measure)

    return filenames


def get_filenames_version2(
    needs_tide: bool,
    config: Optional[configparser.ConfigParser] = None,
) -> Dict[Any, Tuple[str,str]]:
    """
    Extract the list of 2N file names from the configuration.
    This routine is valid for version 2 configuration files.

    Arguments
    ---------
    needs_tide : bool
        Specifies whether the tidal boundary is needed.

    config : Optional[configparser.ConfigParser]
        The variable containing the configuration (may be None for if 0).

    Returns
    -------
    filenames : Dict[Any, Tuple[str,str]]
        Dictionary of string tuples representing the D-Flow FM file names for
        each reference/with measure pair. The keys of the dictionary vary. They
        can be the discharge index, discharge value or a tuple of forcing
        conditions, such as a Discharge and Tide forcing tuple.
    """
    filenames: Dict[Any, Tuple[str,str]]
    key: Union[Tuple[float, int], float]
    filenames = {}
    i = 0
    while True:
        i = i + 1
        CSTR = "C{}".format(i)
        if CSTR in config:
            Q = float(cfg_get(config, CSTR, "Discharge"))
            reference = cfg_get(config, CSTR, "Reference")
            measure = cfg_get(config, CSTR, "WithMeasure")
            if needs_tide:
               T = cfg_get(config, CSTR, "TideBC")
               key = (Q,T)
            else:
               key = Q
            filenames[key] = (reference, measure)
        else:
            break

    return filenames


def cfg_get(config: configparser.ConfigParser, chap: str, key: str) -> str:
    """
    Get a single entry from the analysis configuration structure.
    Raise clear exception message when it fails.

    Arguments
    ---------
    config : Optional[configparser.ConfigParser]
        The variable containing the configuration (may be None for imode = 0).
    chap : str
        The name of the chapter in which to search for the key.
    key : str
        The name of the key for which to return the value.

    Raises
    ------
    Exception
        If the key in the chapter doesn't exist.

    Returns
    -------
    value : str
        The value specified for the key in the chapter.
    """
    try:
         return config[chap][key]
    except:
        pass
    raise Exception(
        'Keyword "{}" is not specified in group "{}" of analysis configuration file.'.format(
            key,
            chap,
        )
    )


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
        return analyse_and_report_waqua(
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
        return analyse_and_report_dflowfm(
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


def analyse_and_report_waqua(
    display: bool,
    report: TextIO,
    reduced_output: bool,
    reach: str,
    q_location: str,
    tstag: float,
    Q: Vector,
    apply_q: BoolVector,
    T: Vector,
    rsigma: Vector,
    slength: float,
    ucrit: float,
    old_zmin_zmax: bool,
    outputdir: str
) -> bool:
    """
    Perform analysis based on WAQUA data.

    Read data from samples files exported from WAQUA simulations, perform
    analysis and write the results to three SIMONA boxfiles.

    Arguments
    ---------
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
        Name of the location at which the discharge is
    tstag : float
        Number of days that the river is stagnant.
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
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.
    outputdir : str
        Name of the output directory.

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out.
    """
    success = True
    first_discharge = True
    
    dzq : List[Optional[Union[float, numpy.ndarray]]]
    dzq = [None] * len(Q)
    for i in range(3):
        if success and apply_q[i]:
            if first_discharge:
                dzq[i], firstm, firstn = get_values_waqua3(
                    i+1, Q[i], ucrit, display, report, reduced_output
                )
                first_discharge = False
            else:
                dzq[i] = get_values_waqua1(i+1, Q[i], ucrit, display, report, reduced_output)
            if dzq[i] is None:
                success = False
        else:
            dzq[i] = 0.0

    if success:
        if display:
            ApplicationSettingsHelper.log_text("char_bed_changes")
            
        if tstag > 0:
            dzq = [dzq[0], 0.0, dzq[1], dzq[2]]
            T = (T[0], tstag, T[1], T[2])
            rsigma = (rsigma[0], 1.0, rsigma[1], rsigma[2])
        
        # main_computation now returns new pointwise zmin and zmax
        data_zgem, data_zmax, data_zmin, dzb = dfastmi.kernel.core.main_computation(
            dzq, T, rsigma
        )
        if old_zmin_zmax:
            # get old zmax and zmin
            data_zmax = dzb[0]
            data_zmin = dzb[1]

        DataTextFileOperations.write_simona_box(
            outputdir + os.sep + ApplicationSettingsHelper.get_filename("avgdzb.out"), data_zgem, firstm, firstn
        )
        DataTextFileOperations.write_simona_box(
            outputdir + os.sep + ApplicationSettingsHelper.get_filename("maxdzb.out"), data_zmax, firstm, firstn
        )
        DataTextFileOperations.write_simona_box(
            outputdir + os.sep + ApplicationSettingsHelper.get_filename("mindzb.out"), data_zmin, firstm, firstn
        )

    return success


def analyse_and_report_dflowfm(
    display: bool,
    report: TextIO,
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
    kmbounds: Tuple[float, float],
    outputdir: str,
    plotops: Dict,
) -> bool:
    """
    Perform analysis based on D-Flow FM data.

    Read data from D-Flow FM output files, perform analysis and write the results
    to a netCDF UGRID file similar to D-Flow FM.

    Arguments
    ---------
    display : bool
        Flag indicating text output to stdout.
    report : TextIO
        Text stream for log file.
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
        Name of output directory.
    plotops : Dict
        Dictionary of plot settings

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out.
    """
    key: Union[Tuple[float, int], float]

    first_discharge = True
    missing_data = False
    one_fm_filename: Union[None, str] = None
    
    # determine the name of the first FM data file that will be used
    if 0 in filenames.keys(): # the keys are 0,1,2
        for i in range(3):
            if not missing_data and not Q[i] is None:
                one_fm_filename = filenames[i][0]
                break
    else: # the keys are the conditions
        for i in range(len(Q)):
            if not missing_data and not Q[i] is None:
                q = Q[i]
                if needs_tide:
                    t = tide_bc[i]
                    key = (q,t)
                else:
                    key = q
                if rsigma[i] == 1 or Q[i] <= q_threshold:
                    # no celerity or measure not active, so ignore field
                    pass
                elif key in filenames.keys():
                    one_fm_filename = filenames[key][0]
                    break
                else:
                    if needs_tide:
                        ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=report)
                    else:
                        ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=report)
                    ApplicationSettingsHelper.log_text("end_program", file=report)
                    missing_data = True

    if one_fm_filename is None:
        print("The measure is not active for any of the checked conditions.")
        missing_data = True

    if missing_data:
        return missing_data
    
    if display:
        ApplicationSettingsHelper.log_text('-- load mesh')
    xn, yn, FNC = get_xynode_connect(one_fm_filename)
    
    if xykm is None:
        # keep all nodes and faces
        keep = numpy.full(xn.shape, True)
        xni, yni, FNCi, iface, inode = filter_faces_by_node_condition(xn, yn, FNC, keep)
        xmin = xn.min()
        xmax = xn.max()
        ymin = yn.min()
        ymax = yn.max()
        dxi = None
        dyi = None
        xykline = None
        
    else:
        dnmax = 3000.0    
        if display:
            ApplicationSettingsHelper.log_text('-- identify region of interest')
        # add call to dfastbe.io.clip_path_to_kmbounds?
        print("buffer")
        xybuffer = xykm.buffer(dnmax)
        bbox = xybuffer.envelope.exterior
        print("prepare")
        xybprep = shapely.prepared.prep(xybuffer)
    
        print("prepare filter step 1")
        xmin = bbox.coords[0][0]
        xmax = bbox.coords[1][0]
        ymin = bbox.coords[0][1]
        ymax = bbox.coords[2][1]
        keep = (xn > xmin) & (xn < xmax) & (yn > ymin) & (yn < ymax)
        print("prepare filter step 2")
        for i in range(xn.size):
            if keep[i] and not xybprep.contains(shapely.geometry.Point((xn[i], yn[i]))):
                keep[i] = False
    
        print("apply filter")
        xni, yni, FNCi, iface, inode = filter_faces_by_node_condition(xn, yn, FNC, keep)
        interest_region = numpy.zeros(FNC.shape[0], dtype=numpy.int64)
        interest_region[iface] = 1
    
        #if display:
        #    ApplicationSettingsHelper.log_text('-- get centres') # note that this should be the circumference point
        #xfi = face_mean(xni, FNCi)
        #yfi = face_mean(yni, FNCi)
    
        xykline = numpy.array(xykm)
    
        # project all nodes onto the line, obtain the distance along (sni) and normal (dni) the line
        # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
        xyline = xykline[:,:2]
        kline = xykline[:,2]
        sline = distance_along_line(xyline)
        # convert chainage bounds to distance along line bounds
        ikeep = numpy.logical_and(kline >= kmbounds[0], kline <= kmbounds[1])
        sline_r = sline[ikeep]
        sbounds = (min(sline_r), max(sline_r))
    
        # project all nodes onto the line, obtain the distance along (sfi) and normal (nfi) the line
        # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
        if display:
            ApplicationSettingsHelper.log_text('-- project')
        sni, nni = proj_xy_line(xni, yni, xyline)
        sfi = face_mean(sni, FNCi)
        #nfi = face_mean(nni, FNCi)
    
        # determine chainage values of each cell
        if display:
            ApplicationSettingsHelper.log_text('-- chainage')
        kfi = distance_to_chainage(sline, xykline[:,2], sfi)
    
        # determine line direction for each cell
        if display:
            ApplicationSettingsHelper.log_text('-- direction')
        dxi, dyi = get_direction(xyline, sfi)
    
        if display:
            ApplicationSettingsHelper.log_text('-- done')
    
    dzq = [None] * len(Q)
    if 0 in filenames.keys(): # the keys are 0,1,2
        for i in range(3):
            if not missing_data and not Q[i] is None:
                dzq[i] = get_values_fm(i+1, Q[i], ucrit, report, filenames[i], n_fields, dxi, dyi, iface)
                if dzq[i] is None:
                    missing_data = True
            else:
                dzq[i] = 0
    else: # the keys are the conditions
        for i in range(len(Q)):
            if not missing_data and not Q[i] is None:
                q = Q[i]
                if needs_tide:
                    t = tide_bc[i]
                    key = (q,t)
                else:
                    t = 0
                    key = q
                if rsigma[i] == 1:
                    # no celerity, so ignore field
                    dzq[i] = 0
                elif key in filenames.keys():
                    if t > 0:
                        n_fields_request = n_fields
                    else:
                        n_fields_request = 1
                    dzq[i] = get_values_fm(i+1, q, ucrit, report, filenames[key], n_fields_request, dxi, dyi, iface)
                else:
                    if t > 0:
                        ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=report)
                    else:
                        ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=report)
                    ApplicationSettingsHelper.log_text("end_program", file=report)
                    missing_data = True
            else:
                dzq[i] = 0

    if not missing_data:
        if display:
            ApplicationSettingsHelper.log_text("char_bed_changes")
            
        if tstag > 0:
            dzq = (dzq[0], dzq[0], dzq[1], dzq[2])
            T = (T[0], tstag, T[1], T[2])
            rsigma = (rsigma[0], 1.0, rsigma[1], rsigma[2])
            
        # main_computation now returns new pointwise zmin and zmax
        dzgemi, dzmaxi, dzmini, dzbi = dfastmi.kernel.core.main_computation(
            dzq, T, rsigma
        )
        if old_zmin_zmax:
            # get old zmax and zmin
            dzmaxi = dzbi[0]
            zmax_str = "maximum bed level change after flood without dredging"
            dzmini = dzbi[1]
            zmin_str = "minimum bed level change after low flow without dredging"
        else:
            zmax_str = "maximum value of bed level change without dredging"
            zmin_str = "minimum value of bed level change without dredging"
        
        if display:
            ApplicationSettingsHelper.log_text('writing_output')
        meshname, facedim = GridOperations.get_mesh_and_facedim_names(one_fm_filename)
        dst = outputdir + os.sep + ApplicationSettingsHelper.get_filename("netcdf.out")
        GridOperations.copy_ugrid(one_fm_filename, meshname, dst)
        nc_fill = netCDF4.default_fillvals['f8']
        dzgem = numpy.repeat(nc_fill, FNC.shape[0])
        dzgem[iface]=dzgemi
        GridOperations.ugrid_add(
            dst,
            "avgdzb",
            dzgem,
            meshname,
            facedim,
            long_name="year-averaged bed level change without dredging",
            units="m",
        )
        dzmax = numpy.repeat(nc_fill, FNC.shape[0])
        dzmax[iface]=dzmaxi
        GridOperations.ugrid_add(
            dst,
            "maxdzb",
            dzmax,
            meshname,
            facedim,
            long_name=zmax_str,
            units="m",
        )
        dzmin = numpy.repeat(nc_fill, FNC.shape[0])
        dzmin[iface]=dzmini
        GridOperations.ugrid_add(
            dst,
            "mindzb",
            dzmin,
            meshname,
            facedim,
            long_name=zmin_str,
            units="m",
        )
        for i in range(len(dzbi)):
            j = (i + 1) % len(dzbi)
            dzb = numpy.repeat(nc_fill, FNC.shape[0])
            dzb[iface]=dzbi[j]
            GridOperations.ugrid_add(
                dst,
                "dzb_{}".format(i),
                dzb,
                meshname,
                facedim,
                long_name="bed level change at end of period {}".format(i+1),
                units="m",
            )
            if rsigma[i]<1 and isinstance(dzq[i], numpy.ndarray):
                dzq_full = numpy.repeat(nc_fill, FNC.shape[0])
                dzq_full[iface]=dzq[i]
                GridOperations.ugrid_add(
                    dst,
                    "dzq_{}".format(i),
                    dzq_full,
                    meshname,
                    facedim,
                    long_name="equilibrium bed level change aimed for during period {}".format(i+1),
                    units="m",
                )
        
        projmesh = outputdir + os.sep + 'projected_mesh.nc'
        GridOperations.copy_ugrid(one_fm_filename, meshname, projmesh)
        GridOperations.ugrid_add(
            projmesh,
            "avgdzb",
            dzgem,
            meshname,
            facedim,
            long_name="year-averaged bed level change without dredging",
            units="m",
        )
        
        if xykm is not None:
            print("replacing coordinates")
            sn = numpy.repeat(nc_fill, xn.shape[0])
            sn[inode]=sni
            nn = numpy.repeat(nc_fill, xn.shape[0])
            nn[inode]=nni
            
            # open destination file
            dst = netCDF4.Dataset(projmesh, "a")
            dst.variables[meshname + '_node_x'][:] = sn[:]
            dst.variables[meshname + '_node_y'][:] = nn[:]
            dst.close()       

        if plotops['plotting']:
            if FNCi.mask.shape == ():
                # all faces have the same number of nodes
                nnodes = numpy.ones(FNCi.data.shape[0], dtype=numpy.int64) * FNCi.data.shape[1]
            else:
                # varying number of nodes
                nnodes = FNCi.mask.shape[1] - FNCi.mask.sum(axis=1)
            fig, ax = dfastmi.plotting.plot_overview(
                (xmin, ymin, xmax, ymax),
                xykline,
                FNCi,
                nnodes,
                xni,
                yni,
                dzgemi,
                "x-coordinate [km]",
                "y-coordinate [km]",
                "change to year-averaged equilibrium",
                "erosion and sedimentation [m]",
                plotops['xyzoom'],
            )

            if plotops['saveplot']:
                figbase = plotops['figdir'] + os.sep + "overview"
                if plotops['saveplot_zoomed']:
                    dfastmi.plotting.zoom_xy_and_save(fig, ax, figbase, plotops['plot_ext'], plotops['xyzoom'], scale=1000)
                figfile = figbase + plotops['plot_ext']
                dfastmi.plotting.savefig(fig, figfile)

        if display:
            ApplicationSettingsHelper.log_text('compute_initial_year_dredging')

        if xykm is not None:
            sedarea, sedvol, sed_area_list, eroarea, erovol, ero_area_list, wght_estimate1i, wbini = comp_sedimentation_volume(xni, yni, sni, nni, FNCi, dzgemi, slength, nwidth,xykline,one_fm_filename, outputdir, plotops)

            if display:
                if sedvol.shape[1] > 0:
                    print("Estimated sedimentation volume per area using 3 methods")
                    print("                              Max:             Method 1:        Method 2:       ")
                    print("                                sum area*dzeqa      sum_L dzeqa   L*W*avg(dzeqa)")
                    for i in range(sedvol.shape[1]):
                        print("Area{:3d} ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(i+1, sedarea[i], sedvol[0,i], sedvol[1,i], sedvol[2,i]))
                    print("Max                         : {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(sedvol[0,:].max(), sedvol[1,:].max(), sedvol[2,:].max()))
                    print("Total   ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(sedarea.sum(), sedvol[0,:].sum(), sedvol[1,:].sum(), sedvol[2,:].sum()))

                if sedvol.shape[1] > 0 and erovol.shape[1] > 0:
                    print("")
                
                if erovol.shape[1] > 0:
                    print("Estimated erosion volume per area using 3 methods")
                    print("                              Max:             Method 1:        Method 2:       ")
                    print("                                sum area*dzeqa      sum_L dzeqa   L*W*avg(dzeqa)")
                    for i in range(erovol.shape[1]):
                        print("Area{:3d} ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(i+1, eroarea[i], erovol[0,i], erovol[1,i], erovol[2,i]))
                    print("Max                         : {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(erovol[0,:].max(), erovol[1,:].max(), erovol[2,:].max()))
                    print("Total   ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(eroarea.sum(), erovol[0,:].sum(), erovol[1,:].sum(), erovol[2,:].sum()))

            projmesh = outputdir + os.sep + 'sedimentation_weights.nc'
            GridOperations.copy_ugrid(one_fm_filename, meshname, projmesh)
            GridOperations.ugrid_add(
                projmesh,
                "interest_region",
                interest_region,
                meshname,
                facedim,
                long_name="Region on which the sedimentation analysis was performed",
               units="1",
            )
            sed_area = numpy.repeat(nc_fill, FNC.shape[0])
        
            for i in range(len(sed_area_list)):
                sed_area[iface[sed_area_list[i] == 1]] = i+1
            GridOperations.ugrid_add(
                projmesh,
                "sed_area",
                sed_area,
                meshname,
                facedim,
                long_name="Sedimentation area",
                units="1",
            )
            ero_area = numpy.repeat(nc_fill, FNC.shape[0])
        
            for i in range(len(ero_area_list)):
                ero_area[iface[ero_area_list[i] == 1]] = i+1
            GridOperations.ugrid_add(
                projmesh,
                "ero_area",
                ero_area,
                meshname,
                facedim,
                long_name="Erosion area",
                units="1",
            )
            wght_estimate1 = numpy.repeat(nc_fill, FNC.shape[0])
            wght_estimate1[iface] = wght_estimate1i
            GridOperations.ugrid_add(
                projmesh,
                "wght_estimate1",
                wght_estimate1,
                meshname,
                facedim,
                long_name="Weight per cell for determining initial year sedimentation volume estimate 1",
                units="1",
            )
            wbin = numpy.repeat(nc_fill, FNC.shape[0])
            wbin[iface] = wbini
            GridOperations.ugrid_add(
                projmesh,
                "wbin",
                wbin,
                meshname,
                facedim,
                long_name="Index of width bin",
                units="1",
            )
        
    return not missing_data


def get_values_waqua1(
    stage: int, q: float, ucrit: float, display: bool, report, reduced_output: bool
) -> numpy.ndarray:
    """
    Read data files exported from WAQUA for the specified stage, and return equilibrium bed level change.

    Arguments
    ---------
    stage : int
        Discharge level (1, 2 or 3).
    q : float
        Discharge value.
    ucrit : float
        Critical flow velocity.
    display : bool
        Flag indicating text output to stdout.
    report : TextIO
        Text stream for log file.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.

    Returns
    -------
    dzq : numpy.ndarray
        Array containing equilibrium bed level change.
    """
    dzq, firstm, firstn = get_values_waqua3(
        stage, q, ucrit, display, report, reduced_output
    )
    return dzq


def get_values_waqua3(
    stage: int, q: float, ucrit: float, display: bool, report, reduced_output: bool
) -> Tuple[numpy.ndarray, int, int]:
    """
    Read data files exported from WAQUA for the specified stage, and return equilibrium bed level change and minimum M and N.

    Arguments
    ---------
    stage : int
        Discharge level (1, 2 or 3).
    q : float
        Discharge value.
    ucrit : float
        Critical flow velocity.
    display : bool
        Flag indicating text output to stdout.
    report : TextIO
        Text stream for log file.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.

    Returns
    -------
    dzq : numpy.ndarray
        Array containing equilibrium bed level change.
    firstm : int
        Minimum M index read (0 if reduced_output is False).
    firstn : int
        Minimum N index read (0 if reduced_output is False).
    """
    cblok = str(stage)
    if display:
        ApplicationSettingsHelper.log_text("input_xyz", dict={"stage": stage, "q": q})
        ApplicationSettingsHelper.log_text("---")
        ApplicationSettingsHelper.log_text("")

    discriptions = ApplicationSettingsHelper.get_text("file_descriptions")
    quantities = ["velocity-zeta.001", "waterdepth-zeta.001", "velocity-zeta.002"]
    files = []
    for i in range(3):
        if display:
            ApplicationSettingsHelper.log_text("input_xyz_name", dict={"name": discriptions[i]})
        cifil = "xyz_" + quantities[i] + ".Q" + cblok + ".xyz"
        if display:
            print(cifil)
        if not os.path.isfile(cifil):
            ApplicationSettingsHelper.log_text("file_not_found", dict={"name": cifil})
            ApplicationSettingsHelper.log_text("file_not_found", dict={"name": cifil}, file=report)
            ApplicationSettingsHelper.log_text("end_program", file=report)
            return numpy.array([]), 0, 0
        else:
            if display:
                ApplicationSettingsHelper.log_text("input_xyz_found", dict={"name": cifil})
        files.extend([cifil])
        if display:
            ApplicationSettingsHelper.log_text("")

    if display:
        ApplicationSettingsHelper.log_text("input_xyz_read", dict={"stage": stage})
    u0temp = DataTextFileOperations.read_waqua_xyz(files[0], cols=(2, 3, 4))
    m = u0temp[:, 1].astype(int) - 1
    n = u0temp[:, 2].astype(int) - 1
    u0temp = u0temp[:, 0]
    h0temp = DataTextFileOperations.read_waqua_xyz(files[1])
    u1temp = DataTextFileOperations.read_waqua_xyz(files[2])

    if reduced_output:
        firstm = min(m)
        firstn = min(n)
    else:
        firstm = 0
        firstn = 0
    szm = max(m) + 1 - firstm
    szn = max(n) + 1 - firstn
    szk = szm * szn
    k = szn * m + n
    u0 = numpy.zeros([szk])
    h0 = numpy.zeros([szk])
    u1 = numpy.zeros([szk])

    u0[k] = u0temp
    h0[k] = h0temp
    u1[k] = u1temp

    sz = [szm, szn]
    u0 = u0.reshape(sz)
    h0 = h0.reshape(sz)
    u1 = u1.reshape(sz)

    dzq = dfastmi.kernel.core.dzq_from_du_and_h(u0, h0, u1, ucrit)
    if display:
        ApplicationSettingsHelper.log_text("---")
    return dzq, firstm, firstn


def get_values_fm(
    stage: int,
    q: float,
    ucrit: float,
    report: TextIO,
    filenames: Tuple[str, str],
    n_fields: int,
    dx: numpy.ndarray,
    dy: numpy.ndarray,
    iface: numpy.ndarray,
) -> numpy.ndarray:
    """
    Read D-Flow FM data files for the specified stage, and return dzq.

    Arguments
    ---------
    stage : int
        Discharge level (1, 2 or 3).
    q : float
        Discharge value.
    ucrit : float
        Critical flow velocity.
    report : TextIO
        Text stream for log file.
    filenames : Tuple[str, str]
        Names of the reference simulation file and file with the implemented measure.
    n_fields : int
        Number of fields to process (e.g. to cover a tidal period).
    dx : numpy.ndarray
        Array containing the x-component of the direction vector at each cell.
    dy : numpy.ndarray
        Array containing the y-component of the direction vector at each cell.
    iface : numpy.ndarray
        Array containing the subselection of cells.

    Returns
    -------
    dzq : numpy.ndarray
        Array containing equilibrium bed level change.
    """
    cblok = str(stage)

    # reference file
    if filenames[0] == "":
        ApplicationSettingsHelper.log_text("no_file_specified", dict={"q": q}, file=report)
        ApplicationSettingsHelper.log_text("end_program", file=report)
        return None
    elif not os.path.isfile(filenames[0]):
        ApplicationSettingsHelper.log_text("file_not_found", dict={"name": filenames[0]}, file=report)
        ApplicationSettingsHelper.log_text("end_program", file=report)
        return None
    else:
        pass

    # file with measure implemented
    if not os.path.isfile(filenames[1]):
        ApplicationSettingsHelper.log_text("file_not_found", dict={"name": filenames[1]}, file=report)
        ApplicationSettingsHelper.log_text("end_program", file=report)
        return None
    else:
        pass

    dzq = 0.
    tot = 0.
    ifld: Optional[int]
    if n_fields > 1:
        ustream_pos = numpy.zeros(dx.shape)
        ustream_neg = numpy.zeros(dx.shape)
        dzq_pos = numpy.zeros(dx.shape)
        dzq_neg = numpy.zeros(dx.shape)
        t_pos = numpy.zeros(dx.shape)
        t_neg = numpy.zeros(dx.shape)
        wght_pos = numpy.zeros(dx.shape)
        wght_neg = numpy.zeros(dx.shape)

    ref = GridOperations.read_fm_map(filenames[0], "sea_water_x_velocity", ifld=0)
    
    for ifld in range(n_fields):
        # if last time step is needed, pass None to allow for files without time specification
        if n_fields == 1:
            ifld = None

        # reference data
        u0 = GridOperations.read_fm_map(filenames[0], "sea_water_x_velocity", ifld=ifld)[iface]
        v0 = GridOperations.read_fm_map(filenames[0], "sea_water_y_velocity", ifld=ifld)[iface]
        umag0 = numpy.sqrt(u0 ** 2 + v0 ** 2)
        h0 = GridOperations.read_fm_map(filenames[0], "sea_floor_depth_below_sea_surface", ifld=ifld)[iface]

        # data with measure
        u1 = GridOperations.read_fm_map(filenames[1], "sea_water_x_velocity", ifld=ifld)[iface]
        v1 = GridOperations.read_fm_map(filenames[1], "sea_water_y_velocity", ifld=ifld)[iface]
        umag1 = numpy.sqrt(u1**2 + v1**2)

        dzq1 = dfastmi.kernel.core.dzq_from_du_and_h(umag0, h0, umag1, ucrit, default=0.0)

        if n_fields > 1:
            ustream = u0*dx + v0*dy
            
            # positive flow -> flow in downstream direction -> biggest flow in positive direction during peak ebb flow
            ipos = ustream > 0.
            t_pos[ipos] = t_pos[ipos] + 1
            
            ipos = ustream > ustream_pos
            ustream_pos[ipos] = ustream[ipos]
            dzq_pos[ipos] = dzq1[ipos]
            
            # negative flow -> flow in upstream direction -> biggest flow in negative direction during peak flood flow
            ineg = ustream < 0.
            t_neg[ineg] = t_neg[ineg] + 1
            
            ineg = ustream < ustream_neg
            ustream_neg[ineg] = ustream[ineg]
            dzq_neg[ineg] = dzq1[ineg]

    if n_fields > 1:
        dzq = (t_pos * dzq_pos + t_neg * dzq_neg ) / numpy.maximum(t_pos + t_neg, 1)
    else:
        dzq = dzq1

    return dzq


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
            return check_configuration_v1(rivers, config)
        else:
            return check_configuration_v2(rivers, config)
    except SystemExit as e:
        raise e
    except:
        return False


def check_configuration_v1(rivers: RiversObject, config: configparser.ConfigParser) -> bool:
    """
    Check if a version 1 analysis configuration is valid.

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
    branch = config["General"]["Branch"]
    if branch not in rivers.branches:
        return False
    
    reach = config["General"]["Reach"]
    ibranch = rivers.branches.index(branch)
    if reach not in rivers.allreaches[ibranch]:
        return False
    
    ireach = rivers.allreaches[ibranch].index(reach)
    nwidth = rivers.nwidth[ibranch][ireach]
    [_, apply_q, _, _, _, _, _, _] = get_levels_v1(rivers, ibranch, ireach, config, nwidth)
    
    mode_str = config["General"].get("Mode", DFLOWFM_MAP)
    for i in range(3):
        if not apply_q[i]:
            continue
        
        if not check_configuration_v1_cond(config, mode_str, i):
            return False
                
    return True


def check_configuration_v1_cond(config: configparser.ConfigParser, mode_str: str, i : int) -> bool:
    """
    Check validity of one condition of a version 1 analysis configuration.

    Arguments
    ---------
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis.
    mode_str : str
        String indicating the source of the model data: WAQUA or D-Flow FM.
    i : int
        Flow condition to be checked.

    Returns
    -------
    success : bool
        Boolean indicating whether the D-FAST MI analysis configuration is valid.
    """
    cond = "Q" + str(i+1)
    if mode_str == WAQUA_EXPORT:
        # condition block may not be specified since it doesn't contain any required keys
        if cond in config.sections() and "Discharge" in config[cond]:
            # if discharge is specified, it must be a number
            if not is_float_str(config[cond]["Discharge"]):
                return False
        
    elif mode_str == DFLOWFM_MAP:
        if not check_configuration_v1_cond_fm(config, cond):
            return False
                
    return True


def check_configuration_v1_cond_fm(config: configparser.ConfigParser, cond : str) -> bool:
    """
    Check validity of one condition of a version 1 analysis configuration using D-Flow FM results.

    Arguments
    ---------
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis.
    cond : str
        Condition block to be checked.

    Returns
    -------
    success : bool
        Boolean indicating whether the D-FAST MI analysis configuration is valid.
    """
    # condition block must be specified since it must contain the Reference and WithMeasure file names
    if cond not in config.sections():
        return False
    
    if "Discharge" in config[cond]:
        # if discharge is specified, it must be a number
        if not is_float_str(config[cond]["Discharge"]):
            return False
    
    if "Reference" not in config[cond]:
        return False
    
    if "WithMeasure" not in config[cond]:
        return False
                
    return True


def is_float_str(string:str) -> bool:
    """
    Check if a string represents a (floating point) number.

    Arguments
    ---------
    string : str
        The string to be checked.

    Returns
    -------
    success : bool
        Boolean indicating whether the the string can be converted to a number or not.
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def check_configuration_v2(rivers: RiversObject, config: configparser.ConfigParser) -> bool:
    """
    Check if a version 2 analysis configuration is valid.

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
    branch = config["General"]["Branch"]
    if branch not in rivers.branches:
        return False

    ibranch = rivers.branches.index(branch)
    reach = config["General"]["Reach"]
    if reach not in rivers.allreaches[ibranch]:
        return False

    ireach = rivers.allreaches[ibranch].index(reach)
    hydro_q = rivers.hydro_q[ibranch][ireach]
    n_cond = len(hydro_q)
    
    found = [False]*n_cond
    
    for i in range(n_cond):
        success, found[i] = check_configuration_v2_cond(config, hydro_q[i])
        if not success:
            return False
    
    if not all(found):
        return False
        
    return True


def check_configuration_v2_cond(config: configparser.ConfigParser, q: float) -> (bool, bool):
    """
    Check if a version 2 analysis configuration is valid.

    Arguments
    ---------
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis.

    Returns
    -------
    success : bool
        Boolean indicating whether the D-FAST MI analysis configuration is valid.
    found : bool
        Flag indicating whether the condition has been found.
    """
    qstr = str(q)
    found = False
    
    for cond in config.keys():
        if cond[0] != "C":
            # not a condition block
            continue
        
        if "Discharge" not in config[cond]:
            return False, found
        
        qstr_cond = config[cond]["Discharge"]
        if qstr != qstr_cond:
            continue
        
        found = True
        
        if "Reference" not in config[cond]:
            return False, found
    
        if "WithMeasure" not in config[cond]:
            return False, found        

    return True, found


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


def comp_sedimentation_volume(
    xni: numpy.ndarray,
    yni: numpy.ndarray,
    sni: numpy.ndarray,
    dni: numpy.ndarray,
    FNCi: numpy.ndarray,
    dzgemi: numpy.ndarray,
    slength: float,
    nwidth: float,
    xykline: numpy.ndarray,
    simfile: str,
    outputdir: str,
    plotops: Dict,
) -> float:
    """
    Compute the yearly dredging volume.

    Arguments
    ---------
    dzgem : numpy.ndarray
        Yearly mean bed level change [m].
    slength : float
        The expected yearly impacted sedimentation length [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].
    xykline : numpy.ndarray
        Array containing the x,y and chainage data of a line.
    simfile : str
        Name of simulation file.
    outputdir : str
        Name of output directory.

    Returns
    -------
    dvol : float
        Dredging volume [m3].
    """
    dzmin = 0.01
    nwbins = 10
    sbin_length = 10.0
    
    areai = xynode_2_area(xni, yni, FNCi)
    
    print("bin cells in across-stream direction")
    # determine the mean normal distance dfi per cell
    dfi = face_mean(dni, FNCi)
    # distribute the cells over nwbins bins over the channel width
    wbini, wthresh = width_bins(dfi, nwidth, nwbins)

    print("bin cells in along-stream direction")
    # determine the minimum and maximum along line distance of each cell
    min_sfi, max_sfi = min_max_s(sni, FNCi)
    # determine the weighted mapping of cells to chainage bins
    siface, afrac, sbin, sthresh = stream_bins(min_sfi, max_sfi, sbin_length)
    wbin = wbini[siface]

    print("determine chainage per bin")
    # determine chainage values of at the midpoints
    smid = (sthresh[1:] + sthresh[:-1])/2
    sline = distance_along_line(xykline[:,:2])
    kmid = distance_to_chainage(sline, xykline[:,2], smid)
    n_sbin = sbin.max()+1
    
    EFCi = facenode_to_edgeface(FNCi)
    wght_area_tot = numpy.zeros(dzgemi.shape)
    wbin_labels = ["between {w1} and {w2} m".format(w1 = wthresh[iw], w2 = wthresh[iw+1]) for iw in range(nwbins)]
    plot_n = 3

    print("-- detecting separate sedimentation areas")
    xyzfil = outputdir + os.sep + "sedimentation_volumes.xyz"
    area_str = "sedimentation area {}"
    total_str = "total sedimentation volume"
    sedarea, sedvol, sed_area_list, wght_area_tot = detect_and_plot_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, slength, plotops, xyzfil, area_str, total_str, True, plot_n)

    print("-- detecting separate erosion areas")
    xyzfil = ""
    area_str = "erosion area {}"
    total_str = "total erosion volume"
    eroarea, erovol, ero_area_list, wght_area_tot = detect_and_plot_areas(-dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, slength, plotops, xyzfil, area_str, total_str, False, plot_n)

    return sedarea, sedvol, sed_area_list, eroarea, erovol, ero_area_list, wght_area_tot, wbini


def detect_and_plot_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, slength, plotops, xyzfil, area_str, total_str, pos_up, plot_n):
    sbin_length = sthresh[1] - sthresh[0]

    area, volume, sub_area_list, wght_area_tot = detect_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wthresh, siface, afrac, sbin, sthresh, slength)

    binvol = comp_binned_volumes(numpy.maximum( dzgemi, 0.0), areai, wbin, siface, afrac, sbin, wthresh, sthresh)
    
    if xyzfil != "":
        # write a table of chainage and volume per width bin to file
        binvol2 = numpy.stack(binvol)
        with open(xyzfil, "w") as file:
            vol_str = " ".join('"{}"'.format(str) for str in wbin_labels)
            file.write('"chainage" ' + vol_str + "\n")
            for i in range(binvol2.shape[1]):
                vol_str = " ".join("{:8.2f}".format(j) for j in binvol2[:,i])
                file.write("{:8.2f} ".format(kmid[i]) + vol_str + "\n")

    if plotops['plotting']:
        fig, ax = dfastmi.plotting.plot_sedimentation(
            kmid,
            "chainage [km]",
            binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            total_str,
            wbin_labels,
            positive_up = pos_up,
        )

        if plotops['saveplot']:
            figbase = plotops['figdir'] + os.sep + total_str.replace(" ","_")
            if plotops['saveplot_zoomed']:
                dfastmi.plotting.zoom_x_and_save(fig, ax, figbase, plotops['plot_ext'], plotops['kmzoom'])
            figfile = figbase + plotops['plot_ext']
            dfastmi.plotting.savefig(fig, figfile)

        if plot_n > 0:
            # plot the figures with details for the N areas with largest volumes
            volume_mean = volume[1:,:].mean(axis=0)
            sorted_list = numpy.argsort(volume_mean)[::-1]
            if len(sorted_list) <= plot_n:
                vol_thresh = 0.0
            else:
                vol_thresh = volume_mean[sorted_list[plot_n]]
            plot_certain_areas(volume_mean > vol_thresh,  dzgemi, sub_area_list, areai, wbin, wbin_labels, siface, afrac, sbin, wthresh, sthresh, kmid, area_str, pos_up, plotops)
    
    return area, volume, sub_area_list, wght_area_tot


def detect_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wthresh, siface, afrac, sbin, sthresh, slength):
    sbin_length = sthresh[1] - sthresh[0]
    nwidth = wthresh[-1] - wthresh[0]
    sub_areai, n_sub_areas = detect_connected_regions(dzgemi > dzmin, EFCi)
    print("number of areas detected: ", n_sub_areas)

    area  = numpy.zeros(n_sub_areas)
    volume = numpy.zeros((3,n_sub_areas))
    sub_area_list = []
    
    for ia in range(n_sub_areas):
        dzgemi_filtered = dzgemi.copy()
        dzgemi_filtered[sub_areai != ia] = 0.0
        sub_area_list.append(sub_areai == ia)
        
        #ApplicationSettingsHelper.log_text("sed_vol",dict = {"ia": ia+1, "nr": 1})
        volume[1,ia], wght_area_ia = comp_sedimentation_volume1(dzgemi_filtered, dzmin, areai, wbin, siface, afrac, sbin, wthresh, sthresh, slength, sbin_length)
        wght_area_tot = wght_area_tot + wght_area_ia
        
        #ApplicationSettingsHelper.log_text("sed_vol",dict = {"ia": ia+1, "nr": 2})
        volume[2,ia], area[ia], volume[0,ia] = comp_sedimentation_volume2(numpy.maximum(dzgemi_filtered,0.0), dzmin, areai, slength, nwidth)
    
    sorted_list = numpy.argsort(area)[::-1]
    area = area[sorted_list]
    volume = volume[:,sorted_list]
    sub_area_list = [sub_area_list[ia] for ia in sorted_list]
    
    return area, volume, sub_area_list, wght_area_tot


def plot_certain_areas(condition, dzgemi, area_list, areai, wbin, wbin_labels, siface, afrac, sbin, wthresh, sthresh, kmid, area_str, pos_up, plotops):
    indices = numpy.where(condition)[0]
    sbin_length = sthresh[1] - sthresh[0]
    for ia in indices:
        dzgemi_filtered = dzgemi.copy()
        dzgemi_filtered[numpy.invert(area_list[ia])] = 0.0
        
        area_binvol = comp_binned_volumes(dzgemi_filtered, areai, wbin, siface, afrac, sbin, wthresh, sthresh)
        
        fig, ax = dfastmi.plotting.plot_sedimentation(
            kmid,
            "chainage [km]",
            area_binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            area_str.format(ia+1),
            wbin_labels,
            positive_up = pos_up,
        )
        
        if plotops['saveplot']:
            figbase = plotops['figdir'] + os.sep + area_str.replace(" ","_").format(ia+1) + "_volumes"
            if plotops['saveplot_zoomed']:
                dfastmi.plotting.zoom_x_and_save(fig, ax, figbase, plotops['plot_ext'], plotops['kmzoom'])
            figfile = figbase + plotops['plot_ext']
            dfastmi.plotting.savefig(fig, figfile)
        

def stream_bins(min_s, max_s, ds):
    """
    Construct the weighted mapping of cells to chainage bins.

    Arguments
    ---------
    min_s : numpy.ndarray
        Array of length M containing the minimum chainage of a cell [m].
    max_s : numpy.ndarray
        Array of length M containing the maximum chainage of a cell [m].
    ds : float
        Length of chainage bins [m].

    Returns
    -------
    siface : numpy.ndarray
        Array of length N containing the index of the source cell.
    afrac : numpy.ndarray
        Array of length N containing the fraction of the source cell associated with the target chainage bin.
    sbin : numpy.ndarray
        Array of length N containing the index of the target chainage bin.
    sthresh : numpy.ndarray
        Threshold values between the chainage bins [m].
    """
    # determine the minimum and maximum chainage in de data set.
    sbin_min = math.floor(min_s.min()/ds)
    sbin_max = math.ceil(max_s.max()/ds)
    # determin the chainage bins.
    sthresh = numpy.arange(sbin_min, sbin_max+2) * ds
    
    # determine for each cell in which bin it starts and ends
    min_sbin = numpy.floor(min_s/ds).astype(numpy.int64) - sbin_min
    max_sbin = numpy.floor(max_s/ds).astype(numpy.int64) - sbin_min
    
    # determine in how many chainage bins a cell is located
    nsbin = max_sbin - min_sbin + 1
    # determine the total number of chainage bin assignments
    nsbin_tot = nsbin.sum()
    
    # determine per cell a mapping from cell iface to the chainage bin sbin,
    # and determine which fraction of the chainage length associated with the
    # cell is mapped to this particular chainage bin
    siface = numpy.zeros(nsbin_tot, dtype=numpy.int64)
    afrac = numpy.zeros(nsbin_tot)
    sbin  = numpy.zeros(nsbin_tot, dtype=numpy.int64)
    nfaces = len(min_s)
    j = 0
    for i in range(nfaces):
        s0 = min_s[i]
        s1 = max_s[i]
        # skip cells that project onto one point (typically they are located outside the length of the line)
        if s0 == s1:
            continue
        wght = 1 / (s1 - s0)
        for ib in range(min_sbin[i], max_sbin[i]+1):
            siface[j] = i
            afrac[j] = wght * (min(sthresh[ib+1], s1) - max(sthresh[ib], s0))
            sbin[j] = ib
            j = j + 1

    # make sure that sthresh is not longer than necessary
    maxbin = sbin.max()
    if maxbin+2 < len(sthresh):
        sthresh = sthresh[:maxbin+2]
    
    return siface, afrac, sbin, sthresh


def min_max_s(s, FNC):
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int64) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)
    nfaces = FNC.shape[0]
    min_s = numpy.zeros((nfaces,))
    max_s = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = FNC[i]
        nni = nnodes[i]
        sni = s[fni][0:nni]
        min_s[i] = sni.min()
        max_s[i] = sni.max() # may need to check if max > min to avoid problems later ...

    return min_s, max_s


def width_bins(df: numpy.ndarray, nwidth: float, nbins: int) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Distribute the points over sample bins based on distance from centreline.

    Arguments
    ---------
    df : numpy.ndarray
        Array containing per point the signed distance from the centreline [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].
    nbins : int
        Number of bins over the normal width.

    Returns
    -------
    jbin : numpy.ndarray
        Bin index of each point (integers in the range 0 to nbins-1).
    wthresh : numpy.ndarray
        Signed distance threshold values between the bins [m].
        This array contains nbins+1 values.
    """
    jbin = numpy.zeros(df.shape, dtype=numpy.int64)
    binwidth = nwidth/nbins
    wthresh = -nwidth/2 + binwidth * numpy.arange(nbins+1)
    
    for i in range(1,nbins):
        idx = df > wthresh[i]
        jbin[idx] = i
        
    return jbin, wthresh
    

def comp_binned_volumes(
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
    
    n_wbin = len(wthresh)-1
    n_sbin = len(sthresh)-1
    sedbinvol : List[numpy.ndarray] = []
    
    # compute for every width bin the sedimentation volume
    for iw in range(n_wbin):
        lw = wbin == iw

        sbin_lw = sbin[lw]
        dvol_lw = dvol[siface[lw]]
        afrac_lw = afrac[lw]
    
        sedbinvol.append(numpy.bincount(sbin_lw, weights = dvol_lw * afrac_lw, minlength = n_sbin))
        
    return sedbinvol
    

def comp_sedimentation_volume1(
    dzgem: numpy.ndarray,
    dzmin: float,
    area: numpy.ndarray,
    wbin: numpy.ndarray,
    siface: numpy.ndarray,
    afrac: numpy.ndarray,
    sbin: numpy.ndarray,
    wthresh: numpy.ndarray,
    sthresh: numpy.ndarray,
    slength: float,
    sbin_length: float,
) -> float:
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
    sthresh : numpy.ndarray
        Array containing the along-stream coordinate boundaries between the streamwise bins [m].
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
    
    n_wbin = len(wthresh)-1
    n_sbin = len(sthresh)-1
    n_faces = len(dvol)
    tot_dredge_vol = 0
    wght_all_dredge = numpy.zeros(dvol.shape)
    
    # compute for every width bin the sedimentation volume
    for iw in range(n_wbin):
        lw = wbin == iw
        
        tot_dredge_vol_wbin, wght_all_dredge_bin = comp_sedimentation_volume1_one_width_bin(dvol[siface[lw]], sbin[lw], afrac[lw], siface[lw], sthresh, sbin_length, slength)
        
        #print("width bin {}, total volume {:.6f} m3".format(iw+1, tot_dredge_vol_wbin))
        tot_dredge_vol = tot_dredge_vol + tot_dredge_vol_wbin
        wght_all_dredge = wght_all_dredge + numpy.bincount(siface[lw], weights = wght_all_dredge_bin, minlength = n_faces)

    #print("-------> total volume {:.6f} m3".format(tot_dredge_vol))

    return tot_dredge_vol, wght_all_dredge


def comp_sedimentation_volume1_one_width_bin(
    dvol: numpy.ndarray,
    sbin: numpy.ndarray,
    afrac: numpy.ndarray,
    siface: numpy.ndarray,
    sthresh: numpy.ndarray,
    sbin_length: float,
    slength: float,
) -> float:
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
    n_sbin = len(sthresh)-1
    
    check_sed = dvol > 0.0
    dvol_sed = dvol[check_sed]
    sbin_sed = sbin[check_sed]
    siface_sed = siface[check_sed]
    afrac_sed = afrac[check_sed]
    
    tot_dredge_vol, wght_all_dredge_sed = comp_sedimentation_volume1_tot(dvol_sed, sbin_sed, afrac_sed, siface_sed, sthresh, sbin_length, slength)
    
    wght_all_dredge = numpy.zeros(dvol.shape)
    wght_all_dredge[check_sed] = wght_all_dredge_sed

    return tot_dredge_vol, wght_all_dredge

    
def comp_sedimentation_volume1_tot(
    sedvol: numpy.ndarray,
    sbin: numpy.ndarray,
    afrac: numpy.ndarray,
    siface: numpy.ndarray,
    sthresh: numpy.ndarray,
    sbin_length: float,
    slength: float,
) -> float:
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
        s0 = sthresh[sbin[index[0]]]
        slength1 = slength
        for i in range(len(index)):
            ii = index[i]
            ib = sbin[ii]
            if ib == ibprev: # same index, same weight
                pass

            else: # next index
                s0 = sthresh[ib]
                frac = max(0.0, min(slength1/sbin_length, 1.0))
                ibprev = ib
                slength1 = slength1 - sbin_length
        
            if frac != 0.0:
                wght[ii] = wght[ii] + frac * afrac[ii]
                dredge_vol = dredge_vol + frac * sedvol[ii] * afrac[ii]
                #print(siface[ii], frac, sedvol[ii], afrac[ii], frac * sedvol[ii] * afrac[ii],' -> ',dredge_vol)
        
    #print(dredge_vol, ' > ', wght)

    return dredge_vol, wght


def comp_sedimentation_volume2(
    dzgem: numpy.ndarray,
    dzmin: float,
    area: numpy.ndarray,
    slength: float,
    nwidth: float,
) -> float:
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
    iface = numpy.where(dzgem > dzmin)
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
    #print("dz_min = {:.6f} m, dz_max = {:.6f} m, dz_thresh = {:.6f} m".format(min(dzgem), max(dzgem), dzmin))
    print("dz_mean = {:.6f} m, width = {:.6f} m, length = {:.6f} m, volume = {:.6f} m3".format(dz_eq, nwidth, slength, dvol))
    return dvol, area_eq, dvol_eq


def comp_sedimentation_volume3(
    dz1: numpy.ndarray,
    dzmin: float,
    area: numpy.ndarray,
) -> float:
    """
    Compute the initial year sedimentation volume.
    Algorithm 3.

    Arguments
    ---------
    dz1 : numpy.ndarray
        Array of length M containing the bed level change after one year [m].
    dzmin : float
        Bed level changes (per cell) less than this threshold value are ignored [m].
    area : numpy.ndarray
        Array of length M containing the grid cell area [m2].

    Returns
    -------
    dvol : float
        Sedimentation volume [m3].
    """
    iface = numpy.where(dz1 > dzmin)
    dz1_clip = dz1[iface]
    area_clip = area[iface]
    dvol = (dz1_clip * area_clip).sum()

    #print("dz1_min = {:.6f} m, dz1_max = {:.6f} m, dz_thresh = {:.6f} m".format(min(dz1), max(dz1), dzmin))
    #print("total area = {:.0f} m2, total volume = {:.6f} m3".format(area_clip.sum(), dvol))
    
    return dvol


def get_xynode_connect(filename: str) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    xn = GridOperations.read_fm_map(filename, "x", location="node")
    yn = GridOperations.read_fm_map(filename, "y", location="node")
    FNC = GridOperations.read_fm_map(filename, "face_node_connectivity")
    if FNC.mask.shape == ():
        # all faces have the same number of nodes; empty mask
        FNC.mask = FNC<0
    else:
        # varying number of nodes
        FNC.mask = numpy.logical_or(FNC.mask,FNC<0)
    
    return xn, yn, FNC


def xynode_2_area(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    """
    Compute the surface area of all cells.

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the nodes [m].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the nodes [m].
    FNC : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.

    Returns
    -------
    area : numpy.ndarray
        Array of length M containing the grid cell area [m2].
    """
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int64) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)
    nfaces = FNC.shape[0]
    area = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = FNC[i]
        nni = nnodes[i]
        xni = xn[fni][0:nni]
        yni = yn[fni][0:nni]
        areai = 0.0
        for j in range(1,nni-1):
            areai += (xni[j] - xni[0]) * (yni[j+1] - yni[j]) - (xni[j+1] - xni[j]) * (yni[j] - yni[0])
        area[i] = abs(areai)/2
    
    return area
    

def face_all(bn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        bf = bn[FNC].all(axis=1)
    else:
        # varying number of nodes
        fnc = FNC.data
        fnc[FNC.mask] = 0
        bfn = numpy.ma.array(bn[fnc], mask=FNC.mask)
        bf = bfn.all(axis=1)
    
    return bf


def face_mean(vn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        vf = vn[FNC].mean(axis=1)
    else:
        # varying number of nodes
        fnc = FNC.data
        fnc[FNC.mask] = 0
        vfn = numpy.ma.array(vn[fnc], mask=FNC.mask)
        vf = vfn.all(axis=1)
    
    return vf


def old_face_mean(vn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    nnodes = count_nodes(FNC)
    nfaces = FNC.shape[0]
    vf = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = FNC[i]
        nni = nnodes[i]
        vni = vn[fni][0:nni]
        vf[i] = vni.mean()
    
    return vf
    

def filter_faces_by_node_condition(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ma.masked_array, condition: numpy.ndarray) -> [numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    Reduces the mesh to only those cells in which the condition is True. 

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the mesh nodes [m or deg east].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the mesh nodes [m or deg north].
    FNC : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
        Node indices are 0-based, hence the maximum node index is K-1.
    condition : numpy.ndarray
        Array of length K containing the boolean flag on the mesh nodes [-].

    Results
    -------
    rxn : numpy.ndarray
        Array of length K2 <= K containing the x-coordinates of the reduced mesh nodes [m or deg east].
    ryn : numpy.ndarray
        Array of length K2 <= K containing the y-coordinate of the reduced mesh nodes [m or deg north].
    rFNC : numpy.ma.masked_array
        Masked M2 x N2 array containing the indices of (max N2) corner nodes for each of the M2 <= M cells [-].
        Node indices are 0-based, hence the maximum node index is K2-1.
    iface : numpy.ndarray
        Array of length M2 containing the indices of the faces to keep [-]. 
    inode : numpy.ndarray
        Array of length K2 containing the indices of the nodes to keep [-]. 
    """
    fcondition = face_all(condition, FNC)
    rxn, ryn, rFNC, iface, inode = filter_faces_by_face_condition(xn, yn, FNC, fcondition)
    return rxn, ryn, rFNC, iface, inode


def filter_faces_by_face_condition(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ma.masked_array, condition: numpy.ndarray) -> [numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    Reduces the mesh to only those cells in which the condition is True. 

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the mesh nodes [m or deg east].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the mesh nodes [m or deg north].
    FNC : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
        Node indices are 0-based, hence the maximum node index is K-1.
    condition : numpy.ndarray
        Array of length M containing the boolean flag on the mesh cells [-].

    Results
    -------
    rxn : numpy.ndarray
        Array of length K2 <= K containing the x-coordinates of the reduced mesh nodes [m or deg east].
    ryn : numpy.ndarray
        Array of length K2 <= K containing the y-coordinate of the reduced mesh nodes [m or deg north].
    rFNC : numpy.ma.masked_array
        Masked M2 x N2 array containing the indices of (max N2) corner nodes for each of the M2 <= M cells [-].
        Node indices are 0-based, hence the maximum node index is K2-1.
    iface : numpy.ndarray
        Array of length M2 containing the indices of the faces to keep [-]. 
    inode : numpy.ndarray
        Array of length K2 containing the indices of the nodes to keep [-]. 
    """
    iface = numpy.where(condition)[0]
    FNCi = FNC[iface]
    inode = numpy.unique(FNCi.flatten())
    if len(inode) == 0:
        inode_max = 0
    else:
        inode_max = inode.max()

    FNCi.data[FNCi.mask] = 0
    renum = numpy.zeros(inode_max + 1, dtype=numpy.int64)
    renum[inode] = range(len(inode))
    rFNCi = numpy.ma.masked_array(renum[FNCi], mask=FNCi.mask)

    return xn[inode], yn[inode], rFNCi, iface, inode


def distance_to_chainage(sline: numpy.ndarray, kline: numpy.ndarray, spnt: numpy.ndarray) -> numpy.ndarray:
    """
    Interpolate a quantity 'chainage' along a line to a given set of points.

    Arguments
    ---------
    sline : numpy.ndarray
        Array of length M containing the distance along a line. Distance should be monotoneously increasing.
    kline : numpy.ndarray
        Array of length M containing the chainage along a line.
    spnt : numpy.ndarray
        Array of length N containing the location of points measured as distance along the same line.

    Results
    -------
    kpnt : numpy.ndarray
        Array of length N containing the location of points expressed as chainage.
    """
    M = len(sline)
    N = len(spnt)
    
    # make sure that spnt is sorted
    isort = numpy.argsort(spnt)
    unsort = numpy.argsort(isort)
    spnt_sorted = spnt[isort]

    kpnt = numpy.zeros(N)
    j = 0
    for i in range(N):
        s = spnt_sorted[i]
        while j < M:
            if sline[j] < s:
                j = j+1
            else:
                break
        if j == 0:
            # distance is less than the distance of the first point, snap to it
            kpnt[i] = kline[0]
        elif j == M:
            # distance is larger than the distance of all the points on the line, snap to the last point
            kpnt[i] = kline[-1]
        else:
            # somewhere in the middle, average the chainage values
            a = (s - sline[j-1]) / (sline[j] - sline[j-1])
            kpnt[i] = (1-a) * kline[j-1] + a * kline[j]

    return kpnt[unsort]


def distance_along_line(xyline: numpy.ndarray)-> numpy.ndarray:
    """
    Compute distance coordinate along the specified line

    Arguments
    ---------
    xyline : numpy.ndarray
        Array of size M x 2 containing the x,y data of a line.

    Results
    -------
    sline : numpy.ndarray
        Array of length M containing the distance along the line.
    """

    # compute distance coordinate along the line
    ds = numpy.sqrt(((xyline[1:] - xyline[:-1])**2).sum(axis=1))
    sline = numpy.cumsum(numpy.concatenate([numpy.zeros(1),ds]))

    return sline


def get_direction(xyline: numpy.ndarray, spnt: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Determine the orientation of a line at a given set of points.

    Arguments
    ---------
    xyline : numpy.ndarray
        Array containing the x,y data of a line.
    spnt : numpy.ndarray
        Array of length N containing the location of points measured as distance along the same line.

    Results
    -------
    dxpnt : numpy.ndarray
        Array of length N containing x-component of the unit direction vector at the given points.
    dypnt : numpy.ndarray
        Array of length N containing y-component of the unit direction vector at the given points.
    """
    sline = distance_along_line(xyline)
    M = len(sline)
    N = len(spnt)
    
    # make sure that spnt is sorted
    isort = numpy.argsort(spnt)
    unsort = numpy.argsort(isort)
    spnt_sorted = spnt[isort]

    dxpnt = numpy.zeros(N)
    dypnt = numpy.zeros(N)
    j = 0
    for i in range(N):
        s = spnt_sorted[i]
        while j < M:
            if sline[j] < s:
                j = j+1
            else:
                break
        if j == 0:
            # distance is less than the distance of the first point, use the direction of the first line segment
            dxy = xyline[1] - xyline[0]
        elif j == M:
            # distance is larger than the distance of all the points on the line, use the direction of the last line segment
            dxy = xyline[-1] - xyline[-2]
        else:
            # somewhere in the middle, get the direction of the line segment
            dxy = xyline[j] - xyline[j-1]
        ds = math.sqrt((dxy**2).sum())
        dxpnt[i] = dxy[0]/ds
        dypnt[i] = dxy[1]/ds

    return dxpnt[unsort], dypnt[unsort]




def proj_xy_line(xf: numpy.ndarray, yf: numpy.ndarray, xyline: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Project points onto a line.

    For a set of points (xf, yf) the closest point P a line (xyline) is determined.
    The quantities returned are the distance (sf) measured along the line (xyline)
    for the closest point P, the signed distance (df) between the original point (xf, yf)
    and the projected point P. If the original point is located alongsize the line
    (xyline) then the distance (df) is the normal distance ... if the original point is
    located before or beyond the line (xyline), it will include an oblique distance component.
    The sign of the distance (df) is positive for points to the right and negative for points
    to the left of the line.

    Arguments
    ---------
    xf : numpy.ndarray
        Array containing the x coordinates of a set of points.
    yf : numpy.ndarray
        Array containing the y coordinates of a set of points.
    xyline : numpy.ndarray
        Array containing the x,y data of a line.

    Results
    -------
    sf : numpy.ndarray
        Array containing the distance along the line.
    df : numpy.ndarray
        Array containing the distance from the line (- for left, + for right).
    """
    # combine xf and yf
    nf = len(xf)
    xyf = numpy.concatenate([xf.reshape((nf,1)),yf.reshape((nf,1))], axis=1)
    
    # pre-allocate the output arrays
    sf = numpy.zeros(nf)
    df = numpy.zeros(nf)

    # compute distance coordinate along the line
    sline = distance_along_line(xyline)
    
    # get an array with only the x,y coordinates of xyline
    last_node = xyline.shape[0] - 1
    
    # initialize sgn for the exceptional case of xyline containing just one node.
    sgn = 1

    # for each point xyp = xyf[i] ...
    for i,xyp in enumerate(xyf):
        # find the node on xyline closest to xyp
        imin = numpy.argmin(((xyp - xyline) ** 2).sum(axis=1))
        p0 = xyline[imin]

        # determine the distance between that node and xyp
        dist2 = ((xyp - p0) ** 2).sum()
    
        # distance value of that node
        s = sline[imin]
        
        if imin == 0:
            # we got the first node
            # check if xyp projects much before the first line segment.
            p1 = xyline[imin + 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p1[0] - p0[0]) * (xyp[1] - p0[1])
                  - (p1[1] - p0[1]) * (xyp[0] - p0[0]))
            # if the closest point is before the segment ...
            if alpha < 0:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                dist2end = dist2 - dist2link
                if dist2end > 100:
                    dist2 = 1e20
            
        else:
            # we didn't get the first node
            # project xyp onto the line segment before this node
            p1 = xyline[imin - 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p0[0] - p1[0]) * (xyp[1] - p0[1])
                  - (p0[1] - p1[1]) * (xyp[0] - p0[0]))
            # if there is a closest point not coinciding with the nodes ...
            if alpha > 0 and alpha < 1:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                # if it's actually closer than the node ...
                if dist2link < dist2:
                    # update the closest point information
                    dist2 = dist2link
                    s = sline[imin] + alpha * (sline[imin - 1] - sline[imin])

        if imin == last_node:
            # we got the last node
            # check if xyp projects much beyond the last line segment.
            p1 = xyline[imin - 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p0[0] - p1[0]) * (xyp[1] - p0[1])
                  - (p0[1] - p1[1]) * (xyp[0] - p0[0]))
            # if the closest point is before the segment ...
            if alpha < 0:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                dist2end = dist2 - dist2link
                if dist2end > 100:
                    dist2 = 1e20
            
        else:
            # we didn't get the last node
            # project rp onto the line segment after this node
            p1 = xyline[imin + 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p1[0] - p0[0]) * (xyp[1] - p0[1])
                  - (p1[1] - p0[1]) * (xyp[0] - p0[0]))
            # if there is a closest point not coinciding with the nodes ...
            if alpha > 0 and alpha < 1:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                # if it's actually closer than the previous value ...
                if dist2link < dist2:
                    # update the closest point information
                    dist2 = dist2link
                    s = sline[imin] + alpha * (
                        sline[imin + 1] - sline[imin]
                    )

        # store the distance values, loop ... and return
        sf[i] = s
        df[i] = math.copysign(math.sqrt(dist2), sgn)
        
    return sf,df


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


def count_nodes(FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int64) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)
    
    return nnodes


def facenode_to_edgeface(FNC: numpy.ndarray) -> numpy.ndarray:
    """
    Derive face 2 face connectivity from face 2 node connectivity.
    
    Arguments
    ---------
    FNC : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.
    
    Returns
    -------
    FFC : numpy.ma.masked_array
        Masked K x 2 array containing the indices of neighbouring cell pairs.
    """
    nfaces = FNC.shape[0]
    nnodes = count_nodes(FNC) # nedges equals to nnodes
    tot_nedges = nnodes.sum()
    
    edges = numpy.zeros((tot_nedges, 2), dtype=numpy.int64)
    ie = 0
    for i in range(nfaces):
        nni = nnodes[i]
        fni = FNC[i][0:nni]
        fni2 = numpy.roll(fni, 1)
        
        m_fni = numpy.reshape(fni,(-1,1))
        m_fni2 = numpy.reshape(fni2,(-1,1))
        edgesi = numpy.concatenate((m_fni,m_fni2), axis=1)
        
        edges[ie + numpy.arange(nni),:] = edgesi
        ie = ie + nni

    edges = numpy.sort(edges, axis=1)
    edges, iedge = numpy.unique(edges, axis=0, return_inverse=True)
    nedges = edges.shape[0]
    
    #FEC = FNC.copy()
    #ie = 0
    #for i in range(nfaces):
    #    nni = nnodes[i]
    #    FEC[i][0:nni] = iedge[ie + numpy.arange(nni)]
    #    ie = ie + nni
    
    EFC = -numpy.ones((nedges, 2), dtype=numpy.int64)
    ie = 0
    for i in range(nfaces):
        nni = nnodes[i]
        for j in range(nni):
            e = iedge[ie + j]
            if EFC[e,0]  < 0:
                EFC[e,0] = i
            else:
                EFC[e,1] = i
        ie = ie + nni

    EFC = EFC[EFC[:,1] > 0,:]
    return EFC


def detect_connected_regions(fcondition: numpy.ndarray, EFC: numpy.ndarray) -> Tuple[numpy.ndarray, int]:
    """
    Detect regions of faces for which the fcondition equals True.
    
    Arguments
    ---------
    fcondition : numpy.ndarray
        Boolean array of length M: one boolean per face.
    EFC : numpy.ndarray
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
    #print('Total number of cells ', fcondition.shape[0])
    
    ncells = fcondition.sum()
    partition[fcondition] = numpy.arange(ncells)
    #print('Total number of flagged cells ', ncells)
    
    efc = EFC[fcondition[EFC].all(axis=1),:]
    nlinks = efc.shape[0]
    #print('Total number of internal flow links ', nlinks)
    
    anychange = True
    while anychange:
        partEFC = partition[efc]
        anychange = False

        for j in range(nlinks):
            m = partition[efc[j]].min()
            if not (partition[efc[j]] == m).all():
                anychange = True
                partition[efc[j]] = m
    
    parts, ipart = numpy.unique(partition, return_inverse=True)
    ipart = ipart-1
    
    return ipart, len(parts)-1
