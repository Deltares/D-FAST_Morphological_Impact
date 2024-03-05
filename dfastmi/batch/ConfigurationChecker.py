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

from typing import Optional, Tuple
from dfastmi.io.Reach import ReachLegacy
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import Vector, BoolVector, QRuns
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

import dfastmi.kernel.core
import dfastmi.kernel.legacy
import dfastmi.plotting
import configparser

WAQUA_EXPORT = "WAQUA export"
DFLOWFM_MAP = "D-Flow FM map"

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
    try:
        reach = get_reach(rivers, config)
    except:
        return False

    nwidth = reach.normal_width
    [_, apply_q, _, _, _, _, _, _] = get_levels_v1(reach, config, nwidth)
    
    mode_str = config["General"].get("Mode", DFLOWFM_MAP)
    for i in range(3):
        if not apply_q[i]:
            continue
        
        if not check_configuration_v1_cond(config, mode_str, i):
            return False
                
    return True

def get_reach(rivers, config):
    """

    """ 
    branch_name = config["General"]["Branch"]
    
    if not any(branch.name == branch_name for branch in rivers.branches):
        raise Exception("Branch not in file {}!".format(branch_name))
    
    ibranch = next((i for i, branch in enumerate(rivers.branches) if branch.name == branch_name), -1)

    reach_name = config["General"]["Reach"]
    
    if not any(reach.name == reach_name for reach in rivers.branches[ibranch].reaches):
        raise Exception("Branch not in file {}!".format(branch_name))
    
    ireach = next((i for i, reach in enumerate(rivers.branches[ibranch].reaches) if reach.name == reach_name), -1)
    reach = rivers.branches[ibranch].reaches[ireach]
    return reach

def get_levels_v1(
    reach: ReachLegacy, config: configparser.ConfigParser, nwidth: float
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
    q_stagnant = reach.qstagnant
    celerity_hg = reach.proprate_high
    celerity_lw = reach.proprate_low

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
        reach, config, q_stagnant, celerity_hg, celerity_lw, nwidth
    )
    Q = Q1
    apply_q = apply_q1
    time_mi = tuple(0 if Q[i] is None or Q[i]<=q_stagnant else T[i] for i in range(len(T)))
    celerity = (celerity_lw, celerity_hg, celerity_hg)
    
    return (Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity)

def batch_get_discharges(
    reach : ReachLegacy,
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

    q_stagnant = reach.qstagnant
    q_fit = reach.qfit
    q_levels = reach.qlevels
    dq = reach.dq

    q_min = reach.qmin
    try:
        q_threshold = float(config["General"]["Qthreshold"])
    except:
        q_threshold = None

    if q_threshold is None or q_threshold < q_levels[1]:
        q_bankfull = float(config["General"]["Qbankfull"])
    else:
        q_bankfull = 0

    Q, apply_q = dfastmi.kernel.legacy.char_discharges(q_levels, dq, q_threshold, q_bankfull)

    tstag, T, rsigma = dfastmi.kernel.legacy.char_times(
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
    try:
        reach = get_reach(rivers, config)
    except:
        return False

    hydro_q = reach.hydro_q
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