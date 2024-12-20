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
from typing import Optional, Tuple

from dfastmi.kernel.typehints import BoolVector, QChange, QLevels, QRuns, Vector


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
        Optional threshold discharge at which intervention starts to flow.
    q_bankfull : float
        Discharge at which intervention is bankfull.

    Returns
    -------
    discharges : QRuns
        A tuple of 3 discharges for which simulations should be run (can later
        be adjusted by the user)
    apply_q : BoolVector
        A tuple of 3 flags indicating whether each value should be used or not.
        The Q1 value can't be set to None because it's needed for char_times.
    """
    Q1: float
    Q2: Optional[float]
    Q3: float

    if q_threshold is None:  # no threshold discharge
        Q1, Q2, Q3, use1, use2 = __get_discharges_without_threshold(
            q_levels, dq, q_bankfull
        )
    else:  # has threshold discharge
        Q1, Q2, Q3, use1, use2 = __get_discharges_with_threshold(
            q_levels, dq, q_threshold, q_bankfull
        )

    return (Q1, Q2, Q3), (use1, use2, True)


def __get_discharges_without_threshold(q_levels, dq, q_bankfull):
    Q1 = q_levels[0]
    use1 = True
    use2 = True
    if q_bankfull < q_levels[2]:
        Q2 = max(q_levels[1], q_bankfull)
        Q3 = q_levels[2]
    else:
        Q2 = min(q_levels[1], q_bankfull - dq[1])
        Q3 = q_bankfull
    return Q1, Q2, Q3, use1, use2


def __get_discharges_with_threshold(q_levels, dq, q_threshold, q_bankfull):
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
    return Q1, Q2, Q3, use1, use2


def char_times(
    q_fit: Tuple[float, float],
    q_stagnant: float,
    discharge_values: QRuns,
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

    t_yr = [0.0] * 3
    if discharge_values[0] is not None:
        t_yr[0] = (
            1 - math.exp((q_fit[0] - discharge_values[0]) / q_fit[1]) - t_stagnant_yr
        )
    if discharge_values[1] is not None and discharge_values[0] is not None:
        t_yr[1] = math.exp((q_fit[0] - discharge_values[0]) / q_fit[1]) - math.exp(
            (q_fit[0] - discharge_values[1]) / q_fit[1]
        )
    t_yr[2] = max(1 - t_yr[0] - t_yr[1] - t_stagnant_yr, 0)

    rsigma0 = math.exp(-500 * celerity_lw * t_yr[0] / nwidth)
    rsigma1 = math.exp(-500 * celerity_hg * t_yr[1] / nwidth)
    rsigma2 = math.exp(-500 * celerity_hg * t_yr[2] / nwidth)

    rsigma = (rsigma0, rsigma1, rsigma2)
    T = (t_yr[0], t_yr[1], t_yr[2])

    return t_stagnant_yr, T, rsigma
