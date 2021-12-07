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
from dfastmi.io import RiversObject
from dfastmi.kernel import Vector, QRuns

import sys
import os
import math
import numpy
import dfastmi.io
import dfastmi.kernel
import configparser
from packaging import version


def batch_mode(config_file: str, rivers: RiversObject, reduced_output: bool) -> None:
    """
    Run the program in batch mode.

    Load the configuration file and run the analysis.

    Arguments
    ---------
    config_file
        Name of the configuration file.
    rivers : RiversObject
        A dictionary containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    """
    if reduced_output:
        dfastmi.io.log_text("reduce_output")

    try:
        config = load_configuration_file(config_file)
    except:
        print(sys.exc_info()[1])
    else:
        batch_mode_core(rivers, reduced_output, config)


def batch_mode_core(
    rivers: RiversObject, reduced_output: bool, config: configparser.ConfigParser
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

    Return
    ------
    success : bool
        Flag indicating whether the analysis could be completed successfully.
    """
    report = open(dfastmi.io.get_filename("report.out"), "w")

    prog_version = dfastmi.__version__
    dfastmi.io.log_text("header", dict={"version": prog_version}, file=report)
    dfastmi.io.log_text("limits", file=report)
    dfastmi.io.log_text("===", file=report)

    cfg_version = config["General"]["Version"]
    rvr_version = rivers["version"]
    if version.parse(cfg_version) != version.parse(rvr_version):
        raise Exception(
            "Version number of configuration file ({}) must match version number of rivers file ({})".format(
                cfg_version,
                rvr_version
            )
        )
    
    branch = config["General"]["Branch"]
    try:
        ibranch = rivers["branches"].index(branch)
    except:
        dfastmi.io.log_text("invalid_branch", dict={"branch": branch}, file=report)
        failed = True
    else:
        reach = config["General"]["Reach"]
        try:
            ireach = rivers["reaches"][ibranch].index(reach)
        except:
            dfastmi.io.log_text(
                "invalid_reach", dict={"reach": reach, "branch": branch}, file=report
            )
            failed = True
        else:
            nwidth = rivers["normal_width"][ibranch][ireach]
            q_location = rivers["qlocations"][ibranch]
            q_stagnant = rivers["qstagnant"][ibranch][ireach]
            needs_tide = False
            n_fields = 1
            tide_bc = []
            
            if version.parse(cfg_version) == version.parse("1"):
                # version 1
                celerity_hg = rivers["proprate_high"][ibranch][ireach]
                celerity_lw = rivers["proprate_low"][ibranch][ireach]
                (
                    all_q,
                    q_threshold,
                    q_bankfull,
                    q_fit,
                    Q,
                    applyQ,
                    tstag,
                    T,
                    rsigma,
                ) = batch_get_discharges(
                    rivers, ibranch, ireach, config, q_stagnant, celerity_hg, celerity_lw, nwidth
                )

            else:
                # version 2
                Q = rivers["hydro_q"][ibranch][ireach]
                applyQ = (True,) * len(Q)
                T = rivers["hydro_t"][ibranch][ireach]
                sumT = sum(T)
                T = tuple(t / sumT for t in T)
                prop_q = rivers["prop_q"][ibranch][ireach]
                prop_c = rivers["prop_c"][ibranch][ireach]
                needs_tide = rivers["tide"][ibranch][ireach]
                if needs_tide:
                    tide_bc = rivers["tide_bc"][ibranch][ireach]
                rsigma = dfastmi.kernel.relax_factors(Q, T, q_stagnant, prop_q, prop_c, nwidth)
                tstag = 0
                try:
                    n_fields = int(config["General"]["NFields"])
                except:
                    n_fields = 1
                if needs_tide and n_fields == 1:
                    raise Exception("Unexpected combination of tides and NFields = 1!")

            slength = dfastmi.kernel.estimate_sedimentation_length(rsigma, applyQ, nwidth)

            reach = rivers["reaches"][ibranch][ireach]
            ucrit = rivers["ucritical"][ibranch][ireach]
            if config["General"]["Mode"] == "WAQUA export":
                mode = 0
                dfastmi.io.log_text(
                    "results_with_input_waqua",
                    file=report,
                    dict={
                        "avgdzb": dfastmi.io.get_filename("avgdzb.out"),
                        "maxdzb": dfastmi.io.get_filename("maxdzb.out"),
                        "mindzb": dfastmi.io.get_filename("mindzb.out"),
                    },
                )
            else:
                mode = 1
                dfastmi.io.log_text(
                    "results_with_input_dflowfm",
                    file=report,
                    dict={"netcdf": dfastmi.io.get_filename("netcdf.out")},
                )
            filenames = get_filenames(mode, needs_tide, config)
            old_zmin_zmax = False
            if "RiverKM" in config["General"]:
                kmfile = config["General"]["RiverKM"]
            else:
                kmfile = ""
            failed = analyse_and_report(
                mode,
                False,
                report,
                reduced_output,
                reach,
                q_location,
                tstag,
                Q,
                T,
                rsigma,
                slength,
                nwidth,
                ucrit,
                filenames,
                kmfile,
                needs_tide,
                n_fields,
                tide_bc,
                old_zmin_zmax,
            )
            if slength > 1:
                nlength = int(slength)
            else:
                nlength = slength
            dfastmi.io.log_text(
                "length_estimate", dict={"nlength": nlength}, file=report
            )

    dfastmi.io.log_text("end", file=report)
    report.close()
    return failed


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
    t_stagnant : float
        Fraction of year during which flow velocity is considered negligible [-].
    T : Vector
        A tuple of 3 values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
    rsigma : Vector
        A tuple of 3 values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
    """
    q_threshold: Optional[float]

    stages = dfastmi.io.get_text("stage_descriptions")

    q_stagnant = rivers["qstagnant"][ibranch][ireach]
    q_fit = rivers["qfit"][ibranch][ireach]
    q_levels = rivers["qlevels"][ibranch][ireach]
    dq = rivers["dq"][ibranch][ireach]

    q_min = rivers["qmin"][ibranch][ireach]
    try:
        q_threshold = float(config["General"]["Qthreshold"])
    except:
        q_threshold = None

    if q_threshold is None or q_threshold < q_levels[1]:
        q_bankfull = float(config["General"]["Qbankfull"])
    else:
        q_bankfull = 0

    Q, applyQ = dfastmi.kernel.char_discharges(q_levels, dq, q_threshold, q_bankfull)

    tstag, T, rsigma = dfastmi.kernel.char_times(
        q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
    )

    QList = list(Q)
    for iq in range(3):
        if applyQ[iq]:
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
        applyQ,
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
    filenames = {}
    if imode == 0 or config is None:
        pass
    else:
        if config["General"]["Version"] == "1.0":
            for i in range(3):
                QSTR = "Q{}".format(i + 1)
                if QSTR in config:
                    reference = cfg_get(config, QSTR, "Reference")
                    measure = cfg_get(config, QSTR, "WithMeasure")
                    filenames[i] = (reference, measure)
        else:
            i = 0
            while True:
                i = i + 1
                CSTR = "C{}".format(i)
                if CSTR in config:
                    Q = float(cfg_get(config, CSTR, "Discharge"))
                    reference = cfg_get(config, CSTR, "Reference")
                    measure = cfg_get(config, CSTR, "WithMeasure")
                    if needs_tide:
                       T = int(cfg_get(config, CSTR, "TideBC"))
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
    tstag: float,
    Q: Vector,
    T: Vector,
    rsigma: Vector,
    slength: float,
    nwidth: float,
    ucrit: float,
    filenames: Dict[Any, Tuple[str,str]],
    kmfile: str,
    needs_tide: bool,
    n_fields: int,
    tide_bc: Vector,
    old_zmin_zmax: bool,
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
        Name of the location at which the discharge is
    tstag : float
        Fraction of year that the river is stagnant.
    Q : Vector
        Array of discharges; one for each forcing condition.
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
    kmfile : str
        Name of chainage file.
    needs_tide : bool
        Specifies whether the tidal boundary is needed.
    n_fields : int
        Number of fields to process (e.g. to cover a tidal period).
    tide_bc : Vector
        Array of tidal boundary condition; one per forcing condition.
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.

    Returns
    -------
    missing_data : bool
        Flag indicating whether analysis couldn't be carried out due to missing
        data.
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
            T,
            rsigma,
            slength,
            ucrit,
            old_zmin_zmax,
        )
    else:
        return analyse_and_report_dflowfm(
            display,
            report,
            reach,
            q_location,
            tstag,
            Q,
            T,
            rsigma,
            slength,
            nwidth,
            ucrit,
            filenames,
            kmfile,
            needs_tide,
            n_fields,
            tide_bc,
            old_zmin_zmax,
        )


def analyse_and_report_waqua(
    display: bool,
    report: TextIO,
    reduced_output: bool,
    reach: str,
    q_location: str,
    tstag: float,
    Q: Vector,
    T: Vector,
    rsigma: Vector,
    slength: float,
    ucrit: float,
    old_zmin_zmax: bool
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

    Returns
    -------
    missing_data : bool
        Flag indicating whether analysis couldn't be carried out due to missing
        data.
    """
    missing_data = False
    first_discharge = True
    
    dzq = [None] * len(Q)
    for i in range(3):
        if not missing_data and not Q[i] is None:
            if first_discharge:
                dzq[i], firstm, firstn = get_values_waqua3(
                    i+1, Q[i], ucrit, display, report, reduced_output
                )
                first_discharge = False
            else:
                dzq[i] = get_values_waqua1(i+1, Q[i], ucrit, display, report, reduced_output)
            if dzq[i] is None:
                missing_data = True
        else:
            dzq[i] = 0

    if not missing_data:
        if display:
            dfastmi.io.log_text("char_bed_changes")
            
        if tstag > 0:
            dzq = (dzq[0], 0*dzq[0], dzq[1], dzq[2])
            T = (T[0], tstag, T[1], T[2])
            rsigma = (rsigma[0], 1., rsigma[1], rsigma[2])
        
        # main_computation now returns new pointwise zmin and zmax
        data_zgem, data_zmax, data_zmin, dzb = dfastmi.kernel.main_computation(
            dzq, T, rsigma
        )
        if old_zmin_zmax:
            # get old zmax and zmin
            data_zmax = dzb[0]
            data_zmin = dzb[1]

        dfastmi.io.write_simona_box(
            dfastmi.io.get_filename("avgdzb.out"), data_zgem, firstm, firstn
        )
        dfastmi.io.write_simona_box(
            dfastmi.io.get_filename("maxdzb.out"), data_zmax, firstm, firstn
        )
        dfastmi.io.write_simona_box(
            dfastmi.io.get_filename("mindzb.out"), data_zmin, firstm, firstn
        )

    return missing_data


def analyse_and_report_dflowfm(
    display: bool,
    report: TextIO,
    reach: str,
    q_location: str,
    tstag: float,
    Q: Vector,
    T: Vector,
    rsigma: Vector,
    slength: float,
    nwidth: float,
    ucrit: float,
    filenames: Dict[Any, Tuple[str,str]],
    kmfile: str,
    needs_tide: bool,
    n_fields: int,
    tide_bc: Vector,
    old_zmin_zmax: bool
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
        Name of the location at which the discharge is
    tstag : float
        Fraction of year that the river is stagnant.
    Q : Vector
        Array of discharges; one for each forcing condition.
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
    kmfile : str
        Name of chainage file.
    needs_tide : bool
        Specifies whether the tidal boundary is needed.
    n_fields : int
        Number of fields to process (e.g. to cover a tidal period).
    tide_bc : Vector
        Array of tidal boundary condition; one per forcing condition.
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.

    Returns
    -------
    missing_data : bool
        Flag indicating whether analysis couldn't be carried out due to missing
        data.
    """
    first_discharge = True
    missing_data = False

    dzq = [None] * len(Q)
    if 0 in filenames.keys(): # the keys are 0,1,2
        one_fm_filename = filenames[0][0]
        for i in range(3):
            if not missing_data and not Q[i] is None:
                dzq[i] = get_values_fm(i+1, Q[i], ucrit, report, filenames[i], n_fields)
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
                    key = q
                if rsigma[i] == 1:
                    # no celerity, so ignore field
                    dzq[i] = 0
                elif key in filenames.keys():
                    one_fm_filename = filenames[key][0]
                    dzq[i] = get_values_fm(i+1, q, ucrit, report, filenames[key], n_fields)
                else:
                    if needs_tide:
                        dfastmi.io.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=report)
                    else:
                        dfastmi.io.log_text("no_file_specified_q_only", dict={"q": q}, file=report)
                    dfastmi.io.log_text("end_program", file=report)
                if dzq[i] is None:
                    missing_data = True
            else:
                dzq[i] = 0

    if not missing_data:
        if display:
            dfastmi.io.log_text("char_bed_changes")
            
        if tstag > 0:
            dzq = (dzq[0], dzq[0], dzq[1], dzq[2])
            T = (T[0], tstag, T[1], T[2])
            rsigma = (rsigma[0], 1., rsigma[1], rsigma[2])
            
        # main_computation now returns new pointwise zmin and zmax
        data_zgem, data_z1o, data_z2o, dzb = dfastmi.kernel.main_computation(
            dzq, T, rsigma
        )
        if old_zmin_zmax:
            # get old zmax and zmin
            data_zmax = dzb[0]
            zmax_str = "maximum bed level change after flood without dredging"
            data_zmin = dzb[1]
            zmin_str = "minimum bed level change after low flow without dredging"
        else:
            zmax_str = "maximum value of bed level change without dredging"
            zmin_str = "minimum value of bed level change without dredging"

        meshname, facedim = dfastmi.io.get_mesh_and_facedim_names(one_fm_filename)
        dst = dfastmi.io.get_filename("netcdf.out")
        dfastmi.io.copy_ugrid(one_fm_filename, meshname, dst)
        dfastmi.io.ugrid_add(
            dst,
            "avgdzb",
            data_zgem,
            meshname,
            facedim,
            long_name="year-averaged bed level change without dredging",
            units="m",
        )
        dfastmi.io.ugrid_add(
            dst,
            "maxdzb",
            data_z1o,
            meshname,
            facedim,
            long_name=zmax_str,
            units="m",
        )
        dfastmi.io.ugrid_add(
            dst,
            "mindzb",
            data_z2o,
            meshname,
            facedim,
            long_name=zmin_str,
            units="m",
        )
        for i in range(len(dzb)):
            j = (i + 1) % len(dzb)
            dfastmi.io.ugrid_add(
                dst,
                "dzb_{}".format(i),
                dzb[j],
                meshname,
                facedim,
                long_name="bed level change at end of period {}".format(i+1),
                units="m",
            )
            if rsigma[i]<1:
                dfastmi.io.ugrid_add(
                    dst,
                    "dzq_{}".format(i),
                    dzq[i],
                    meshname,
                    facedim,
                    long_name="equilibrium bed level change aimed for during period {}".format(i+1),
                    units="m",
                )
        
        dvol1,dvol2 = comp_dredging_volume(data_zgem, slength, nwidth,kmfile,one_fm_filename)
        print("Initial year dredging volume")
        print("Estimate 1: ",dvol1)
        print("Estimate 2: ",dvol2)

    return missing_data


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
        dfastmi.io.log_text("input_xyz", dict={"stage": stage, "q": q})
        dfastmi.io.log_text("---")
        dfastmi.io.log_text("")

    discriptions = dfastmi.io.get_text("file_descriptions")
    quantities = ["velocity-zeta.001", "waterdepth-zeta.001", "velocity-zeta.002"]
    files = []
    for i in range(3):
        if display:
            dfastmi.io.log_text("input_xyz_name", dict={"name": discriptions[i]})
        cifil = "xyz_" + quantities[i] + ".Q" + cblok + ".xyz"
        if display:
            print(cifil)
        if not os.path.isfile(cifil):
            dfastmi.io.log_text("file_not_found", dict={"name": cifil})
            dfastmi.io.log_text("file_not_found", dict={"name": cifil}, file=report)
            dfastmi.io.log_text("end_program", file=report)
            return numpy.array([]), 0, 0
        else:
            if display:
                dfastmi.io.log_text("input_xyz_found", dict={"name": cifil})
        files.extend([cifil])
        if display:
            dfastmi.io.log_text("")

    if display:
        dfastmi.io.log_text("input_xyz_read", dict={"stage": stage})
    u0temp = dfastmi.io.read_waqua_xyz(files[0], cols=(2, 3, 4))
    m = u0temp[:, 1].astype(int) - 1
    n = u0temp[:, 2].astype(int) - 1
    u0temp = u0temp[:, 0]
    h0temp = dfastmi.io.read_waqua_xyz(files[1])
    u1temp = dfastmi.io.read_waqua_xyz(files[2])

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

    dzq = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
    if display:
        dfastmi.io.log_text("---")
    return dzq, firstm, firstn


def get_values_fm(
    stage: int,
    q: float,
    ucrit: float,
    report: TextIO,
    filenames: Tuple[str, str],
    n_fields: int,
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

    Returns
    -------
    dzq : numpy.ndarray
        Array containing equilibrium bed level change.
    """
    cblok = str(stage)

    # reference file
    if filenames[0] == "":
        dfastmi.io.log_text("no_file_specified", dict={"q": q}, file=report)
        dfastmi.io.log_text("end_program", file=report)
        return None
    elif not os.path.isfile(filenames[0]):
        dfastmi.io.log_text("file_not_found", dict={"name": filenames[0]}, file=report)
        dfastmi.io.log_text("end_program", file=report)
        return None
    else:
        pass

    # file with measure implemented
    if not os.path.isfile(filenames[1]):
        dfastmi.io.log_text("file_not_found", dict={"name": filenames[1]}, file=report)
        dfastmi.io.log_text("end_program", file=report)
        return None
    else:
        pass

    dzq = 0.
    tot = 0.
    ifld: Optional[int]

    for ifld in range(n_fields):
        # if last time step is needed, pass None to allow for files without time specification
        if n_fields == 1:
            ifld = None

        # reference data
        u = dfastmi.io.read_fm_map(filenames[0], "sea_water_x_velocity", ifld=ifld)
        v = dfastmi.io.read_fm_map(filenames[0], "sea_water_x_velocity", ifld=ifld)
        u0 = numpy.sqrt(u ** 2 + v ** 2)
        h0 = dfastmi.io.read_fm_map(filenames[0], "sea_floor_depth_below_sea_surface", ifld=ifld)

        # data with measure
        u = dfastmi.io.read_fm_map(filenames[1], "sea_water_x_velocity", ifld=ifld)
        v = dfastmi.io.read_fm_map(filenames[1], "sea_water_x_velocity", ifld=ifld)
        u1 = numpy.sqrt(u ** 2 + v ** 2)

        dzq1 = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)

        if n_fields <= 2 or (ifld > 0 and ifld < n_fields - 1):
            wght = 1.
        else:
            wght = 0.5
        tot = tot + wght
        dzq = dzq + wght * dzq1
    
    dzq = dzq / tot
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
    dfastmi.io.log_text("", file=report)
    dfastmi.io.log_text("reach", dict={"reach": reach}, file=report)
    dfastmi.io.log_text("", file=report)
    if not q_threshold is None:
        dfastmi.io.log_text(
            "report_qthreshold",
            dict={"q": q_threshold, "border": q_location},
            file=report,
        )
    dfastmi.io.log_text(
        "report_qbankfull", dict={"q": q_bankfull, "border": q_location}, file=report,
    )
    dfastmi.io.log_text("", file=report)
    if q_stagnant > q_fit[0]:
        dfastmi.io.log_text(
            "closed_barriers", dict={"ndays": int(365 * tstag)}, file=report
        )
        dfastmi.io.log_text("", file=report)
    for i in range(3):
        if not Q[i] is None:
            dfastmi.io.log_text(
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
            dfastmi.io.log_text(
                "char_period", dict={"n": i + 1, "ndays": tdays}, file=report
            )
            if i < 2:
                dfastmi.io.log_text("", file=report)
            else:
                dfastmi.io.log_text("---", file=report)
    nQ = countQ(Q)
    if nQ == 1:
        dfastmi.io.log_text("need_single_input", dict={"reach": reach}, file=report)
    else:
        dfastmi.io.log_text(
            "need_multiple_input", dict={"reach": reach, "numq": nQ}, file=report,
        )
    for i in range(3):
        if not Q[i] is None:
            dfastmi.io.log_text(
                stagename(i), dict={"q": Q[i], "border": q_location}, file=report
            )
    dfastmi.io.log_text("---", file=report)
    if slength > 1:
        nlength = int(slength)
    else:
        nlength = slength
    dfastmi.io.log_text("length_estimate", dict={"nlength": nlength}, file=report)
    dfastmi.io.log_text("prepare_input", file=report)


def config_to_absolute_paths(
    filename: str, config: configparser.ConfigParser
) -> configparser.ConfigParser:
    """
    Convert a configuration object to contain absolute paths (for editing).

    Arguments
    ---------
    filename : str
        The name of the file: all relative paths in the configuration will be assumed relative to this.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with absolute or relative paths.

    Returns
    -------
    aconfig : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with only absolute paths.
    """
    rootdir = os.path.dirname(filename)
    if "RiverKM" in config["General"]:
        config["General"]["RiverKM"] = dfastmi.io.absolute_path(
            rootdir, config["General"]["RiverKM"]
        )
    for QSTR in config.keys():
        if "Reference" in config[QSTR]:
            config[QSTR]["Reference"] = dfastmi.io.absolute_path(
                rootdir, config[QSTR]["Reference"]
            )
        if "WithMeasure" in config[QSTR]:
            config[QSTR]["WithMeasure"] = dfastmi.io.absolute_path(
                rootdir, config[QSTR]["WithMeasure"]
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

    return config_to_absolute_paths(filename, config)


def config_to_relative_paths(
    filename: str, config: configparser.ConfigParser
) -> configparser.ConfigParser:
    """
    Convert a configuration object to contain relative paths (for saving).

    Arguments
    ---------
    filename : str
        The name of the file: all paths will be defined relative to this.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with only absolute paths.

    Returns
    -------
    rconfig : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis with as much as possible relative paths.
    """
    rootdir = os.path.dirname(filename)
    if "RiverKM" in config["General"]:
        config["General"]["RiverKM"] = dfastmi.io.relative_path(
            rootdir, config["General"]["RiverKM"]
        )
    for QSTR in config.keys():
        if "Reference" in config[QSTR]:
            config[QSTR]["Reference"] = dfastmi.io.relative_path(
                rootdir, config[QSTR]["Reference"]
            )
        if "WithMeasure" in config[QSTR]:
            config[QSTR]["WithMeasure"] = dfastmi.io.relative_path(
                rootdir, config[QSTR]["WithMeasure"]
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
    config = config_to_relative_paths(filename, config)
    dfastmi.io.write_config(filename, config)


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


def comp_dredging_volume(
    dzgem: numpy.ndarray,
    slength: float,
    nwidth: float,
    kmfile: str,
    simfile: str,
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
    kmfile : str
        Name of chainage file.
    simfile : str
        Name of simulation file.

    Returns
    -------
    dvol : float
        Dredging volume [m3].
    """
    dzmin = 0.01
    nwbins = 10
    sbin_length = 10.0
    
    xn, yn, FNC = get_xynode_connect(simfile)
    xni, yni, FNCi, dzgemi = dz_filter(xn, yn, FNC, dzgem, dzmin)
    areai = xynode_2_area(xni, yni, FNCi)

    if kmfile == "":
        dvol1 = math.nan
    else:
        xykm = dfastmi.io.get_xykm(kmfile)
        xy_numpy = numpy.array(xykm)[:, :2]
        dvol1 = comp_dredging_volume1(dzgemi, areai, xni, yni, FNCi, slength, nwidth, nwbins, sbin_length)
    
    dvol2 = comp_dredging_volume2(dzgemi, areai, slength, nwidth)
    return dvol1, dvol2


def stream_bins(min_s, max_s, ds):
    sbin_min = math.floor(min_s.min()/ds)
    sbin_max = math.ceil(max_s.max()/ds)
    sthresh = numpy.arange(sbin_min, sbin_max+2) * ds
    
    min_sbin = numpy.floor(min_s/ds).astype(numpy.int) - sbin_min
    max_sbin = numpy.floor(max_s/ds).astype(numpy.int) - sbin_min
    
    nsbin = max_sbin - min_sbin + 1
    nsbin_tot = nsbin.sum()
    
    iface = numpy.zeros(nsbin_tot, dtype=numpy.int)
    afrac = numpy.zeros(nsbin_tot)
    sbin  = numpy.zeros(nsbin_tot, dtype=numpy.int)
    nfaces = len(min_s)
    j = 0
    for i in range(nfaces):
        s0 = min_s[i]
        s1 = max_s[i]
        wght = 1 / (s1 - s0)
        for ib in range(min_sbin[i], max_sbin[i]+1):
            iface[j] = i
            afrac[j] = wght * (min(sthresh[ib+1], s1) - max(sthresh[ib], s0))
            sbin[j] = ib
            j = j + 1

    return iface, afrac, sbin, sthresh


def min_max_s(s, FNC):
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int) * FNC.data.shape[1]
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
    

def comp_dredging_volume1(
    dzgemi: numpy.ndarray,
    areai: numpy.ndarray,
    xni: numpy.ndarray,
    yni: numpy.ndarray,
    FNCi: numpy.ma.masked_array,
    xyline: numpy.ndarray,
    slength: float,
    nwidth: float,
    nwbins: int = 10,
    sbin_length: float = 10.0
) -> float:
    """
    Compute the yearly dredging volume.
    Algorithm 1.

    Arguments
    ---------
    dzgemi : numpy.ndarray
        Array of length M containing the yearly mean bed level change per cell [m].
    areai : numpy.ndarray
        Array of length M containing the grid cell area [m2].
    xni : numpy.ndarray
        Array of length K containing the x-coordinates of the nodes [m].
    yni : numpy.ndarray
        Array of length K containing the y-coordinate of the nodes [m2].
    FNCi : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.
    xyline : numpy.ndarray
        Array containing the x,y data of a line.
    slength : float
        The expected yearly impacted sedimentation length [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].
    nwbins : int
        Number of bins to subdivide the normal width into [-].
    sbin_length : float
        Size of bins in streamwise direction [m].

    Returns
    -------
    dvol : float
        Dredging volume [m3].
    """
    sni, dni = proj_xy_line(xni, yni, xyline)
    
    dfi = face_mean(dni, FNCi)
    wbini, wthresh = width_bins(dfi, nwidth, nwbins)
    
    min_sfi, max_sfi = min_max_s(sni, FNCi)
    iface, afrac, sbin, sthresh = stream_bins(min_sfi, max_sfi, sbin_length)
    
    wbin = wbini[iface]
    dvoli = dzgemi * areai
    n_wbin = len(wthresh)-1
    n_sbin = sbin.max()+1
    binvol = [None] * n_wbin
    dredge_vol = 0
    for iw in range(n_wbin):
        lw = wbin == iw
        bvol = numpy.bincount(sbin[lw], weights = dvoli[iface[lw]] * afrac[lw], minlength = n_sbin)
        binvol[iw] = bvol
        
        gap = True
        dvol = 0
        for ib in range(len(bvol)):
            if bvol[ib] > 0:
                if gap:
                    s0 = sthresh[ib]
                    gap = False
                dvol = dvol + bvol[ib] * (max(0, min(s0 - sthresh[ib] + slength, sbin_length)) / sbin_length)
            else:
                if dvol > 0:
                    #print("width bin {}, start {}, volume {}".format(iw,s0,dvol))
                    dredge_vol = dredge_vol + dvol
                    dvol = 0
                gap = True
        if dvol > 0:
            #print("width bin {}, start {}, volume {}".format(iw,s0,dvol))
            dredge_vol = dredge_vol + dvol
            dvol = 0

    xf = face_mean(xn, FNC)
    yf = face_mean(yn, FNC)
    #with open("zgem.xyz", "w") as file:
    #    for i in range(len(xf)):
    #        file.write("{:.2f} {:.2f} {:.6f}\n".format(xf[i],yf[i],dzgem[i]))

    xfi = face_mean(xni, FNCi)
    yfi = face_mean(yni, FNCi)
    #with open("zgem_filtered.xyz", "w") as file:
    #    for i in range(len(xfi)):
    #        file.write("{:.2f} {:.2f} {:.6f}\n".format(xfi[i],yfi[i],dzgemi[i]))

    #with open("node_sd_filtered.xyz", "w") as file:
    #    for i in range(len(sni)):
    #        file.write("{:.2f} {:.2f} {:.2f} {:.2f}\n".format(sni[i],dni[i],sni[i],dni[i]))

    sfi = face_mean(sni, FNCi)
    #with open("zgem_sd_filtered.xyz", "w") as file:
    #    for i in range(len(sfi)):
    #        file.write("{:.2f} {:.2f} {:.6f} {:.2f} {:.2f}\n".format(sfi[i],dfi[i],dzgemi[i],min_sfi[i],max_sfi[i]))

    binvol2 = numpy.stack(binvol)
    with open("binned_data.xyz", "w") as file:
        for i in range(n_sbin):
            vol_str = " ".join("{:.2f}".format(i) for i in binvol2[:,i])
            file.write("{:.2f} ".format((sthresh[i] + sthresh[i+1])/2) + vol_str + "\n")

    return dredge_vol


def comp_dredging_volume2(
    dzgemi: numpy.ndarray,
    areai: numpy.ndarray,
    slength: float,
    nwidth: float,
) -> float:
    """
    Compute the yearly dredging volume.
    Algorithm 2.

    Arguments
    ---------
    dzgemi : numpy.ndarray
        Array of length M containing the yearly mean bed level change per cell [m].
        Array clipped to values with dzgem > dzmin.
    areai : numpy.ndarray
        Array of length M containing the grid cell area [m2].
        Array clipped to values with dzgem > dzmin.
    slength : float
        The expected yearly impacted sedimentation length [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].

    Returns
    -------
    dvol : float
        Dredging volume [m3].
    """
    dvol_eq = (dzgemi * areai).sum()
    area_eq = areai.sum()
    dvol = dvol_eq * (slength * nwidth) / area_eq
    return dvol


def get_xynode_connect(filename: str) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    xn = dfastmi.io.read_fm_map(filename, "x", location="node")
    yn = dfastmi.io.read_fm_map(filename, "y", location="node")
    FNC = dfastmi.io.read_fm_map(filename, "face_node_connectivity")
    
    return xn, yn, FNC

def xynode_2_area(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int) * FNC.data.shape[1]
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
    

def face_mean(vn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)
    nfaces = FNC.shape[0]
    vf = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = FNC[i]
        nni = nnodes[i]
        vni = vn[fni][0:nni]
        vf[i] = vni.mean()
    
    return vf
    

def dz_filter(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ma.masked_array, dzb: numpy.ndarray, dzbmin: float):
    iface = numpy.where(dzb > dzbmin)
    FNCi = FNC[iface]
    inode = numpy.unique(FNCi.flatten())
    inode_max = inode.max()

    FNCi.data[FNCi.mask] = 0
    renum = numpy.zeros(inode_max + 1, dtype=numpy.int)
    renum[inode] = range(len(inode))
    rFNCi = numpy.ma.masked_array(renum[FNCi], mask=FNCi.mask)

    return xn[inode], yn[inode], rFNCi, dzb[iface]


def proj_xy_line(xf: numpy.ndarray, yf: numpy.ndarray, xyline: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Project chainage values from source line L1 onto another line L2.

    The chainage values are giving along a line L1 (xykm_numpy). For each node
    of the line L2 (line_xy) on which we would like to know the chainage, first
    the closest node (discrete set of nodes) on L1 is determined and
    subsequently the exact chainage isobtained by determining the closest point
    (continuous line) on L1 for which the chainage is determined using by means
    of interpolation.

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

    # compute coordinate
    ds = numpy.sqrt(((xyline[1:] - xyline[:-1]) **2).sum(axis=1))
    sline = numpy.cumsum(numpy.concatenate([numpy.zeros(1),ds]))
    
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
        
        # if we didn't get the first node
        if imin > 0:
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

        # if we didn't get the last node
        if imin < last_node:
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
