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
from typing import Any, Dict, List, Optional, TextIO, Tuple

import dfastmi.batch.core
import dfastmi.kernel.core
import dfastmi.kernel.legacy
from dfastmi.batch.AnalyserAndReporterWaqua import analyse_and_report_waqua
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.IReach import IReach
from dfastmi.io.ReachLegacy import ReachLegacy
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import QRuns, BoolVector


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
    have_files = _interactive_mode_opening(src, version, report)

    all_done = False
    while not all_done:
        all_done = _run_interactive_mode_once(
            src, rivers, reduced_output, report, have_files
        )

    ApplicationSettingsHelper.log_text("end")
    ApplicationSettingsHelper.log_text("end", file=report)
    report.close()


def _run_interactive_mode_once(
    src: TextIO,
    rivers: RiversObject,
    reduced_output: bool,
    report: TextIO,
    have_files: bool,
) -> bool:
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
    report : TextIO
        Text stream for log file.
    have_files : bool
        Flag indicating whether the user specified that the simulation results
        are available or not.

    Returns
    -------
    all_done : bool
        Flag indicating whether the interactive session can be ended.
    """
    branch = None
    reach = None
    while branch is None or reach is None:
        branch, reach = _interactive_get_location(src, rivers)
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
        discharges,
        apply_q,
        tstag,
        fraction_of_year,
        rsigma,
    ) = _interactive_get_discharges(
        src, branch, reach, have_files, celerity_hg, celerity_lw, nwidth
    )
    if have_files and not all_q:
        return True

    tmi = []
    for i, value in enumerate(apply_q):
        if value:
            tmi.append(fraction_of_year[i])
        else:
            tmi.append(0.0)
    celerity = [celerity_lw, celerity_hg, celerity_hg]
    slength = dfastmi.kernel.core.estimate_sedimentation_length(tmi, celerity)
    if slength > 1:
        nlength = int(slength)
    else:
        nlength = slength

    if have_files:
        _write_report_data(
            src,
            report,
            reach,
            reduced_output,
            tstag,
            discharges,
            apply_q,
            fraction_of_year,
            rsigma,
            nlength,
        )
        all_done = True
    else:
        all_done = _write_report_nodata(
            src,
            report,
            reach,
            q_location,
            q_threshold,
            q_bankfull,
            q_stagnant,
            tstag,
            q_fit,
            discharges,
            apply_q,
            fraction_of_year,
            nlength,
        )

    return all_done


def _interactive_mode_opening(src: TextIO, version: str, report: TextIO) -> bool:
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
    ApplicationSettingsHelper.log_text("header_legacy", dict={"version": version})
    _interactive_get_bool(src, "confirm")

    ApplicationSettingsHelper.log_text("limits")
    ApplicationSettingsHelper.log_text("qblocks")
    tdum = False
    while not tdum:
        ApplicationSettingsHelper.log_text("query_input-available")
        have_files = _interactive_get_bool(src, "confirm_or")

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
        tdum = _interactive_get_bool(src, "confirm_or_restart")

    ApplicationSettingsHelper.log_text(
        "header_legacy", dict={"version": version}, file=report
    )
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


def _interactive_get_location(
    src: TextIO,
    rivers: RiversObject,
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
    branch : Optional[Branch]
        Selected branch object (None if user cancels).
    reach : Optional[IReach]
        Selected reach object (None if user cancels).
    """
    branches = [branch.name for branch in rivers.branches]

    accept = False
    ibranch = _interactive_get_item(src, "branch", branches)
    if not ibranch is None:
        ireach = _interactive_get_item(
            src, "reach", [reach.name for reach in rivers.branches[ibranch].reaches]
        )
        ApplicationSettingsHelper.log_text("---")
        if not ireach is None:
            branch = rivers.branches[ibranch]
            reach = branch.reaches[ireach]
            ApplicationSettingsHelper.log_text("reach", dict={"reach": reach.name})
            ApplicationSettingsHelper.log_text("---")
            accept = _interactive_get_bool(src, "confirm_location")
    if accept:
        return branch, reach
    else:
        return None, None


def _interactive_get_discharges(
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
    BoolVector,
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
    branch : Branch
        Selected branch.
    ireach : ReachLegacy
        Selected reach.
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
        River discharge at which the intervention becomes active.
    q_bankfull : float
        River discharge at which the intervention is bankfull.
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    q_stagnant : float
        A discharge below which the river flow is negligible.
    discharges : QRuns
        Tuple of (at most) three characteristic discharges.
    apply_q : BoolVector
        A list of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.
    t_stagnant : float
        Fraction of year during which flow velocity is considered negligible.
    fraction_of_year : Tuple[float, float, float]
        A tuple of 3 values each representing the fraction of the year during which the discharge is given by the corresponding entry in discharges.
    rsigma : Tuple[float, float, float]
        A tuple of 3 values each representing the relaxation factor for the period given by the corresponding entry in discharges.
    """
    q_location = branch.qlocation
    q_stagnant = reach.qstagnant
    q_min = reach.qmin
    q_fit = reach.qfit
    q_levels = reach.qlevels
    dq = reach.dq

    ApplicationSettingsHelper.log_text("intro-intervention")
    if q_stagnant > q_fit[0]:
        ApplicationSettingsHelper.log_text("query_flowing_when_barriers_open")
    else:
        ApplicationSettingsHelper.log_text(
            "query_flowing_above_qmin",
            dict={"border": q_location, "qmin": int(q_min)},
        )
    tdrem = _interactive_get_bool(src, "confirm_or")
    if tdrem:
        q_threshold = None
    else:
        q_threshold = _interactive_get_float(
            src, "query_qthreshold", dict={"border": q_location}
        )

    if q_threshold is None or q_threshold < q_levels[1]:
        ApplicationSettingsHelper.log_text(
            "query_flowing", dict={"qborder": int(q_levels[1])}
        )
        tdum = _interactive_get_bool(src, "confirm_or")
        if tdum:
            q_bankfull = q_levels[1]
        else:
            q_bankfull_opt = _interactive_get_float(src, "query_qbankfull")
            if not q_bankfull_opt is None:
                q_bankfull = q_bankfull_opt
            else:
                q_bankfull = 0
    else:
        q_bankfull = 0

    discharges, apply_q = dfastmi.kernel.legacy.char_discharges(
        q_levels, dq, q_threshold, q_bankfull
    )

    tstag, fraction_of_year, rsigma = dfastmi.kernel.legacy.char_times(
        q_fit, q_stagnant, discharges, celerity_hg, celerity_lw, nwidth
    )

    all_q, discharge_list = _interactive_get_and_check_discharges(
        src, discharges, have_files, apply_q
    )
    discharges = (discharge_list[0], discharge_list[1], discharge_list[2])

    return (
        all_q,
        q_location,
        q_threshold,
        q_bankfull,
        q_fit,
        q_stagnant,
        discharges,
        apply_q,
        tstag,
        fraction_of_year,
        rsigma,
    )


def _interactive_get_and_check_discharges(
    src: TextIO,
    discharges: QRuns,
    have_files: bool,
    apply_q: BoolVector,
) -> Tuple[
    bool,
    List[Optional[float]],
]:
    """
    Get the simulation discharges in interactive mode.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    discharges : List[Optional[float]]
        Tuple of (at most) three characteristic discharges.
    have_files : bool
        flag to indicate whether user specified that simulation results are
        available.
    apply_q : BoolVector
        A list of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.

    Results
    -------
    all_q : bool
        Flag indicating whether data for all discharges is found.
    new_discharges : List[Optional[float]]
        List of (at most) three discharges. Same as input discharges, unless updated by the user.
    """
    if not have_files:
        return True, discharges

    stages = ApplicationSettingsHelper.get_text("stage_descriptions")
    new_discharges = list(discharges)

    all_q = True

    if apply_q[0] and discharges[0] is not None:
        new_discharges[0] = _interactive_get_and_check_one_discharge(
            src, 1, discharges[0]
        )
        all_q = new_discharges[0] is not None

    i_prev = 0
    if all_q and apply_q[1] and discharges[1] is not None:
        i_prev = 1
        new_discharges[1] = _interactive_get_and_check_one_discharge(
            src, 2, discharges[1], stages[0], new_discharges[0]
        )
        all_q = new_discharges[1] is not None

    if all_q and apply_q[2] and discharges[2] is not None:
        new_discharges[2] = _interactive_get_and_check_one_discharge(
            src, 3, discharges[2], stages[i_prev], new_discharges[i_prev]
        )
        all_q = new_discharges[2] is not None

    return all_q, new_discharges


def _write_report_data(
    src: TextIO,
    report: TextIO,
    reach: IReach,
    reduced_output: bool,
    tstag: float,
    discharges: QRuns,
    apply_q: BoolVector,
    fraction_of_year: Tuple[float, float, float],
    rsigma: Tuple[float, float, float],
    nlength: float,
) -> None:
    """
    Write the screen log and report file if simulation input is available.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    report : TextIO
        Text stream for log file.
    reach : IReach
        Selected reach.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    tstag : float
        Fraction of year that the river is stagnant.
    """

    # determine critical flow velocity
    ucrit = reach.ucritical
    ucrit_min = 0.01
    ApplicationSettingsHelper.log_text("", repeat=3)
    ApplicationSettingsHelper.log_text(
        "default_ucrit", dict={"uc": ucrit, "reach": reach}
    )
    tdum = _interactive_get_bool(src, "confirm_or")
    if not tdum:
        ucrit = _interactive_get_float(src, "query_ucrit")
        if ucrit < ucrit_min:
            ApplicationSettingsHelper.log_text("ucrit_too_low", dict={"uc": ucrit_min})
            ApplicationSettingsHelper.log_text(
                "ucrit_too_low", dict={"uc": ucrit_min}, file=report
            )
            ucrit = ucrit_min

    ApplicationSettingsHelper.log_text("", repeat=19)
    display = True
    old_zmin_zmax = True
    outputdir = Path.cwd()

    success = analyse_and_report_waqua(
        display,
        report,
        reduced_output,
        tstag,
        discharges,
        apply_q,
        fraction_of_year,
        rsigma,
        ucrit,
        old_zmin_zmax,
        outputdir,
    )

    if success:
        ApplicationSettingsHelper.log_text("")
        ApplicationSettingsHelper.log_text("length_estimate", dict={"nlength": nlength})
        ApplicationSettingsHelper.log_text(
            "length_estimate", dict={"nlength": nlength}, file=report
        )
        _interactive_get_bool(src, "confirm_to_close")


def _write_report_nodata(
    src: TextIO,
    report: TextIO,
    reach: IReach,
    q_location: str,
    q_threshold: Optional[float],
    q_bankfull: float,
    q_stagnant: float,
    tstag: float,
    q_fit: Tuple[float, float],
    discharges: QRuns,
    apply_q: BoolVector,
    fraction_of_year: Tuple[float, float, float],
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
    reach : IReach
        Selected reach.
    q_location : str
        Name of the location at which the discharge is
    q_threshold : Optional[float]
        River discharge at which the intervention becomes active.
    q_bankfull : float
        River discharge at which the intervention is bankfull.
    q_stagnant : float
        Discharge below which the river flow is negligible.
    tstag : float
        Fraction of year that the river is stagnant.
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    discharges : QRuns
        Tuple of (at most) three characteristic discharges.
    apply_q : BoolVector
        A list of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.
    fraction_of_year : Tuple[float, float, float]
        Fraction of year represented by each characteristic discharge.
    nlength : float
        The expected yearly impacted length.

    Returns
    -------
    all_done : bool
        Flag indicating whether the program should be closed.
    """
    ApplicationSettingsHelper.log_text("---")
    number_of_discharges = dfastmi.batch.core.count_discharges(apply_q)
    if number_of_discharges == 1:
        ApplicationSettingsHelper.log_text("need_single_input", dict={"reach": reach})
    else:
        ApplicationSettingsHelper.log_text(
            "need_multiple_input", dict={"reach": reach, "numq": number_of_discharges}
        )
    if apply_q[0]:
        ApplicationSettingsHelper.log_text(
            "lowwater", dict={"border": q_location, "q": discharges[0]}
        )
    if apply_q[1]:
        ApplicationSettingsHelper.log_text(
            "transition", dict={"border": q_location, "q": discharges[1]}
        )
    if apply_q[2]:
        ApplicationSettingsHelper.log_text(
            "highwater", dict={"border": q_location, "q": discharges[2]}
        )
    ApplicationSettingsHelper.log_text("length_estimate", dict={"nlength": nlength})
    ApplicationSettingsHelper.log_text("---")
    ApplicationSettingsHelper.log_text("canclose")
    all_done = _interactive_get_bool(src, "confirm_or_repeat")
    if all_done:
        dfastmi.batch.core.write_report(
            report,
            reach.name,
            q_location,
            q_threshold,
            q_bankfull,
            q_stagnant,
            tstag,
            q_fit,
            discharges,
            apply_q,
            fraction_of_year,
            nlength,
        )
    else:
        ApplicationSettingsHelper.log_text("", repeat=10)
        ApplicationSettingsHelper.log_text("===", file=report)
        ApplicationSettingsHelper.log_text("repeat_input", file=report)
    return all_done


def _interactive_get_and_check_one_discharge(
    src: TextIO, i: int, q_prop: float, pname: str = "dummy", q_prev: float = 0
) -> Optional[float]:
    """
    Interactively request discharge for which simulation results are available.

    Arguments
    ---------
    src : TextIO
        Source to read from (typically sys.stdin)
    i : int
        Discharge level (1, 2 or 3).
    q_prop : float
        Proposed discharge.
    pname : str
        Name of previous discharge level.
    q_prev : float
        Previous discharge.

    Returns
    -------
    q_new : Optional[float]
        Final discharge.
    """
    q_new: Optional[float]
    ApplicationSettingsHelper.log_text("")
    ApplicationSettingsHelper.log_text("input_avail", dict={"i": i, "q": q_prop})
    tdum = _interactive_get_bool(src, "confirm_or")
    q_new = q_prop
    if not tdum:
        while True:
            q_new = _interactive_get_float(src, "query_qavail", dict={"i": i})
            if q_new is None:
                break
            elif q_new < q_prev:
                ApplicationSettingsHelper.log_text("")
                if i == 1:
                    ApplicationSettingsHelper.log_text("qavail_too_small_1")
                else:
                    ApplicationSettingsHelper.log_text(
                        "qavail_too_small_2",
                        dict={"p": i - 1, "pname": pname, "qp": q_prev, "i": i},
                    )
            else:
                break
    return q_new


def _interactive_get_bool(src: TextIO, key: str, dict: Dict[str, Any] = {}) -> bool:
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


def _interactive_get_int(
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
    except ValueError:
        val = None
    return val


def _interactive_get_float(
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
    except ValueError:
        val = None
    return val


def _interactive_get_item(src: TextIO, type: str, list: List[str]) -> Optional[int]:
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
        The integer index of the item selected by the user (None if _interactive_get_int returns None).
    """
    i = 0
    nitems = len(list)
    while i < 1 or i > nitems:
        ApplicationSettingsHelper.log_text("query_" + type + "_header")
        for i in range(nitems):
            ApplicationSettingsHelper.log_text(
                "query_list", dict={"item": list[i], "index": i + 1}
            )
        i_opt = _interactive_get_int(src, "query_" + type)
        if i_opt is None:
            return None
        else:
            i = i_opt
    return i - 1
