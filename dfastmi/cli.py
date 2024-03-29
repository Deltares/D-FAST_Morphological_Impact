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

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, TextIO
from dfastmi.batch.AnalyserAndReporterWaqua import analyse_and_report_waqua
from dfastmi.io.IReach import IReach
from dfastmi.io.Branch import Branch
from dfastmi.io.ReachLegacy import ReachLegacy
import dfastmi.kernel.core
import dfastmi.kernel.legacy
import dfastmi.batch.core

from dfastmi.kernel.typehints import QRuns
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper



def interactive_mode(src: TextIO, rivers: RiversObject, reduced_output: bool) -> None:
    """
    Run the analysis in interactive mode.

    The interactive mode works only for WAQUA simulations.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    rivers : RiversObject
        An object containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    """
    if reduced_output:
        ApplicationSettingsHelper.log_text("reduce_output")

    report = open(ApplicationSettingsHelper.get_filename("report.out"), "w")

    version = dfastmi.__version__
    have_files = interactive_mode_opening(src, version, report)

    all_done = False
    while not all_done:        
        branch = None
        reach = None
        while branch is None or reach is None:
            branch, reach = interactive_get_location(src, rivers)
        if isinstance(reach, ReachLegacy):
            celerity_hg = reach.proprate_high
            celerity_lw = reach.proprate_low
        nwidth = reach.normal_width

        (
            all_q,
            q_location,
            q_threshold,
            q_bankfull,
            q_fit,
            q_stagnant,
            Q,
            applyQ,
            tstag,
            T,
            rsigma,
        ) = interactive_get_discharges(
            src, branch, reach, have_files, celerity_hg, celerity_lw, nwidth
        )
        if have_files and not all_q:
            break

        tmi = []
        for i, value in enumerate(applyQ):
            if value:
                tmi.append(T[i])
            else:
                tmi.append(0.0)
        celerity = [celerity_lw, celerity_hg, celerity_hg]
        slength = dfastmi.kernel.core.estimate_sedimentation_length(tmi, celerity)

        
        if have_files:
            # determine critical flow velocity
            ucrit = reach.ucritical
            ucritMin = 0.01
            ApplicationSettingsHelper.log_text("", repeat=3)
            ApplicationSettingsHelper.log_text("default_ucrit", dict={"uc": ucrit, "reach": reach})
            tdum = interactive_get_bool(src, "confirm_or")
            if not tdum:
                ucrit = interactive_get_float(src, "query_ucrit")
                if ucrit < ucritMin:
                    ApplicationSettingsHelper.log_text("ucrit_too_low", dict={"uc": ucritMin})
                    ApplicationSettingsHelper.log_text(
                        "ucrit_too_low", dict={"uc": ucritMin}, file=report
                    )
                    ucrit = ucritMin

            ApplicationSettingsHelper.log_text("", repeat=19)
            display = True
            old_zmin_zmax = True
            outputdir = Path(".")
            
            success = analyse_and_report_waqua(
            display,
            report,
            reduced_output,
            tstag,
            Q,
            applyQ,
            T,
            rsigma,
            ucrit,
            old_zmin_zmax,
            outputdir,
            )
            
            if success:
                if slength > 1:
                    nlength = int(slength)
                else:
                    nlength = slength
                ApplicationSettingsHelper.log_text("")
                ApplicationSettingsHelper.log_text("length_estimate", dict={"nlength": nlength})
                ApplicationSettingsHelper.log_text(
                    "length_estimate", dict={"nlength": nlength}, file=report
                )
                tdum = interactive_get_bool(src, "confirm_to_close")
            all_done = True
        else:
            all_done = write_report_nodata(
                src,
                report,
                reach,
                q_location,
                q_threshold,
                q_bankfull,
                q_stagnant,
                tstag,
                q_fit,
                Q,
                T,
                nlength,
            )

    ApplicationSettingsHelper.log_text("end")
    ApplicationSettingsHelper.log_text("end", file=report)
    report.close()


def interactive_mode_opening(src: TextIO, version: str, report: TextIO) -> bool:
    """
    Interactive mode opening.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    version : str
        Version string.
    report : TextIO
        Text stream for log file.

    Returns
    -------
    have_files : bool
        Flag indicating whether the user specified that the simulation results
        are available or not.
    """
    ApplicationSettingsHelper.log_text("header", dict={"version": version})
    tdum = interactive_get_bool(src, "confirm")

    ApplicationSettingsHelper.log_text("limits")
    ApplicationSettingsHelper.log_text("qblocks")
    tdum = False
    while not tdum:
        ApplicationSettingsHelper.log_text("query_input-available")
        have_files = interactive_get_bool(src, "confirm_or")

        ApplicationSettingsHelper.log_text("---")
        if have_files:
            ApplicationSettingsHelper.log_text(
                "results_with_input_waqua",
                dict={
                    "avgdzb": ApplicationSettingsHelper.get_filename("avgdzb.out"),
                    "maxdzb": ApplicationSettingsHelper.get_filename("maxdzb.out"),
                    "mindzb": ApplicationSettingsHelper.get_filename("mindzb.out"),
                },
            )
        else:
            ApplicationSettingsHelper.log_text("results_without_input")
        ApplicationSettingsHelper.log_text("---")
        tdum = interactive_get_bool(src, "confirm_or_restart")

    ApplicationSettingsHelper.log_text("header", dict={"version": version}, file=report)
    ApplicationSettingsHelper.log_text("limits", file=report)
    ApplicationSettingsHelper.log_text("===", file=report)
    if have_files:
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
        ApplicationSettingsHelper.log_text("results_without_input", file=report)
    return have_files


def interactive_get_location(
    src: TextIO, rivers: RiversObject,
) -> Tuple[Optional[Branch], Optional[IReach]]:
    """
    Ask the user interactively for the branch and reach.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    rivers : RiversObject
        An object containing the river data.

    Returns
    -------
    ibranch : Optional[int]
        Number of selected branch (None if user cancels).
    ireach : Optional[int]
        Number of selected reach (None if user cancels).
    """
    branches = [branch.name for branch in rivers.branches]
    

    accept = False
    ibranch = interactive_get_item(src, "branch", branches)
    if not ibranch is None:
        ireach = interactive_get_item(src, "reach", [reach.name for reach in rivers.branches[ibranch].reaches])
        ApplicationSettingsHelper.log_text("---")
        if not ireach is None:            
            branch = rivers.branches[ibranch]
            reach = branch.reaches[ireach]
            ApplicationSettingsHelper.log_text("reach", dict={"reach": reach.name})
            ApplicationSettingsHelper.log_text("---")
            accept = interactive_get_bool(src, "confirm_location")
    if accept:
        return branch, reach
    else:
        return None, None


def interactive_get_discharges(
    src: TextIO,
    branch: Branch,
    reach: ReachLegacy,
    have_files: bool,
    celerity_hg: float,
    celerity_lw: float,
    nwidth: float,
) -> Tuple[
    bool,
    str,
    Optional[float],
    float,
    Tuple[float, float],
    float,
    QRuns,
    Tuple[bool, bool, bool],
    float,
    Tuple[float, float, float],
    Tuple[float, float, float],
]:
    """
    Get the simulation discharges in interactive mode.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    rivers : RiversObject
        An object containing the river data.
    ibranch : int
        Number of selected branch.
    ireach : int
        Number of selected reach.
    have_files : bool
        flag to indicate whether user specified that simulation results are
        available.
    celerity_hg : float
        Bed celerity during transitional and flood periods (from rivers configuration file).
    celerity_lw : float
        Bed celerity during low flow period (from rivers configuration file).
    nwidth : float
        Normal river width (from rivers configuration file).

    Results
    -------
    all_q : bool
    q_location : str
        Name of the location at which the discharge is
    q_threshold : Optional[float]
        River discharge at which the measure becomes active.
    q_bankfull : float
        River discharge at which the measure is bankfull.
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    q_stagnant : float
        A discharge below which the river flow is negligible.
    Q : QRuns
        Tuple of (at most) three characteristic discharges.
    applyQ : Tuple[bool, bool, bool]
        A list of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.
    t_stagnant : float
        Fraction of year during which flow velocity is considered negligible.
    T : Tuple[float, float, float]
        A tuple of 3 values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q.
    rsigma : Tuple[float, float, float]
        A tuple of 3 values each representing the relaxation factor for the period given by the corresponding entry in Q.
    """
    stages = ApplicationSettingsHelper.get_text("stage_descriptions")

    q_location = branch.qlocation
    q_stagnant = reach.qstagnant
    q_min = reach.qmin
    q_fit = reach.qfit
    q_levels = reach.qlevels
    dq = reach.dq

    ApplicationSettingsHelper.log_text("intro-measure")
    if q_stagnant > q_fit[0]:
        ApplicationSettingsHelper.log_text("query_flowing_when_barriers_open")
    else:
        ApplicationSettingsHelper.log_text(
            "query_flowing_above_qmin", dict={"border": q_location, "qmin": int(q_min)},
        )
    tdrem = interactive_get_bool(src, "confirm_or")
    if tdrem:
        q_threshold = None
    else:
        q_threshold = interactive_get_float(
            src, "query_qthreshold", dict={"border": q_location}
        )

    if q_threshold is None or q_threshold < q_levels[1]:
        ApplicationSettingsHelper.log_text("query_flowing", dict={"qborder": int(q_levels[1])})
        tdum = interactive_get_bool(src, "confirm_or")
        if tdum:
            q_bankfull = q_levels[1]
        else:
            q_bankfull_opt = interactive_get_float(src, "query_qbankfull")
            if not q_bankfull_opt is None:
                q_bankfull = q_bankfull_opt
            else:
                q_bankfull = 0
    else:
        q_bankfull = 0

    Q, applyQ = dfastmi.kernel.legacy.char_discharges(q_levels, dq, q_threshold, q_bankfull)

    tstag, T, rsigma = dfastmi.kernel.legacy.char_times(
        q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
    )

    QList = list(Q)
    all_q = True
    if have_files:
        lastStage = None
        if applyQ[0] and not QList[0] is None:
            QList[0] = interactive_check_discharge(src, 1, QList[0])
            if QList[0] is None:
                all_q = False
        if not all_q:
            pass
        elif applyQ[1] and not QList[1] is None and not QList[0] is None:
            QList[1] = interactive_check_discharge(
                src, 2, QList[1], stages[0], QList[0]
            )
            if QList[1] is None:
                all_q = False
            elif not QList[2] is None:
                QList[2] = interactive_check_discharge(
                    src, 3, QList[2], stages[1], QList[1]
                )
                if QList[2] is None:
                    all_q = False
        elif applyQ[2] and not QList[2] is None and not QList[0] is None:
            QList[2] = interactive_check_discharge(
                src, 3, QList[2], stages[0], QList[0]
            )
            if QList[2] is None:
                all_q = False
    Q = (QList[0], QList[1], QList[2])

    return (
        all_q,
        q_location,
        q_threshold,
        q_bankfull,
        q_fit,
        q_stagnant,
        Q,
        applyQ,
        tstag,
        T,
        rsigma,
    )


def write_report_nodata(
    src: TextIO,
    report: TextIO,
    reach: str,
    q_location: str,
    q_threshold: Optional[float],
    q_bankfull: float,
    q_stagnant: float,
    tstag: float,
    q_fit: Tuple[float, float],
    Q: QRuns,
    T: Tuple[float, float, float],
    nlength: float,
) -> bool:
    """
    Write the screen log and report file if simulation input is not yet available.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    report : TextIO
        Text stream for log file.
    reach : str
        Name of the reach.
    q_location : str
        Name of the location at which the discharge is
    q_threshold : Optional[float]
        River discharge at which the measure becomes active.
    q_bankfull : float
        River discharge at which the measure is bankfull.
    q_stagnant : float
        Discharge below which the river flow is negligible.
    tstag : float
        Fraction of year that the river is stagnant.
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    Q : QRuns
        Tuple of (at most) three characteristic discharges.
    T : Tuple[float, float, float]
        Fraction of year represented by each characteristic discharge.
    nlength : float
        The expected yearly impacted length.

    Returns
    -------
    all_done : bool
        Flag indicating whether the program should be closed.
    """
    ApplicationSettingsHelper.log_text("---")
    number_of_discharges = dfastmi.batch.core.count_discharges(Q)
    if number_of_discharges == 1:
        ApplicationSettingsHelper.log_text("need_single_input", dict={"reach": reach})
    else:
        ApplicationSettingsHelper.log_text("need_multiple_input", dict={"reach": reach, "numq": number_of_discharges})
    if not Q[0] is None:
        ApplicationSettingsHelper.log_text("lowwater", dict={"border": q_location, "q": Q[0]})
    if not Q[1] is None:
        ApplicationSettingsHelper.log_text("transition", dict={"border": q_location, "q": Q[1]})
    if not Q[2] is None:
        ApplicationSettingsHelper.log_text("highwater", dict={"border": q_location, "q": Q[2]})
    ApplicationSettingsHelper.log_text("length_estimate", dict={"nlength": nlength})
    ApplicationSettingsHelper.log_text("---")
    ApplicationSettingsHelper.log_text("canclose")
    all_done = interactive_get_bool(src, "confirm_or_repeat")
    if all_done:
        dfastmi.batch.core.write_report(
            report,
            reach,
            q_location,
            q_threshold,
            q_bankfull,
            q_stagnant,
            tstag,
            q_fit,
            Q,
            T,
            nlength,
        )
    else:
        ApplicationSettingsHelper.log_text("", repeat=10)
        ApplicationSettingsHelper.log_text("===", file=report)
        ApplicationSettingsHelper.log_text("repeat_input", file=report)
    return all_done


def interactive_check_discharge(
    src: TextIO, i: int, Q: float, pname: str = "dummy", Qp: float = 0
) -> Optional[float]:
    """
    Interactively request discharge for which simulation results are available.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    i : int
        Discharge level (1, 2 or 3).
    Q : float
        Proposed discharge.
    pname : str
        Name of previous discharge level.
    Qp : float
        Previous discharge.

    Returns
    -------
    Q : float
        Final discharge.
    """
    Q1: Optional[float]
    ApplicationSettingsHelper.log_text("")
    ApplicationSettingsHelper.log_text("input_avail", dict={"i": i, "q": Q})
    tdum = interactive_get_bool(src, "confirm_or")
    Q1 = Q
    if not tdum:
        while True:
            Q1 = interactive_get_float(src, "query_qavail", dict={"i": i})
            if Q1 is None:
                break
            elif Q1 < Qp:
                ApplicationSettingsHelper.log_text("")
                if i == 1:
                    ApplicationSettingsHelper.log_text("qavail_too_small_1")
                else:
                    ApplicationSettingsHelper.log_text(
                        "qavail_too_small_2",
                        dict={"p": i - 1, "pname": pname, "qp": Qp, "i": i},
                    )
            else:
                break
    return Q1


def interactive_get_bool(src: TextIO, key: str, dict: Dict[str, Any] = {}) -> bool:
    """
    Interactively get a boolean from the user.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    key : str
        The key for the text to show to the user.
    dict : Dict[str, Any]
        A dictionary used for placeholder expansions (default empty).

    Returns
    -------
    val : bool
        The boolean entered by the user (True if the user entered "j" or "y", False otherwise).
    """
    ApplicationSettingsHelper.log_text(key, dict=dict)
    str = src.readline().lower()
    bool = str == "j\n" or str == "y\n"
    if bool:
        ApplicationSettingsHelper.log_text("yes")
    else:
        ApplicationSettingsHelper.log_text("no")
    return bool


def interactive_get_int(
    src: TextIO, key: str, dict: Dict[str, Any] = {}
) -> Optional[int]:
    """
    Interactively get an integer from the user.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    key : str
        The key for the text to show to the user.
    dict : Dict[str, Any]
        A dictionary used for placeholder expansions (default empty).

    Returns
    -------
    val : Optional[int]
        The integer entered by the user (None if the string entered by the user can't be converted to an integer).
    """
    val: Optional[int]

    ApplicationSettingsHelper.log_text(key, dict=dict)
    str = src.readline()
    print(str)
    try:
        val = int(str)
    except:
        val = None
    return val


def interactive_get_float(
    src: TextIO, key: str, dict: Dict[str, Any] = {}
) -> Optional[float]:
    """
    Interactively get a floating point value from the user.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    key : str
        The key for the text to show to the user.
    dict : Dict[str, Any]
        A dictionary used for placeholder expansions (default empty).

    Returns
    -------
    val : Optional[float]
        The floating point value entered by the user (None if the string entered by the user can't be converted to a floating point value).
    """
    val: Optional[float]

    ApplicationSettingsHelper.log_text(key, dict=dict)
    str = src.readline()
    print(str)
    try:
        val = float(str)
    except:
        val = None
    return val


def interactive_get_item(src: TextIO, type: str, list: List[str]) -> Optional[int]:
    """
    Interactively get an item from the user.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    type : str
        The type of the items to select from.
    list : List[str]
        A list of items.

    Returns
    -------
    val : Optional[int]
        The integer index of the item selected by the user (None if interactive_get_int returns None).
    """
    i = 0
    nitems = len(list)
    while i < 1 or i > nitems:
        ApplicationSettingsHelper.log_text("query_" + type + "_header")
        for i in range(nitems):
            ApplicationSettingsHelper.log_text("query_list", dict={"item": list[i], "index": i + 1})
        i_opt = interactive_get_int(src, "query_" + type)
        if i_opt is None:
            return None
        else:
            i = i_opt
    return i - 1
