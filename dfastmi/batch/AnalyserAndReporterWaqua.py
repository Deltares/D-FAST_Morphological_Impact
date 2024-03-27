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

from typing import TextIO
from dfastmi.batch.AnalyserWaqua import AnalyserWaqua
from dfastmi.batch.ReporterWaqua import ReporterWaqua
from dfastmi.kernel.typehints import Vector, BoolVector

def analyse_and_report_waqua(
    display: bool,
    report: TextIO,
    reduced_output: bool,
    tstag: float,
    discharges: Vector,
    apply_q: BoolVector,
    fraction_of_year: Vector,
    rsigma: Vector,
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
    tstag : float
        Number of days that the river is stagnant.
    discharges : Vector
        Array of discharges; one for each forcing condition. (Q list of discharges)
    apply_q : BoolVector
        A tuple of 3 flags indicating whether each value should be used or not.
    fraction_of_year : Vector
        Fraction of year represented by each forcing condition. (T list of fraction of year)
    rsigma : Vector
        Array of relaxation factors; one per forcing condition.
    ucrit : float
        Critical flow velocity [m/s].
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.
    outputdir : str
        Name of the output directory.

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out. (always true)
    """
    waqua = AnalyserWaqua(display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax)
    output_data = waqua.analyse(fraction_of_year, rsigma)

    waqua_reporter = ReporterWaqua(outputdir)
    waqua_reporter.write_report(output_data)

    return True