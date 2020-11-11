# -*- coding: utf-8 -*-
"""
This module contains the main computational routines of the D-FAST
Morphological Impact application.

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

from typing import Tuple, Optional
import math
import numpy

QLevels = Tuple[float, float, float, float]
QChange = Tuple[float, float]
QRuns = Tuple[Optional[float], Optional[float], Optional[float]]


def char_discharges(
    q_levels: QLevels, dq: QChange, q_threshold: Optional[float], q_bankfull: float
) -> Tuple[QRuns, Tuple[bool, bool, bool]]:
    """
    This routine determines the discharges needed for the analysis.

    Arguments
    ---------
    q_levels : QLevels
        A tuple of 4 characteristic discharges (from rivers configuration file).
    dq : QChange
        A tuple of 2 characteristic discharge adjustments (from rivers configuration file).
    q_threshold : Optional[float]
        Optional threshold discharge at which measure starts to flow.
    q_bankfull : float
        Discharge at which measure is bankfull.

    Returns
    -------
    Q : QRuns
        A tuple of 3 discharges for which simulations should be run (can later
        be adjusted by the user)
    applyQ : Tuple[bool, bool, bool]
        A tuple of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.
    """
    Q1: float
    Q2: Optional[float]
    Q3: float

    if q_threshold is None:  # no threshold discharge
        Q1 = q_levels[0]
        use1 = True
        use2 = True
        if q_bankfull < q_levels[2]:
            Q2 = max(q_levels[1], q_bankfull)
            Q3 = q_levels[2]
        else:
            Q2 = min(q_levels[1], q_bankfull - dq[1])
            Q3 = q_bankfull
    else:  # has threshold discharge
        Q1 = q_threshold
        use1 = False
        if q_threshold < q_levels[0]:
            use2 = True
            if q_bankfull < q_levels[2]:
                Q2 = max(q_bankfull, q_threshold + dq[1])
                Q3 = max(q_levels[2], Q2 + dq[1])
            else:
                Q2 = q_levels[1]
                Q3 = q_bankfull
        elif q_threshold < q_levels[1]:
            use2 = True
            Q2 = max(q_bankfull, q_threshold + dq[1])
            Q3 = q_levels[2]
        else:  # q_threshold >= q_levels[1]
            Q2 = None
            use2 = False
            if q_threshold > q_levels[2]:
                Q3 = min(q_threshold + dq[0], q_levels[3])
            else:
                Q3 = max(q_levels[2], q_threshold + dq[0])

    return (Q1, Q2, Q3), (use1, use2, True)


def char_times(
    q_fit: Tuple[float, float],
    q_stagnant: float,
    Q: QRuns,
    celerity_hg: float,
    celerity_lw: float,
    nwidth: float,
) -> Tuple[float, Tuple[float, float, float], Tuple[float, float, float]]:
    """
    This routine determines the characteric times and rsigma.

    This routine computes:
    * the duration t_stagnant of the stagnant period
    * the duration T[0:2] of the three discharge Q[0:2] periods
    * the rsigma[0:2] of the three discharge Q[0:2] periods

    NOTE: the duration variables are initially defined as fraction of the year,
    but they are converted to number of days before returning.
    
    Arguments
    ---------
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    q_stagnant : float
        Discharge below which flow velocity is considered negligible (from rivers configuration file).
    Q : QRuns
        A tuple of 3 discharges for which simulation results are (expected to be) available.
    celerity_hg : float
        Bed celerity during transitional and flood periods (from rivers configuration file).
    celerity_lw : float
        Bed celerity during low flow period (from rivers configuration file).
    nwidth : float
        Normal river width (from rivers configuration file).

    Returns
    -------
    t_stagnant : float
        Number of days during which flow velocity is considered negligible.
    T : Tuple[float, float, float]
        A tuple of 3 values each representing the number of days during which the discharge is given by the corresponding entry in Q.
    rsigma : Tuple[float, float, float]
        A tuple of 3 values each representing the relaxation factor for the period given by the corresponding entry in Q.
    """
    if q_stagnant > q_fit[0]:
        t_stagnant_yr = 1 - math.exp((q_fit[0] - q_stagnant) / q_fit[1])
    else:
        t_stagnant_yr = 0

    T_yr = [0.0] * 3
    if not Q[0] is None:
        T_yr[0] = 1 - math.exp((q_fit[0] - Q[0]) / q_fit[1]) - t_stagnant_yr
    if not Q[1] is None and not Q[0] is None:
        T_yr[1] = math.exp((q_fit[0] - Q[0]) / q_fit[1]) - math.exp(
            (q_fit[0] - Q[1]) / q_fit[1]
        )
    T_yr[2] = max(1 - T_yr[0] - T_yr[1] - t_stagnant_yr, 0)

    rsigma0 = math.exp(-500 * celerity_lw * T_yr[0] / nwidth)
    rsigma1 = math.exp(-500 * celerity_hg * T_yr[1] / nwidth)
    rsigma2 = math.exp(-500 * celerity_hg * T_yr[2] / nwidth)
    rsigma = (rsigma0, rsigma1, rsigma2)

    T = (T_yr[0], T_yr[1], T_yr[2])

    return t_stagnant_yr, T, rsigma


def estimate_sedimentation_length(
    rsigma: Tuple[float, float, float], nwidth: float
) -> int:
    """
    This routine computes the sedimentation length in metres.

    Arguments
    ---------
    rsigma : Tuple[float, float, float]
        Relaxation factors of the 3 discharge periods.
    nwidth : float
        Normal river width (from rivers configuration file).

    Returns
    -------
    L : int
        The expected yearly impacted length.
    """
    length = -sum(math.log(r) for r in rsigma)
    return int(2 * nwidth * length)


def dzq_from_du_and_h(
    u0: numpy.ndarray, h0: numpy.ndarray, u1: numpy.ndarray, ucrit: float
) -> numpy.ndarray:
    """
    This routine computes dzq from the velocity change and water depth.

    Arguments
    ---------
    u0 : numpy.ndarray
        Array containing the flow velocities in the reference simulation.
    h0 : numpy.ndarray
        Array containing the water depths (in the reference simulation).
    u1 : numpy.ndarray
        Array containing the flow velocities in the simulation with the measure.
    ucrit : float
        Critical flow velocity below which no change is expected.

    Returns
    -------
    dzq : numpy.ndarray
        Array containing the equilibrium bed level change: h*(u0 - u1)/u0.
    """
    with numpy.errstate(divide="ignore", invalid="ignore"):
        dzq = numpy.where(
            (abs(u0) > ucrit) & (abs(u1) > ucrit) & (abs(u0) < 100),
            h0 * (u0 - u1) / u0,
            numpy.NaN,
        )
    return dzq


def main_computation(
    dzq1: numpy.ndarray,
    dzq2: numpy.ndarray,
    dzq3: numpy.ndarray,
    t_stagnant: float,
    T: Tuple[float, float, float],
    rsigma: Tuple[float, float, float],
) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    This routine computes the bed level changes.

    Arguments
    ---------
    dzq1 : numpy.ndarray
        Array containing the equilibrium bed level change of the lowest discharge.
    dzq2 : numpy.ndarray
        Array containing the equilibrium bed level change of the middle discharge.
    dzq3 : numpy.ndarray
        Array containing the equilibrium bed level change of the highest discharge.
    t_stagnant : float
        Number of days during which flow velocity is considered negligible.
    T : Tuple[float, float, float]
        A tuple of 3 values each representing the number of days during which the three discharges are valid.
    rsigma : Tuple[float, float, float]
        A tuple of 3 rsigma values.

    Returns
    -------
    zgem : numpy.ndarray
        Yearly mean bed level change.
    z1o : numpy.ndarray
        Maximum bed level change (after flood period).
    z2o : numpy.ndarray
        Minimum bed level change (after low flow period).
    """
    mask = numpy.isnan(dzq1) | numpy.isnan(dzq2) | numpy.isnan(dzq3)
    sz = numpy.shape(dzq1)
    rsigma1l = numpy.ones(sz) * rsigma[0]
    rsigma2l = numpy.ones(sz) * rsigma[1]
    rsigma3l = numpy.ones(sz) * rsigma[2]
    rsigma1l[mask] = 1
    rsigma2l[mask] = 1
    rsigma3l[mask] = 1

    den = 1 - rsigma1l * rsigma2l * rsigma3l

    #zmbb = (
    #    dzq1 * (1 - rsigma1l) * rsigma2l * rsigma3l
    #    + dzq2 * (1 - rsigma2l) * rsigma3l
    #    + dzq3 * (1 - rsigma3l)
    #)

    with numpy.errstate(divide="ignore", invalid="ignore"):
        z1o = numpy.where(
            den != 0,
            (
                dzq1 * (1 - rsigma1l) * rsigma2l * rsigma3l
                + dzq2 * (1 - rsigma2l) * rsigma3l
                + dzq3 * (1 - rsigma3l)
            )
            / den,
            0,
        )

        z2o = numpy.where(
            den != 0,
            (
                dzq1 * (1 - rsigma1l)
                + dzq2 * (1 - rsigma2l) * rsigma3l * rsigma1l
                + dzq3 * (1 - rsigma3l) * rsigma1l
            )
            / den,
            0,
        )

        z3o = numpy.where(
            den != 0,
            (
                dzq1 * (1 - rsigma1l) * rsigma2l
                + dzq2 * (1 - rsigma2l)
                + dzq3 * (1 - rsigma3l) * rsigma1l * rsigma2l
            )
            / den,
            0,
        )

    zgem = (
        z1o * (T[0] + T[2]) / 2
        + z2o * ((T[1] + T[0]) / 2 + t_stagnant)
        + z3o * (T[2] + T[1]) / 2
    )

    return zgem, z1o, z2o
