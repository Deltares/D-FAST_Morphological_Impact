import math
import dfastmi.batch.Distance
import dfastmi.batch.Face
from dfastmi.batch import DetectAndPlot
import numpy
import os
from typing import Dict, Tuple

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
    sbin_min = math.floor(min_s.min()/ds)
    sbin_max = math.ceil(max_s.max()/ds)
    # determin the chainage bins.
    sthresh = numpy.arange(sbin_min, sbin_max+2) * ds

    # determine for each cell in which bin it starts and ends
    min_sbin = numpy.floor(min_s/ds).astype(numpy.int64) - sbin_min
    max_sbin = numpy.floor(max_s/ds).astype(numpy.int64) - sbin_min

    # determine in how many chainage bins a cell is located
    nsbin = max_sbin - min_sbin + 1
    # determine the total number of chainage bin assignments
    nsbin_tot = nsbin.sum()

    # determine per cell a mapping from cell iface to the chainage bin sbin,
    # and determine which fraction of the chainage length associated with the
    # cell is mapped to this particular chainage bin
    siface = numpy.zeros(nsbin_tot, dtype=numpy.int64)
    afrac = numpy.zeros(nsbin_tot)
    sbin  = numpy.zeros(nsbin_tot, dtype=numpy.int64)
    nfaces = len(min_s)
    j = 0
    for i in range(nfaces):
        s0 = min_s[i]
        s1 = max_s[i]
        # skip cells that project onto one point (typically they are located outside the length of the line)
        if s0 == s1:
            continue
        wght = 1 / (s1 - s0)
        for ib in range(min_sbin[i], max_sbin[i]+1):
            siface[j] = i
            afrac[j] = wght * (min(sthresh[ib+1], s1) - max(sthresh[ib], s0))
            sbin[j] = ib
            j = j + 1

    # make sure that sthresh is not longer than necessary
    maxbin = sbin.max()
    if maxbin+2 < len(sthresh):
        sthresh = sthresh[:maxbin+2]

    return siface, afrac, sbin, sthresh

def width_bins(df: numpy.ndarray, nwidth: float, nbins: int) -> Tuple[numpy.ndarray, numpy.ndarray]:
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
    binwidth = nwidth/nbins
    wthresh = -nwidth/2 + binwidth * numpy.arange(nbins+1)

    for i in range(1,nbins):
        idx = df > wthresh[i]
        jbin[idx] = i

    return jbin, wthresh

def xynode_2_area(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    """
    Compute the surface area of all cells.

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the nodes [m].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the nodes [m].
    FNC : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.

    Returns
    -------
    area : numpy.ndarray
        Array of length M containing the grid cell area [m2].
    """
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int64) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)
    nfaces = FNC.shape[0]
    area = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = FNC[i]
        nni = nnodes[i]
        xni = xn[fni][0:nni]
        yni = yn[fni][0:nni]
        areai = 0.0
        for j in range(1,nni-1):
            areai += (xni[j] - xni[0]) * (yni[j+1] - yni[j]) - (xni[j+1] - xni[j]) * (yni[j] - yni[0])
        area[i] = abs(areai)/2

    return area

def min_max_s(s, FNC):
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int64) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)
    nfaces = FNC.shape[0]
    min_s = numpy.zeros((nfaces,))
    max_s = numpy.zeros((nfaces,))
    for i in range(nfaces):
        fni = FNC[i]
        nni = nnodes[i]
        sni = s[fni][0:nni]
        min_s[i] = sni.min()
        max_s[i] = sni.max() # may need to check if max > min to avoid problems later ...

    return min_s, max_s

def comp_sedimentation_volume(
    xni: numpy.ndarray,
    yni: numpy.ndarray,
    sni: numpy.ndarray,
    dni: numpy.ndarray,
    FNCi: numpy.ndarray,
    dzgemi: numpy.ndarray,
    slength: float,
    nwidth: float,
    xykline: numpy.ndarray,
    simfile: str,
    outputdir: str,
    plotops: Dict,
) -> float:
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
    outputdir : str
        Name of output directory.
    Returns
    -------
    dvol : float
        Dredging volume [m3].
    """
    dzmin = 0.01
    nwbins = 10
    sbin_length = 10.0

    areai = xynode_2_area(xni, yni, FNCi)

    print("bin cells in across-stream direction")
    # determine the mean normal distance dfi per cell
    dfi = dfastmi.batch.Face.face_mean(dni, FNCi)
    # distribute the cells over nwbins bins over the channel width
    wbini, wthresh = width_bins(dfi, nwidth, nwbins)
    print("bin cells in along-stream direction")
    # determine the minimum and maximum along line distance of each cell
    min_sfi, max_sfi = min_max_s(sni, FNCi)
    # determine the weighted mapping of cells to chainage bins
    siface, afrac, sbin, sthresh = stream_bins(min_sfi, max_sfi, sbin_length)
    wbin = wbini[siface]
    print("determine chainage per bin")
    # determine chainage values of at the midpoints
    smid = (sthresh[1:] + sthresh[:-1])/2
    sline = dfastmi.batch.Distance.distance_along_line(xykline[:,:2])
    kmid = dfastmi.batch.Distance.distance_to_chainage(sline, xykline[:,2], smid)
    n_sbin = sbin.max()+1

    EFCi = dfastmi.batch.Face.facenode_to_edgeface(FNCi)
    wght_area_tot = numpy.zeros(dzgemi.shape)
    wbin_labels = ["between {w1} and {w2} m".format(w1 = wthresh[iw], w2 = wthresh[iw+1]) for iw in range(nwbins)]
    plot_n = 3
    
    print("-- detecting separate sedimentation areas")
    xyzfil = outputdir + os.sep + "sedimentation_volumes.xyz"
    area_str = "sedimentation area {}"
    total_str = "total sedimentation volume"
    sedarea, sedvol, sed_area_list, wght_area_tot = DetectAndPlot.detect_and_plot_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, slength, plotops, xyzfil, area_str, total_str, True, plot_n)
    
    print("-- detecting separate erosion areas")
    xyzfil = ""
    area_str = "erosion area {}"
    total_str = "total erosion volume"
    eroarea, erovol, ero_area_list, wght_area_tot = DetectAndPlot.detect_and_plot_areas(-dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, slength, plotops, xyzfil, area_str, total_str, False, plot_n)
    return sedarea, sedvol, sed_area_list, eroarea, erovol, ero_area_list, wght_area_tot, wbini