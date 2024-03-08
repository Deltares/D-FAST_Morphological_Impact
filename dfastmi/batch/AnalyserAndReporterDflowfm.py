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

from typing import Dict, Any, Tuple, TextIO
from dfastmi.batch.AnalyserDflowfm import AnalyserDflowfm
from dfastmi.batch.ReporterDflowfm import ReporterDflowfm
from dfastmi.kernel.typehints import Vector, BoolVector

import shapely

def analyse_and_report_dflowfm(
    display: bool,
    report: TextIO,
    q_threshold: float,
    tstag: float,
    discharges: Vector,
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
    q_threshold : float
        Threshold discharge above which the measure is active.
    tstag : float
        Fraction of year that the river is stagnant.
    discharges : Vector
        Array of discharges; one for each forcing condition. (Q list of discharges)
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
    analyser = AnalyserDflowfm()
    missing_data, report_data = analyser.analyse(display, report, q_threshold, tstag, discharges, T, rsigma, slength, nwidth, ucrit, filenames, xykm, needs_tide, n_fields, tide_bc, old_zmin_zmax, outputdir, plotops)
    
    if missing_data:
        return missing_data
    
    reporter = ReporterDflowfm()
    reporter.report(display, outputdir, plotops, report_data)

    return not missing_data