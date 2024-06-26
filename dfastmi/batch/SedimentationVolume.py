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
from pathlib import Path
from typing import List, Tuple

import numpy

from dfastmi.batch.AreaDetector import AreaData, AreaDetector
from dfastmi.batch.AreaPlotter import ErosionAreaPlotter, SedimentationAreaPlotter
from dfastmi.batch.Distance import distance_along_line, distance_to_chainage
from dfastmi.batch.Face import face_mean, facenode_to_edgeface
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from dfastmi.batch.XyzFileWriter import XyzFileWriter


def stream_bins(min_s, max_s, ds):
    """
    Construct the weighted mapping of cells to chainage bins.

    Arguments
    ---------
    min_s : numpy.ndarray
        Array of length M containing the minimum chainage of a cell [m].
    max_s : numpy.ndarray
        Array of length M containing the maximum chainage of a cell [m].
    ds : float
        Length of chainage bins [m].

    Returns
    -------
    siface : numpy.ndarray
        Array of length N containing the index of the source cell.
    afrac : numpy.ndarray
        Array of length N containing the fraction of the source cell associated with the target chainage bin.
    sbin : numpy.ndarray
        Array of length N containing the index of the target chainage bin.
    sthresh : numpy.ndarray
        Threshold values between the chainage bins [m].
    """
    # determine the minimum and maximum chainage in de data set.
    sbin_min = math.floor(min_s.min() / ds)
    sbin_max = math.ceil(max_s.max() / ds)
    # determin the chainage bins.
    sthresh = numpy.arange(sbin_min, sbin_max + 2) * ds

    # determine for each cell in which bin it starts and ends
    min_sbin = numpy.floor(min_s / ds).astype(numpy.int64) - sbin_min
    max_sbin = numpy.floor(max_s / ds).astype(numpy.int64) - sbin_min

    # determine in how many chainage bins a cell is located
    nsbin = max_sbin - min_sbin + 1
    # determine the total number of chainage bin assignments
    nsbin_tot = nsbin.sum()

    # determine per cell a mapping from cell iface to the chainage bin sbin,
    # and determine which fraction of the chainage length associated with the
    # cell is mapped to this particular chainage bin
    siface = numpy.zeros(nsbin_tot, dtype=numpy.int64)
    afrac = numpy.zeros(nsbin_tot)
    sbin = numpy.zeros(nsbin_tot, dtype=numpy.int64)
    nfaces = len(min_s)
    j = 0
    for i in range(nfaces):
        s0 = min_s[i]
        s1 = max_s[i]
        # skip cells that project onto one point (typically they are located outside the length of the line)
        if s0 == s1:
            continue
        wght = 1 / (s1 - s0)
        for ib in range(min_sbin[i], max_sbin[i] + 1):
            siface[j] = i
            afrac[j] = wght * (min(sthresh[ib + 1], s1) - max(sthresh[ib], s0))
            sbin[j] = ib
            j = j + 1

    # make sure that sthresh is not longer than necessary
    maxbin = sbin.max()
    if maxbin + 2 < len(sthresh):
        sthresh = sthresh[: maxbin + 2]

    return siface, afrac, sbin, sthresh


def width_bins(
    df: numpy.ndarray, nwidth: float, nbins: int
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Distribute the points over sample bins based on distance from centreline.

    Arguments
    ---------
    df : numpy.ndarray
        Array containing per point the signed distance from the centreline [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].
    nbins : int
        Number of bins over the normal width.

    Returns
    -------
    jbin : numpy.ndarray
        Bin index of each point (integers in the range 0 to nbins-1).
    wthresh : numpy.ndarray
        Signed distance threshold values between the bins [m].
        This array contains nbins+1 values.
    """
    jbin = numpy.zeros(df.shape, dtype=numpy.int64)
    binwidth = nwidth / nbins
    wthresh = -nwidth / 2 + binwidth * numpy.arange(nbins + 1)

    for i in range(1, nbins):
        idx = df > wthresh[i]
        jbin[idx] = i

    return jbin, wthresh


def xynode_2_area(
    xn: numpy.ndarray, yn: numpy.ndarray, face_node_connectivity: numpy.ndarray
) -> numpy.ndarray:
    """
    Compute the surface area of all cells.

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the nodes [m].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the nodes [m].
    face_node_connectivity : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.

    Returns
    -------
    area : numpy.ndarray
        Array of length M containing the grid cell area [m2].
    """
    if face_node_connectivity.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = (
            numpy.ones(face_node_connectivity.data.shape[0], dtype=numpy.int64)
            * face_node_connectivity.data.shape[1]
        )
    else:
        # varying number of nodes
        nnodes = face_node_connectivity.mask.shape[1] - face_node_connectivity.mask.sum(
            axis=1
        )
    nfaces = face_node_connectivity.shape[0]
    area = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = face_node_connectivity[i]
        nni = nnodes[i]
        xni = xn[fni][0:nni]
        yni = yn[fni][0:nni]
        areai = 0.0
        for j in range(1, nni - 1):
            areai += (xni[j] - xni[0]) * (yni[j + 1] - yni[j]) - (
                xni[j + 1] - xni[j]
            ) * (yni[j] - yni[0])
        area[i] = abs(areai) / 2

    return area


def min_max_s(s, face_node_connectivity):
    if face_node_connectivity.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = (
            numpy.ones(face_node_connectivity.data.shape[0], dtype=numpy.int64)
            * face_node_connectivity.data.shape[1]
        )
    else:
        # varying number of nodes
        nnodes = face_node_connectivity.mask.shape[1] - face_node_connectivity.mask.sum(
            axis=1
        )
    nfaces = face_node_connectivity.shape[0]
    min_s = numpy.zeros((nfaces,))
    max_s = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = face_node_connectivity[i]
        nni = nnodes[i]
        sni = s[fni][0:nni]
        min_s[i] = sni.min()
        max_s[i] = (
            sni.max()
        )  # may need to check if max > min to avoid problems later ...

    return min_s, max_s


def _comp_binned_volumes(
    dzgem: numpy.ndarray,
    area: numpy.ndarray,
    wbin: numpy.ndarray,
    siface: numpy.ndarray,
    afrac: numpy.ndarray,
    sbin: numpy.ndarray,
    wthresh: numpy.ndarray,
    sthresh: numpy.ndarray,
) -> List[numpy.ndarray]:
    """
    Determine the volume per streamwise bin and width bin.

    Arguments
    ---------
    dzgem : numpy.ndarray
        Array of length M containing the bed level change per cell [m].
    area : numpy.ndarray
        Array of length M containing the grid cell area [m2].
    wbin: numpy.ndarray
        Array of length N containing the index of the target width bin [-].
    siface : numpy.ndarray
        Array of length N containing the index of the source cell (range 0 to M-1) [-].
    afrac : numpy.ndarray
        Array of length N containing the fraction of the source cell associated with the target chainage bin [-].
    sbin : numpy.ndarray
        Array of length N containing the index of the target chainage bin [-].
    wthresh : numpy.ndarray
        Array containing the cross-stream coordinate boundaries between the width bins [m].
    sthresh : numpy.ndarray
        Array containing the along-stream coordinate boundaries between the streamwise bins [m].

    Returns
    -------
    binvol : List[numpy.ndarray]
        List of arrays containing the total volume per streamwise bin [m3]. List length corresponds to number of width bins.
    """

    dvol = dzgem * area

    n_wbin = len(wthresh) - 1
    n_sbin = len(sthresh) - 1
    sedbinvol: List[numpy.ndarray] = []

    # compute for every width bin the sedimentation volume
    for iw in range(n_wbin):
        lw = wbin == iw

        sbin_lw = sbin[lw]
        dvol_lw = dvol[siface[lw]]
        afrac_lw = afrac[lw]

        sedbinvol.append(
            numpy.bincount(sbin_lw, weights=dvol_lw * afrac_lw, minlength=n_sbin)
        )

    return sedbinvol


def comp_sedimentation_volume(
    xykm_data: XykmData,
    dzgemi: numpy.ndarray,
    slength: float,
    nwidth: float,
    outputdir: Path,
    plotting_options: PlotOptions,
):
    """
    Compute the yearly dredging volume.
    Arguments
    ---------
    dzgem : numpy.ndarray
        Yearly mean bed level change [m].
    slength : float
        The expected yearly impacted sedimentation length [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].
    xykline : numpy.ndarray
        Array containing the x,y and chainage data of a line.
    simfile : str
        Name of simulation file.
    outputdir : Path
        Path of output directory.
    plotting_options : PlotOptions
        Class containing the plot options.
    Returns
    -------
    dvol : float
        Dredging volume [m3].
    """
    dzmin = 0.01
    nwbins = 10
    sbin_length = 10.0

    areai = xynode_2_area(
        xykm_data.xni, xykm_data.yni, xykm_data.face_node_connectivity_index
    )

    print("bin cells in across-stream direction")
    # determine the mean normal distance dfi per cell
    dfi = face_mean(xykm_data.nni, xykm_data.face_node_connectivity_index)
    # distribute the cells over nwbins bins over the channel width
    wbini, wthresh = width_bins(dfi, nwidth, nwbins)
    print("bin cells in along-stream direction")
    # determine the minimum and maximum along line distance of each cell
    min_sfi, max_sfi = min_max_s(xykm_data.sni, xykm_data.face_node_connectivity_index)
    # determine the weighted mapping of cells to chainage bins
    siface, afrac, sbin, sthresh = stream_bins(min_sfi, max_sfi, sbin_length)
    wbin = wbini[siface]
    print("determine chainage per bin")
    # determine chainage values of at the midpoints
    smid = (sthresh[1:] + sthresh[:-1]) / 2
    sline = distance_along_line(xykm_data.xykline[:, :2])
    kmid = distance_to_chainage(sline, xykm_data.xykline[:, 2], smid)

    edgeface_index = facenode_to_edgeface(xykm_data.face_node_connectivity_index)
    wbin_labels = [
        "between {w1} and {w2} m".format(w1=wthresh[iw], w2=wthresh[iw + 1])
        for iw in range(nwbins)
    ]
    plot_n = 3

    print("-- detecting separate sedimentation areas")
    sedimentation_area_detector = AreaDetector()
    sedimentation_area_data: AreaData = sedimentation_area_detector.detect_areas(
        dzgemi,
        dzmin,
        edgeface_index,
        areai,
        wbin,
        wthresh,
        siface,
        afrac,
        sbin,
        sthresh,
        slength,
    )

    sedimentation_binvol = _comp_binned_volumes(
        numpy.maximum(dzgemi, 0.0),
        areai,
        wbin,
        siface,
        afrac,
        sbin,
        wthresh,
        sthresh,
    )

    xyz_file_location = outputdir.joinpath("sedimentation_volumes.xyz")
    XyzFileWriter.write_xyz_file(
        wbin_labels, kmid, sedimentation_binvol, xyz_file_location
    )

    sedimentation_area_plotter = SedimentationAreaPlotter(
        plotting_options, plot_n, sedimentation_area_data
    )
    sedimentation_area_plotter.plot_areas(
        dzgemi,
        areai,
        wbin,
        wbin_labels,
        wthresh,
        siface,
        afrac,
        sbin,
        sthresh,
        kmid,
        sedimentation_binvol,
    )

    print("-- detecting separate erosion areas")
    erosion_area_detector = AreaDetector()
    erosion_area_data: AreaData = erosion_area_detector.detect_areas(
        -dzgemi,
        dzmin,
        edgeface_index,
        areai,
        wbin,
        wthresh,
        siface,
        afrac,
        sbin,
        sthresh,
        slength,
    )

    erosion_binvol = _comp_binned_volumes(
        numpy.maximum(-dzgemi, 0.0),
        areai,
        wbin,
        siface,
        afrac,
        sbin,
        wthresh,
        sthresh,
    )

    erosion_area_plotter = ErosionAreaPlotter(
        plotting_options, plot_n, erosion_area_data
    )
    erosion_area_plotter.plot_areas(
        -dzgemi,
        areai,
        wbin,
        wbin_labels,
        wthresh,
        siface,
        afrac,
        sbin,
        sthresh,
        kmid,
        erosion_binvol,
    )

    return SedimentationData(
        sedimentation_area_data.area,
        sedimentation_area_data.volume,
        sedimentation_area_data.area_list,
        erosion_area_data.area,
        erosion_area_data.volume,
        erosion_area_data.area_list,
        sedimentation_area_data.total_area_weight + erosion_area_data.total_area_weight,
        wbini,
    )
