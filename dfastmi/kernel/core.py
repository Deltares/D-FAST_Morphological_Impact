# -*- coding: utf-8 -*-
"""
This module contains the main computational routines of the D-FAST
Morphological Impact application.

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
import math
from typing import List, Tuple

import numpy

from dfastmi.kernel.BedLevelCalculator import BedLevelCalculator
from dfastmi.kernel.typehints import Vector


def relax_factors(
    discharge_values: Vector,
    year_fraction_values: Vector,
    q_stagnant: float,
    celerity: Vector,
    nwidth: float,
) -> Vector:
    lsigma = [-1.0] * len(discharge_values)
    for i, q in enumerate(discharge_values):
        if q <= q_stagnant:
            lsigma[i] = 1.0
        else:
            lsigma[i] = math.exp(-500 * celerity[i] * year_fraction_values[i] / nwidth)
    rsigma = tuple(s for s in lsigma)

    return rsigma


def estimate_sedimentation_length(
    tmi: Vector,
    celerity: Vector,
) -> float:
    """
    This routine computes the sedimentation length in metres.

    Arguments
    ---------
    tmi : Vector
        Morphological impact period of this discharge level [y].
    celerity : Vector
        Celerity of this discharge level [km/y].

    Returns
    -------
    L : float
        The expected yearly impacted sedimentation length [m].
    """
    sedimentation_length_contributions = [tmi[i] * celerity[i] for i in range(len(tmi))]
    KM_TO_M = 1000
    return sum(sedimentation_length_contributions) * KM_TO_M


def dzq_from_du_and_h(
    u0: numpy.ndarray,
    h0: numpy.ndarray,
    u1: numpy.ndarray,
    ucrit: float,
    default: float = numpy.NaN,
) -> numpy.ndarray:
    """
    This routine computes dzq from the velocity change and water depth.

    Arguments
    ---------
    u0 : numpy.ndarray
        Array containing the flow velocitiy magnitudes in the reference simulation.
    h0 : numpy.ndarray
        Array containing the water depths (in the reference simulation).
    u1 : numpy.ndarray
        Array containing the flow velocity magnitudes in the simulation with the intervention.
    ucrit : float
        Critical flow velocity below which no change is expected.

    Returns
    -------
    dzq : numpy.ndarray
        Array containing the equilibrium bed level change: h*(u0 - u1)/u0.
    """
    with numpy.errstate(divide="ignore", invalid="ignore"):
        dzq = numpy.where(
            (u0 > ucrit) & (u1 > ucrit) & (u0 < 100),
            h0 * (u0 - u1) / u0,
            default,
        )
    return dzq


def main_computation(
    dzq: List[numpy.ndarray],
    fraction_of_year: Vector,
    rsigma: Vector,
) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray, List[numpy.ndarray]]:
    """
    This routine computes the bed level changes.
    This routine requires that dzq, T and rsigma have the same length.
    A stagnant period can be represented by a period with rsigma = 1.

    Arguments
    ---------
    dzq : List[numpy.ndarray]
        A list of arrays containing the equilibrium bed level change for each respective discharge period.
    fraction_of_year : Vector
        A tuple of periods indicating the number of days during which each discharge applies.
    rsigma : Vector
        A tuple of relaxation factors, one for each period.

    Returns
    -------
    dzgem : numpy.ndarray
        Yearly mean bed level change.
    dzmax : numpy.ndarray
        Maximum bed level change.
    dzmin : numpy.ndarray
        Minimum bed level change.
    dzb   : List[numpy.ndarray]
        List of arrays containing the bed level change at the beginning of each respective discharge period.
    """
    number_of_periods = len(dzq)
    blc = BedLevelCalculator(number_of_periods)
    dzb = blc.get_bed_level_changes(dzq, rsigma)
    dzmax = blc.get_element_wise_maximum(dzb)
    dzmin = blc.get_element_wise_minimum(dzb)
    dzgem = blc.get_linear_average(fraction_of_year, dzb)

    return dzgem, dzmax, dzmin, dzb
