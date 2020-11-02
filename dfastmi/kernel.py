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

import math
import numpy


def char_discharges(q_lvl, dq, q_threshold, q_bankfull):
    if not q_threshold is None:  # has threshold discharge
        Q1 = q_threshold
        if q_threshold < q_lvl[0]:
            if q_bankfull < q_lvl[2]:
                Q2 = max(q_bankfull, q_threshold + dq[1])
                Q3 = max(q_lvl[2], Q2 + dq[1])
            else:
                Q2 = q_lvl[1]
                Q3 = q_bankfull
        elif q_threshold < q_lvl[1]:
            Q2 = max(q_bankfull, q_threshold + dq[1])
            Q3 = q_lvl[2]
        else:  # q_threshold >= q_lvl[1]
            Q2 = None
            if q_threshold > q_lvl[2]:
                Q3 = min(q_threshold + dq[0], q_lvl[3])
            else:
                Q3 = max(q_lvl[2], q_threshold + dq[0])
    else:  # no threshold discharge
        Q1 = q_lvl[0]
        if q_bankfull < q_lvl[2]:
            Q2 = max(q_lvl[1], q_bankfull)
            Q3 = q_lvl[2]
        else:
            Q2 = min(q_lvl[1], q_bankfull - dq[1])
            Q3 = q_bankfull
        if Q2 == Q3:
            Q3 = None
        if Q1 == Q2:
            Q2 = None

    return [Q1, Q2, Q3]


def char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth):
    if q_stagnant > q_fit[0]:
        t_stagnant = 1 - math.exp((q_fit[0] - q_stagnant) / q_fit[1])
    else:
        t_stagnant = 0

    T = [0]*3
    T[0] = 1 - math.exp((q_fit[0] - Q[0]) / q_fit[1]) - t_stagnant
    if Q[1] is None:
        T[1] = 0
    else:
        T[1] = math.exp((q_fit[0] - Q[0]) / q_fit[1]) - math.exp((q_fit[0] - Q[1]) / q_fit[1])
    T[2] = max(1 - T[0] - T[1] - t_stagnant, 0)  # math.exp((q_fit[0] - Q[1])/q_fit[1])

    rsigma = [1]*3
    rsigma[0] = math.exp(-500 * celerity_lw * T[0] / nwidth)
    if not Q[1] is None:
        rsigma[1] = math.exp(-500 * celerity_hg * T[1] / nwidth)
    if not Q[2] is None:
        rsigma[2] = math.exp(-500 * celerity_hg * T[2] / nwidth)

    t_stagnant = int(365*t_stagnant)
    T[0] = int(365*T[0])
    T[1] = int(365*T[1])
    T[2] = max(365 - T[0] - T[1] - t_stagnant, 0)

    return t_stagnant, T, rsigma


def estimate_sedimentation_length(rsigma, nwidth):
    length = - sum(math.log(r) for r in rsigma)
    return int(2 * nwidth * length)


def dzq_from_du_and_h(u0, h0, u1, ucrit):
    with numpy.errstate(divide="ignore", invalid="ignore"):
        dzq = numpy.where(
            (abs(u0) > ucrit) & (abs(u1) > ucrit) & (abs(u0) < 100),
            h0 * (u0 - u1) / u0,
            numpy.NaN,
        )
    return dzq


def main_computation(dzq1, dzq2, dzq3, tstag, T, rsigma):
    mask = numpy.isnan(dzq1) | numpy.isnan(dzq2) | numpy.isnan(dzq3)
    sz = numpy.shape(dzq1)
    rsigma1l = numpy.ones(sz) * rsigma[0]
    rsigma2l = numpy.ones(sz) * rsigma[1]
    rsigma3l = numpy.ones(sz) * rsigma[2]
    rsigma1l[mask] = 1
    rsigma2l[mask] = 1
    rsigma3l[mask] = 1

    den = 1 - rsigma1l * rsigma2l * rsigma3l

    zmbb = (
        dzq1 * (1 - rsigma1l) * rsigma2l * rsigma3l
        + dzq2 * (1 - rsigma2l) * rsigma3l
        + dzq3 * (1 - rsigma3l)
    )

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

    zgem = z1o * (T[0] + T[2]) / 2 + z2o * ((T[1] + T[0]) / 2 + tstag) + z3o * (T[2] + T[1]) / 2

    return zgem, z1o, z2o
