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
from typing import Tuple, List, Optional

import math
import numpy

from dfastmi.kernel.typehints import QLevels, QChange, QRuns, Vector, BoolVector

def char_discharges(
    q_levels: QLevels, dq: QChange, q_threshold: Optional[float], q_bankfull: float
) -> Tuple[QRuns, BoolVector]:
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
    applyQ : BoolVector
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
) -> Tuple[float, Vector, Vector]:
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
    Q : Vector
        A list of 3 discharges for which simulation results are (expected to be) available.
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
    T : Vector
        A tuple of 3 values each representing the number of days during which the discharge is given by the corresponding entry in Q.
    rsigma : Vector
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


def relax_factors(Q: Vector, T: Vector, q_stagnant: float, celerity: Vector, nwidth: float) -> Vector:
    lsigma = [-1.0] * len(Q)
    for i,q in enumerate(Q):
         if q <= q_stagnant:
             lsigma[i] = 1.0
         else:
             lsigma[i] = math.exp(-500 * celerity[i] * T[i] / nwidth)
    rsigma = tuple(s for s in lsigma)

    return rsigma


def get_celerity(q: float, cel_q: Vector, cel_c: Vector) -> float:
    for i in range(len(cel_q)):
        if q < cel_q[i]:
            if i > 0:
                c = cel_c[i - 1] + (cel_c[i] - cel_c[i - 1]) * (q - cel_q[i - 1]) / (cel_q[i] - cel_q[i - 1])
            else:
                c = cel_c[0]
            break
    else:
        c = cel_c[-1]
    return c


def estimate_sedimentation_length(
    rsigma: Vector,
    applyQ: BoolVector,
    nwidth: float,
) -> float:
    """
    This routine computes the sedimentation length in metres.

    Arguments
    ---------
    rsigma : Vector
        A tuple of relaxation factors, one for each period.
    applyQ : BoolVector
        A tuple of 3 flags indicating whether each value should be used or not.
    nwidth : float
        Normal river width (from rivers configuration file).

    Returns
    -------
    L : float
        The expected yearly impacted sedimentation length.
    """
    logrsig = [0.0] * len(rsigma)
    for i in range(len(rsigma)):
        if applyQ[i]:
            logrsig[i] = math.log(rsigma[i])
    length = -sum(logrsig)
    
    return 2.0 * nwidth * length


def estimate_sedimentation_length2(
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
    Lt = [tmi[i] * celerity[i] for i in range(len(tmi))]
    
    return sum(Lt) * 1000


def dzq_from_du_and_h(
    u0: numpy.ndarray, h0: numpy.ndarray, u1: numpy.ndarray, ucrit: float, default: float = numpy.NaN,
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
        Array containing the flow velocity magnitudes in the simulation with the measure.
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
    T: Vector,
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
    T : Vector
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
    N = len(dzq)
    # N should also equal len(T) and len(rsigma)
    firstQ = True
    
    for i in range(len(dzq)):
        if dzq[i] is None:
            pass
        elif firstQ:
            mask = numpy.isnan(dzq[0])
            firstQ = False
        else:
            mask = mask | numpy.isnan(dzq[i])
    
    vsigma: List[numpy.ndarray]
    vsigma = []
    sz = numpy.shape(mask)
    for i in range(N):
        vsigma_tmp = numpy.ones(sz) * rsigma[i]
        vsigma_tmp[mask] = 1
        vsigma.append( vsigma_tmp )

    # compute denominator
    for i in range(N):
        if i == 0:
             den = vsigma[0]
        else:
             den = den * vsigma[i]
    den = 1 - den

    # compute dzb at beginning of each period
    dzb: List[numpy.ndarray]
    dzb = []
    for i in range(N):
        # compute enumerator
        for j in range(N):
            jr = (i + j) % N
            dzb_tmp = dzq[jr] * (1 - vsigma[jr])
            for k in range(j+1,N):
                kr = (i + k) % N
                dzb_tmp = dzb_tmp * vsigma[kr]
            if j == 0:
                enm = dzb_tmp
            else:
                enm = enm + dzb_tmp
        
        # divide by denominator
        with numpy.errstate(divide="ignore", invalid="ignore"):
            dzb.append(numpy.where(den != 0, enm / den, 0))
        
        # element-wise minimum and maximum
        if i == 0:
            dzmax = dzb[0]
            dzmin = dzb[0]
        else:
            dzmax = numpy.maximum(dzmax, dzb[i])
            dzmin = numpy.minimum(dzmin, dzb[i])

    # linear average
    for i in range(N):
        if i == 0:
            dzgem = dzb[0] * (T[0] + T[-1]) / 2
        else:
            dzgem = dzgem + dzb[i] * (T[i] + T[i-1]) / 2
    
    return dzgem, dzmax, dzmin, dzb
