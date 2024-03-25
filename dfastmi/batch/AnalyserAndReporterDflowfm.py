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

from pathlib import Path
from typing import Dict, Any, Tuple, TextIO
from dfastmi.batch.AnalyserDflowfm import AnalyserDflowfm
from dfastmi.batch.ReporterDflowfm import ReporterDflowfm
from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase

import shapely

def analyse_and_report_dflowfm(
    display: bool,
    report: TextIO,
    nwidth: float,
    filenames: Dict[Any, Tuple[str,str]],
    xykm: shapely.geometry.linestring.LineString,
    old_zmin_zmax: bool,
    outputdir: Path,
    plotops: Dict,
    initialized_config : AConfigurationInitializerBase
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
    nwidth : float
        normal width of the reach.
    filenames : Dict[Any, Tuple[str,str]]
        Dictionary of the names of the data file containing the simulation
        results to be processed. The conditions (discharge, wave conditions,
        ...) are the key in the dictionary. Per condition a tuple of two file
        names is given: a reference file and a file with measure.
    xykm : shapely.geometry.linestring.LineString
        Original river chainage line.
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.
    outputdir : Path
        Path of output directory.
    plotops : Dict
        Dictionary of plot settings
    initialized_config : AConfigurationInitializerBase
        DTO with discharges, times, etc. for analysis

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out.
    """
    analyser = AnalyserDflowfm(display, report, old_zmin_zmax, outputdir, initialized_config)
    missing_data, report_data = analyser.analyse(nwidth, filenames, xykm, plotops)
    
    if missing_data:
        return missing_data
    
    reporter = ReporterDflowfm(display)
    reporter.report(outputdir, plotops, report_data)

    return not missing_data