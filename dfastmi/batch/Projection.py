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

import dfastmi.batch.Distance
import dfastmi.batch.Face

import numpy
import math
from typing import Tuple

def project_xy_point_onto_line(xf: numpy.ndarray, yf: numpy.ndarray, xyline: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
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
    xyf = numpy.concatenate([xf.reshape((nf,1)),yf.reshape((nf,1))], axis=1)

    # pre-allocate the output arrays
    sf = numpy.zeros(nf)
    df = numpy.zeros(nf)

    # compute distance coordinate along the line
    sline = dfastmi.batch.Distance.distance_along_line(xyline)

    # get an array with only the x,y coordinates of xyline
    last_node = xyline.shape[0] - 1

    # initialize sgn for the exceptional case of xyline containing just one node.
    sgn = 1

    # for each point xyp = xyf[i] ...
    for i,xyp in enumerate(xyf):
        # find the node on xyline closest to xyp
        imin = numpy.argmin(((xyp - xyline) ** 2).sum(axis=1))
        p0 = xyline[imin]

        # determine the distance between that node and xyp
        dist2 = ((xyp - p0) ** 2).sum()

        # distance value of that node
        s = sline[imin]

        if imin == 0:
            # we got the first node
            # check if xyp projects much before the first line segment.
            p1 = xyline[imin + 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p1[0] - p0[0]) * (xyp[1] - p0[1])
                - (p1[1] - p0[1]) * (xyp[0] - p0[0]))
            # if the closest point is before the segment ...
            if alpha < 0:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                dist2end = dist2 - dist2link
                if dist2end > 100:
                    dist2 = 1e20

        else:
            # we didn't get the first node
            # project xyp onto the line segment before this node
            p1 = xyline[imin - 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p0[0] - p1[0]) * (xyp[1] - p0[1])
                - (p0[1] - p1[1]) * (xyp[0] - p0[0]))
            # if there is a closest point not coinciding with the nodes ...
            if alpha > 0 and alpha < 1:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                # if it's actually closer than the node ...
                if dist2link < dist2:
                    # update the closest point information
                    dist2 = dist2link
                    s = sline[imin] + alpha * (sline[imin - 1] - sline[imin])

        if imin == last_node:
            # we got the last node
            # check if xyp projects much beyond the last line segment.
            p1 = xyline[imin - 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p0[0] - p1[0]) * (xyp[1] - p0[1])
                - (p0[1] - p1[1]) * (xyp[0] - p0[0]))
            # if the closest point is before the segment ...
            if alpha < 0:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                dist2end = dist2 - dist2link
                if dist2end > 100:
                    dist2 = 1e20

        else:
            # we didn't get the last node
            # project rp onto the line segment after this node
            p1 = xyline[imin + 1]
            alpha = (
                (p1[0] - p0[0]) * (xyp[0] - p0[0])
                + (p1[1] - p0[1]) * (xyp[1] - p0[1])
            ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            sgn = ((p1[0] - p0[0]) * (xyp[1] - p0[1])
                - (p1[1] - p0[1]) * (xyp[0] - p0[0]))
            # if there is a closest point not coinciding with the nodes ...
            if alpha > 0 and alpha < 1:
                dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                    xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                ) ** 2
                # if it's actually closer than the previous value ...
                if dist2link < dist2:
                    # update the closest point information
                    dist2 = dist2link
                    s = sline[imin] + alpha * (
                        sline[imin + 1] - sline[imin]
                    )

        # store the distance values, loop ... and return
        sf[i] = s
        df[i] = math.copysign(math.sqrt(dist2), sgn)

    return sf,df