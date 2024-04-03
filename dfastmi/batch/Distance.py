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

import math
from typing import Tuple

import numpy


def distance_to_chainage(
    sline: numpy.ndarray, kline: numpy.ndarray, spnt: numpy.ndarray
) -> numpy.ndarray:
    """
    Interpolate a quantity 'chainage' along a line to a given set of points.

    Arguments
    ---------
    sline : numpy.ndarray
        Array of length M containing the distance along a line. Distance should be monotoneously increasing.
    kline : numpy.ndarray
        Array of length M containing the chainage along a line.
    spnt : numpy.ndarray
        Array of length N containing the location of points measured as distance along the same line.

    Results
    -------
    kpnt : numpy.ndarray
        Array of length N containing the location of points expressed as chainage.
    """
    M = len(sline)
    N = len(spnt)

    # make sure that spnt is sorted
    isort = numpy.argsort(spnt)
    unsort = numpy.argsort(isort)
    spnt_sorted = spnt[isort]

    kpnt = numpy.zeros(N)
    j = 0
    for i in range(N):
        s = spnt_sorted[i]
        while j < M:
            if sline[j] < s:
                j = j + 1
            else:
                break
        if j == 0:
            # distance is less than the distance of the first point, snap to it
            kpnt[i] = kline[0]
        elif j == M:
            # distance is larger than the distance of all the points on the line, snap to the last point
            kpnt[i] = kline[-1]
        else:
            # somewhere in the middle, average the chainage values
            a = (s - sline[j - 1]) / (sline[j] - sline[j - 1])
            kpnt[i] = (1 - a) * kline[j - 1] + a * kline[j]

    return kpnt[unsort]


def distance_along_line(xyline: numpy.ndarray) -> numpy.ndarray:
    """
    Compute distance coordinate along the specified line

    Arguments
    ---------
    xyline : numpy.ndarray
        Array of size M x 2 containing the x,y data of a line.

    Results
    -------
    sline : numpy.ndarray
        Array of length M containing the distance along the line.
    """

    # compute distance coordinate along the line
    ds = numpy.sqrt(((xyline[1:] - xyline[:-1]) ** 2).sum(axis=1))
    sline = numpy.cumsum(numpy.concatenate([numpy.zeros(1), ds]))

    return sline


def get_direction(
    xyline: numpy.ndarray, spnt: numpy.ndarray
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Determine the orientation of a line at a given set of points.

    Arguments
    ---------
    xyline : numpy.ndarray
        Array containing the x,y data of a line.
    spnt : numpy.ndarray
        Array of length N containing the location of points measured as distance along the same line.

    Results
    -------
    dxpnt : numpy.ndarray
        Array of length N containing x-component of the unit direction vector at the given points.
    dypnt : numpy.ndarray
        Array of length N containing y-component of the unit direction vector at the given points.
    """
    sline = distance_along_line(xyline)
    M = len(sline)
    N = len(spnt)

    # make sure that spnt is sorted
    isort = numpy.argsort(spnt)
    unsort = numpy.argsort(isort)
    spnt_sorted = spnt[isort]

    dxpnt = numpy.zeros(N)
    dypnt = numpy.zeros(N)
    j = 0
    for i in range(N):
        s = spnt_sorted[i]
        while j < M:
            if sline[j] < s:
                j = j + 1
            else:
                break
        if j == 0:
            # distance is less than the distance of the first point, use the direction of the first line segment
            dxy = xyline[1] - xyline[0]
        elif j == M:
            # distance is larger than the distance of all the points on the line, use the direction of the last line segment
            dxy = xyline[-1] - xyline[-2]
        else:
            # somewhere in the middle, get the direction of the line segment
            dxy = xyline[j] - xyline[j - 1]
        ds = math.sqrt((dxy**2).sum())
        dxpnt[i] = dxy[0] / ds
        dypnt[i] = dxy[1] / ds

    return dxpnt[unsort], dypnt[unsort]
