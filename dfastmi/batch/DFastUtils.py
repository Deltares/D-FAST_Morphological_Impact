# -*- coding: utf-8 -*-
"""
Copyright (C) 2024 Stichting Deltares.

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
from typing import List, Tuple
import math
import numpy


def get_zoom_extends(km_min: float, km_max: float, zoom_km_step: float, xykline: numpy.ndarray) -> Tuple[List[Tuple[float, float]],List[Tuple[float, float, float, float]]]:
    """
    Zoom .

    Arguments
    ---------
    km_min : float
        Minimum value for the chainage range of interest.
    km_max : float
        Maximum value for the chainage range of interest.
    zoom_km_step : float
        Preferred chainage length of zoom box.
    xykline : numpy.ndarray 
        Array containing the x,y and chainage data of a line.

    Returns
    -------
    kmzoom : List[Tuple[float, float]]
        Zoom ranges for plots with chainage along x-axis.
    xyzoom : List[Tuple[float, float, float, float]]
        Zoom ranges for xy-plots.
    """

    zoom_km_bin = (km_min, km_max, zoom_km_step)
    zoom_km_bnd = _get_km_bins(zoom_km_bin, type_characteristic_chainage=0, adjust=True)
    eps = 0.1 * zoom_km_step

    kmzoom: List[Tuple[float, float]] = []
    xyzoom: List[Tuple[float, float, float, float]] = []
    for i in range(len(zoom_km_bnd)-1):
        km_min = zoom_km_bnd[i] - eps
        km_max = zoom_km_bnd[i + 1] + eps

        # only append zoom range if there are any chainage points in that range
        # (might be none if there is a chainage discontinuity in the region of
        # interest)
        irange = (xykline[:,2] >= km_min) & (xykline[:,2] <= km_max)
        if any(irange):
            kmzoom.append((km_min, km_max))

            range_crds = xykline[irange, :]
            x = range_crds[:, 0]
            y = range_crds[:, 1]
            xmin = min(x)
            xmax = max(x)
            ymin = min(y)
            ymax = max(y)
            xyzoom.append((xmin, xmax, ymin, ymax))

    return kmzoom, xyzoom

def _get_km_bins(km_bin: Tuple[float, float, float], type_characteristic_chainage: int = 2, adjust: bool = False) -> numpy.ndarray:
    """
    [identical to dfastbe.kernel.get_km_bins]
    Get an array of representative chainage values.

    Arguments
    ---------
    km_bin : Tuple[float, float, float]
        Tuple containing (start, end, step) for the chainage bins
    type_characteristic_chainage : int
        Type of characteristic chainage values returned
            0: all bounds (N+1 values)
            1: lower bounds (N values)
            2: upper bounds (N values) - default
            3: mid points (N values)
    adjust : bool
        Flag indicating whether the step size should be adjusted to include an integer number of steps

    Returns
    -------
    km : numpy.ndarray
        Array containing the chainage bin upper bounds
    """
    km_step = km_bin[2]
    nbins = int(math.ceil((km_bin[1] - km_bin[0]) / km_step))

    lb = 0
    ub = nbins + 1
    dx = 0.0

    if adjust:
        km_step = (km_bin[1] - km_bin[0]) / nbins

    if type_characteristic_chainage == 0:
        # all bounds
        pass
    elif type_characteristic_chainage == 1:
        # lower bounds
        ub = ub - 1
    elif type_characteristic_chainage == 2:
        # upper bounds
        lb = lb + 1
    elif type_characteristic_chainage == 3:
        # midpoint values
        ub = ub - 1
        dx = km_bin[2] / 2

    km = km_bin[0] + dx + numpy.arange(lb, ub) * km_step

    return km
