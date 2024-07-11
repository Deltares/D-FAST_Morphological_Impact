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

import dfastmi.batch.Distance
import dfastmi.batch.Face


def project_xy_point_onto_line(
    xf: numpy.ndarray, yf: numpy.ndarray, xyline: numpy.ndarray
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Project points onto a line.

    For a set of points (xf, yf) the closest point P a line (xyline) is determined.
    The quantities returned are the distance (sf) measured along the line (xyline)
    for the closest point P, the signed distance (df) between the original point (xf, yf)
    and the projected point P. If the original point is located alongsize the line
    (xyline) then the distance (df) is the normal distance ... if the original point is
    located before or beyond the line (xyline), it will include an oblique distance component.
    The sign of the distance (df) is positive for points to the right and negative for points
    to the left of the line.

    Arguments
    ---------
    xf : numpy.ndarray
        Array containing the x coordinates of a set of points.
    yf : numpy.ndarray
        Array containing the y coordinates of a set of points.
    xyline : numpy.ndarray
        Array containing the x,y data of a line.

    Results
    -------
    sf : numpy.ndarray
        Array containing the distance along the line.
    df : numpy.ndarray
        Array containing the distance from the line (- for left, + for right).
    """
    # combine xf and yf
    nf = len(xf)
    xyf = numpy.concatenate([xf.reshape((nf, 1)), yf.reshape((nf, 1))], axis=1)

    # pre-allocate the output arrays
    sf = numpy.zeros(nf)
    df = numpy.zeros(nf)

    # compute distance coordinate along the line
    sline = dfastmi.batch.Distance.distance_along_line(xyline)

    # get an array with only the x,y coordinates of xyline
    last_node = xyline.shape[0] - 1

    # for each point
    for i, xyp in enumerate(xyf):
        sf[i], df[i] = _project_one_xy_point_onto_line(xyp, xyline, sline, last_node)

    return sf, df


def _project_one_xy_point_onto_line(
    xyp: numpy.ndarray, xyline: numpy.ndarray, sline: numpy.ndarray, last_node: int
) -> Tuple[float, float]:
    """
    Project a single point onto a line.

    For a point xyp the closest point P a line (xyline) is determined.
    The quantities returned are the distance (s) measured along the line (xyline)
    for the closest point P, the signed distance (d) between the original point (xf, yf)
    and the projected point P. If the original point is located alongsize the line
    (xyline) then the distance (df) is the normal distance ... if the original point is
    located before or beyond the line (xyline), it will include an oblique distance component.
    The sign of the distance (df) is positive for points to the right and negative for points
    to the left of the line.

    Arguments
    ---------
    xyp : numpy.ndarray
        Array containing the x and y coordinate of a point.
    xyline : numpy.ndarray
        Array containing the x,y data of a line.
    sline : numpy.ndarray
        Array containing the distance intervention along the line xyline.
    last_node : int
        Index of the last node: xyline.shape[0] - 1

    Results
    -------
    s : float
        Distance along the line.
    d : float
        The distance from the line (- for left, + for right).
    """
    # find the node on xyline closest to xyp
    imin = numpy.argmin(((xyp - xyline) ** 2).sum(axis=1))
    p0 = xyline[imin]

    # determine the distance between that node and xyp
    dist = ((xyp - p0) ** 2).sum()

    # distance value of that node
    s0 = sline[imin]
    s = s0

    if imin == 0:
        # we got the first node
        # check if xyp projects much before the first line segment.
        dist, sgn = _project_one_xy_point_beyond_segment(
            xyp, p0, xyline[imin + 1], 1.0, dist
        )

    else:
        # we didn't get the first node
        # project xyp onto the line segment before this node
        dist, sgn, s = _project_one_xy_point_onto_segment(
            xyp, p0, xyline[imin - 1], -1.0, dist, s, s0, sline[imin - 1]
        )

    if imin == last_node:
        # we got the last node
        # check if xyp projects much beyond the last line segment.
        dist, sgn = _project_one_xy_point_beyond_segment(
            xyp, p0, xyline[imin - 1], -1.0, dist
        )

    else:
        # we didn't get the last node
        # project rp onto the line segment after this node
        dist, sgn, s = _project_one_xy_point_onto_segment(
            xyp, p0, xyline[imin + 1], 1.0, dist, s, s0, sline[imin + 1]
        )

    return s, math.copysign(math.sqrt(dist), sgn)


def _project_one_xy_point_beyond_segment(
    xyp: numpy.ndarray, p0: numpy.ndarray, p1: numpy.ndarray, sgn0: float, dist: float
) -> Tuple[float, float]:
    """
    Project a single point onto an extended line segment.

    A point xyp is projected on the extension of the line segment between points p0 and
    point p1 beyond point p0. The distance dist is set to 1e20 if the point xyp projects
    "far" beyond point p0.

    Arguments
    ---------
    xyp : numpy.ndarray
        Array containing the x and y coordinate of a point.
    p0 : numpy.ndarray
        Array containing the x,y data of segment point 0.
    p1 : numpy.ndarray
        Array containing the x,y data of segment point 1.
    sgn0 : float
        Orientation of the segment.
    dist : float
        Reference distance.

    Results
    -------
    dist : float
        The distance from the line (always positive).
    sgn : float
        The direction from the line (- for left, + for right).
    """
    alpha = (
        (p1[0] - p0[0]) * (xyp[0] - p0[0]) + (p1[1] - p0[1]) * (xyp[1] - p0[1])
    ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
    sgn = sgn0 * (
        (p1[0] - p0[0]) * (xyp[1] - p0[1]) - (p1[1] - p0[1]) * (xyp[0] - p0[0])
    )
    # if the closest point is before the segment ...
    if alpha < 0:
        dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
            xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
        ) ** 2
        dist2end = dist - dist2link
        if dist2end > 100:
            dist = 1e20

    return dist, sgn


def _project_one_xy_point_onto_segment(
    xyp: numpy.ndarray,
    p0: numpy.ndarray,
    p1: numpy.ndarray,
    sgn0: float,
    dist: float,
    s: float,
    s0: float,
    s1: float,
) -> Tuple[float, float, float]:
    """
    Project a single point onto a line segment.

    A point xyp is projected on the line segment between points p0 and point p1.
    The distance dist between point and the path distance along the line are updated if
    the point projects onto the line segment.

    Arguments
    ---------
    xyp : numpy.ndarray
        Array containing the x and y coordinate of a point.
    p0 : numpy.ndarray
        Array containing the x,y data of segment point 0.
    p1 : numpy.ndarray
        Array containing the x,y data of segment point 1.
    sgn0 : float
        Orientation of the segment.
    dist : float
        Reference distance.
    s : float
        Reference path distance along line.
    s0 : float
        Path distance along line of segment point 0.
    s1 : float
        Path distance along line of segment point 1.

    Results
    -------
    dist : float
        The distance from the line (always positive).
    sgn : float
        The direction from the line (- for left, + for right).
    dist : float
        The path distance of the projected point.
    """
    alpha = (
        (p1[0] - p0[0]) * (xyp[0] - p0[0]) + (p1[1] - p0[1]) * (xyp[1] - p0[1])
    ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
    sgn = sgn0 * (
        (p1[0] - p0[0]) * (xyp[1] - p0[1]) - (p1[1] - p0[1]) * (xyp[0] - p0[0])
    )
    # if there is a closest point not coinciding with the nodes ...
    if alpha > 0 and alpha < 1:
        dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
            xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
        ) ** 2
        # if it's actually closer than the node ...
        if dist2link < dist:
            # update the closest point information
            dist = dist2link
            s = s0 + alpha * (s1 - s0)

    return dist, sgn, s
