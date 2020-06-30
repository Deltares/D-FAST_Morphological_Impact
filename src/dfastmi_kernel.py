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


def program_version():
    return "PRE-ALPHA"


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

    return Q1, Q2, Q3


def char_times(q_fit, q_stagnant, Q1, Q2, Q3, celerity_hg, celerity_lw, nwidth):
    if q_stagnant > q_fit[0]:
        t_stagnant = 1 - math.exp((q_fit[0] - q_stagnant) / q_fit[1])
    else:
        t_stagnant = 0

    t1 = 1 - math.exp((q_fit[0] - Q1) / q_fit[1]) - t_stagnant
    if Q2 is None:
        t2 = 0
    else:
        t2 = math.exp((q_fit[0] - Q1) / q_fit[1]) - math.exp((q_fit[0] - Q2) / q_fit[1])
    t3 = max(1 - t1 - t2 - t_stagnant, 0)  # math.exp((q_fit[0]-Q2)/q_fit[1])

    rsigma1 = math.exp(-500 * celerity_lw * t1 / nwidth)
    if not Q2 is None:
        rsigma2 = math.exp(-500 * celerity_hg * t2 / nwidth)
    else:
        rsigma2 = 1
    if not Q3 is None:
        rsigma3 = math.exp(-500 * celerity_hg * t3 / nwidth)
    else:
        rsigma3 = 1

    return t_stagnant, t1, t2, t3, rsigma1, rsigma2, rsigma3


def estimate_sedimentation_length(rsigma1, rsigma2, rsigma3, nwidth):
    length = -math.log(rsigma1) - math.log(rsigma2) - math.log(rsigma3)
    return int(2 * nwidth * length)


def dzq_from_du_and_h(u0, h0, u1, ucrit):
    with numpy.errstate(divide="ignore", invalid="ignore"):
        dzq = numpy.where(
            (abs(u0) > ucrit) & (abs(u1) > ucrit) & (abs(u0) < 100),
            h0 * (u0 - u1) / u0,
            numpy.NaN,
        )
    return dzq


def main_computation(dzq1, dzq2, dzq3, tstag, t1, t2, t3, rsigma1, rsigma2, rsigma3):
    mask = numpy.isnan(dzq1) | numpy.isnan(dzq2) | numpy.isnan(dzq3)
    sz = numpy.shape(dzq1)
    rsigma1l = numpy.ones(sz) * rsigma1
    rsigma2l = numpy.ones(sz) * rsigma2
    rsigma3l = numpy.ones(sz) * rsigma3
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

    zgem = z1o * (t1 + t3) / 2 + z2o * ((t2 + t1) / 2 + tstag) + z3o * (t3 + t2) / 2

    return zgem, z1o, z2o
