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

from typing import List, Tuple

import os
import numpy
from dfastmi.batch.PlotOptions import PlotOptions
import dfastmi.kernel.core
import dfastmi.plotting

def detect_and_plot_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, slength, plotting_options : PlotOptions, xyzfil, area_str, total_str, pos_up, plot_n):
    sbin_length = sthresh[1] - sthresh[0]

    area, volume, sub_area_list, wght_area_tot = detect_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wthresh, siface, afrac, sbin, sthresh, slength)

    binvol = comp_binned_volumes(numpy.maximum( dzgemi, 0.0), areai, wbin, siface, afrac, sbin, wthresh, sthresh)
    
    if xyzfil != "":
        # write a table of chainage and volume per width bin to file
        binvol2 = numpy.stack(binvol)
        with open(xyzfil, "w") as file:
            vol_str = " ".join('"{}"'.format(str) for str in wbin_labels)
            file.write('"chainage" ' + vol_str + "\n")
            for i in range(binvol2.shape[1]):
                vol_str = " ".join("{:8.2f}".format(j) for j in binvol2[:,i])
                file.write("{:8.2f} ".format(kmid[i]) + vol_str + "\n")

    if plotting_options.plotting:
        fig, ax = dfastmi.plotting.plot_sedimentation(
            kmid,
            "chainage [km]",
            binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            total_str,
            wbin_labels,
            positive_up = pos_up,
        )

        if plotting_options.saveplot:
            figbase = plotting_options.figure_save_directory + os.sep + total_str.replace(" ","_")
            if plotting_options.saveplot_zoomed:
                dfastmi.plotting.zoom_x_and_save(fig, ax, figbase, plotting_options.plot_extension, plotting_options.kmzoom)
            figfile = figbase + plotting_options.plot_extension
            dfastmi.plotting.savefig(fig, figfile)

        if plot_n > 0:
            # plot the figures with details for the N areas with largest volumes
            volume_mean = volume[1:,:].mean(axis=0)
            sorted_list = numpy.argsort(volume_mean)[::-1]
            if len(sorted_list) <= plot_n:
                vol_thresh = 0.0
            else:
                vol_thresh = volume_mean[sorted_list[plot_n]]
            plot_certain_areas(volume_mean > vol_thresh,  dzgemi, sub_area_list, areai, wbin, wbin_labels, siface, afrac, sbin, wthresh, sthresh, kmid, area_str, pos_up, plotting_options)
    
    return area, volume, sub_area_list, wght_area_tot

def detect_areas(dzgemi, dzmin, EFCi, wght_area_tot, areai, wbin, wthresh, siface, afrac, sbin, sthresh, slength):
    sbin_length = sthresh[1] - sthresh[0]
    nwidth = wthresh[-1] - wthresh[0]
    sub_areai, n_sub_areas = detect_connected_regions(dzgemi > dzmin, EFCi)
    print("number of areas detected: ", n_sub_areas)

    area  = numpy.zeros(n_sub_areas)
    volume = numpy.zeros((3,n_sub_areas))
    sub_area_list = []
    
    for ia in range(n_sub_areas):
        dzgemi_filtered = dzgemi.copy()
        dzgemi_filtered[sub_areai != ia] = 0.0
        sub_area_list.append(sub_areai == ia)
        
        #ApplicationSettingsHelper.log_text("sed_vol",dict = {"ia": ia+1, "nr": 1})
        volume[1,ia], wght_area_ia = comp_sedimentation_volume1(dzgemi_filtered, dzmin, areai, wbin, siface, afrac, sbin, wthresh, sthresh, slength, sbin_length)
        wght_area_tot = wght_area_tot + wght_area_ia
        
        #ApplicationSettingsHelper.log_text("sed_vol",dict = {"ia": ia+1, "nr": 2})
        volume[2,ia], area[ia], volume[0,ia] = comp_sedimentation_volume2(numpy.maximum(dzgemi_filtered,0.0), dzmin, areai, slength, nwidth)
    
    sorted_list = numpy.argsort(area)[::-1]
    area = area[sorted_list]
    volume = volume[:,sorted_list]
    sub_area_list = [sub_area_list[ia] for ia in sorted_list]
    
    return area, volume, sub_area_list, wght_area_tot

def plot_certain_areas(condition, dzgemi, area_list, areai, wbin, wbin_labels, siface, afrac, sbin, wthresh, sthresh, kmid, area_str, pos_up, plotting_options : PlotOptions):
    indices = numpy.where(condition)[0]
    sbin_length = sthresh[1] - sthresh[0]
    for ia in indices:
        dzgemi_filtered = dzgemi.copy()
        dzgemi_filtered[numpy.invert(area_list[ia])] = 0.0
        
        area_binvol = comp_binned_volumes(dzgemi_filtered, areai, wbin, siface, afrac, sbin, wthresh, sthresh)
        
        fig, ax = dfastmi.plotting.plot_sedimentation(
            kmid,
            "chainage [km]",
            area_binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            area_str.format(ia+1),
            wbin_labels,
            positive_up = pos_up,
        )
        
        if plotting_options.saveplot:
            figbase = plotting_options.figure_save_directory + os.sep + area_str.replace(" ","_").format(ia+1) + "_volumes"
            if plotting_options.saveplot_zoomed:
                dfastmi.plotting.zoom_x_and_save(fig, ax, figbase, plotting_options.plot_extension, plotting_options.kmzoom)
            figfile = figbase + plotting_options.plot_extension
            dfastmi.plotting.savefig(fig, figfile)
        
def comp_binned_volumes(
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
    
    n_wbin = len(wthresh)-1
    n_sbin = len(sthresh)-1
    sedbinvol : List[numpy.ndarray] = []
    
    # compute for every width bin the sedimentation volume
    for iw in range(n_wbin):
        lw = wbin == iw

        sbin_lw = sbin[lw]
        dvol_lw = dvol[siface[lw]]
        afrac_lw = afrac[lw]
    
        sedbinvol.append(numpy.bincount(sbin_lw, weights = dvol_lw * afrac_lw, minlength = n_sbin))
        
    return sedbinvol
    
def comp_sedimentation_volume1(
    dzgem: numpy.ndarray,
    dzmin: float,
    area: numpy.ndarray,
    wbin: numpy.ndarray,
    siface: numpy.ndarray,
    afrac: numpy.ndarray,
    sbin: numpy.ndarray,
    wthresh: numpy.ndarray,
    sthresh: numpy.ndarray,
    slength: float,
    sbin_length: float,
) -> float:
    """
    Compute the initial year sedimentation volume.
    Algorithm 1.

    Arguments
    ---------
    dzgem : numpy.ndarray
        Array of length M containing the yearly mean bed level change per cell [m].
    dzmin : float
        Bed level changes (per cell) less than this threshold value are ignored [m].
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
    slength : float
        The expected yearly impacted sedimentation length [m].
    sbin_length : float
        Size of bins in streamwise direction [m].

    Returns
    -------
    dvol : float
        Sedimentation volume [m3].
    """    
    
    dzgem_filtered = dzgem.copy()
    dzgem_filtered[abs(dzgem) < dzmin] = 0.0
    dvol = dzgem_filtered * area
    
    n_wbin = len(wthresh)-1
    n_sbin = len(sthresh)-1
    n_faces = len(dvol)
    tot_dredge_vol = 0
    wght_all_dredge = numpy.zeros(dvol.shape)
    
    # compute for every width bin the sedimentation volume
    for iw in range(n_wbin):
        lw = wbin == iw
        
        tot_dredge_vol_wbin, wght_all_dredge_bin = comp_sedimentation_volume1_one_width_bin(dvol[siface[lw]], sbin[lw], afrac[lw], siface[lw], sthresh, sbin_length, slength)
        
        #print("width bin {}, total volume {:.6f} m3".format(iw+1, tot_dredge_vol_wbin))
        tot_dredge_vol = tot_dredge_vol + tot_dredge_vol_wbin
        wght_all_dredge = wght_all_dredge + numpy.bincount(siface[lw], weights = wght_all_dredge_bin, minlength = n_faces)

    #print("-------> total volume {:.6f} m3".format(tot_dredge_vol))

    return tot_dredge_vol, wght_all_dredge

def comp_sedimentation_volume1_one_width_bin(
    dvol: numpy.ndarray,
    sbin: numpy.ndarray,
    afrac: numpy.ndarray,
    siface: numpy.ndarray,
    sthresh: numpy.ndarray,
    sbin_length: float,
    slength: float,
) -> float:
    """
    Compute the initial year sedimentation volume.
    Algorithm 1.

    Arguments
    ---------


    Returns
    -------
    dvol : float
        Sedimentation volume [m3].
    """    
    n_sbin = len(sthresh)-1
    
    check_sed = dvol > 0.0
    dvol_sed = dvol[check_sed]
    sbin_sed = sbin[check_sed]
    siface_sed = siface[check_sed]
    afrac_sed = afrac[check_sed]
    
    tot_dredge_vol, wght_all_dredge_sed = comp_sedimentation_volume1_tot(dvol_sed, sbin_sed, afrac_sed, siface_sed, sthresh, sbin_length, slength)
    
    wght_all_dredge = numpy.zeros(dvol.shape)
    wght_all_dredge[check_sed] = wght_all_dredge_sed

    return tot_dredge_vol, wght_all_dredge
    
def comp_sedimentation_volume1_tot(
    sedvol: numpy.ndarray,
    sbin: numpy.ndarray,
    afrac: numpy.ndarray,
    siface: numpy.ndarray,
    sthresh: numpy.ndarray,
    sbin_length: float,
    slength: float,
) -> float:
    """
    Compute the initial year sedimentation volume.
    Algorithm 1.

    Arguments
    ---------


    Returns
    -------
    dvol : float
        Sedimentation volume [m3].
    sedbinvol : List[Optional[numpy.ndarray]]
        List of arrays containing the total sedimentation volume per streamwise bin [m3]. List length corresponds to number of width bins.
    erobinvol : List[Optional[numpy.ndarray]]
        List of arrays containing the total erosion volume per streamwise bin [m3]. List length corresponds to number of width bins.
    """    
    index = numpy.argsort(sbin)

    dredge_vol = 0.0
    wght = numpy.zeros(siface.shape)

    if len(index) > 0:
        ibprev = -999
        s0 = sthresh[sbin[index[0]]]
        slength1 = slength
        for i in range(len(index)):
            ii = index[i]
            ib = sbin[ii]
            if ib == ibprev: # same index, same weight
                pass

            else: # next index
                s0 = sthresh[ib]
                frac = max(0.0, min(slength1/sbin_length, 1.0))
                ibprev = ib
                slength1 = slength1 - sbin_length
        
            if frac != 0.0:
                wght[ii] = wght[ii] + frac * afrac[ii]
                dredge_vol = dredge_vol + frac * sedvol[ii] * afrac[ii]
                #print(siface[ii], frac, sedvol[ii], afrac[ii], frac * sedvol[ii] * afrac[ii],' -> ',dredge_vol)
        
    #print(dredge_vol, ' > ', wght)

    return dredge_vol, wght

def comp_sedimentation_volume2(
    dzgem: numpy.ndarray,
    dzmin: float,
    area: numpy.ndarray,
    slength: float,
    nwidth: float,
) -> float:
    """
    Compute the initial year sedimentation volume.
    Algorithm 2.

    Arguments
    ---------
    dzgem : numpy.ndarray
        Array of length M containing the yearly mean bed level change per cell [m].
    dzmin : float
        Bed level changes (per cell) less than this threshold value are ignored [m].
    area : numpy.ndarray
        Array of length M containing the grid cell area [m2].
    slength : float
        The expected yearly impacted sedimentation length [m].
    nwidth : float
        Normal river width (from rivers configuration file) [m].

    Returns
    -------
    dvol : float
        Sedimentation volume [m3].
    """
    iface = numpy.where(dzgem > dzmin)
    dzgem_clip = dzgem[iface]
    area_clip = area[iface]
    
    dvol_eq = (dzgem_clip * area_clip).sum()
    area_eq = area_clip.sum()
    dz_eq = dvol_eq / area_eq
    area_1y = slength * nwidth
    if area_eq < area_1y:
        dvol = dvol_eq
    else:
        dvol = dz_eq * area_1y
    
    print(dzmin)
    #print("dz_min = {:.6f} m, dz_max = {:.6f} m, dz_thresh = {:.6f} m".format(min(dzgem), max(dzgem), dzmin))
    print("dz_mean = {:.6f} m, width = {:.6f} m, length = {:.6f} m, volume = {:.6f} m3".format(dz_eq, nwidth, slength, dvol))
    return dvol, area_eq, dvol_eq

def detect_connected_regions(fcondition: numpy.ndarray, EFC: numpy.ndarray) -> Tuple[numpy.ndarray, int]:
    """
    Detect regions of faces for which the fcondition equals True.
    
    Arguments
    ---------
    fcondition : numpy.ndarray
        Boolean array of length M: one boolean per face.
    EFC : numpy.ndarray
        N x 2 array containing the indices of neighbouring faces.
        Maximum face index is M-1.
    
    Returns
    -------
    partition : numpy.ndarray
        Integer array of length M: for all faces at which fcondition is True, the integer indicates the region that the face assigned to.
        Contains -1 for faces at which fcondition is False.
    nregions : int
        Number of regions detected.
    """
    partition = -numpy.ones(fcondition.shape[0], dtype=numpy.int64)
    #print('Total number of cells ', fcondition.shape[0])
    
    ncells = fcondition.sum()
    partition[fcondition] = numpy.arange(ncells)
    #print('Total number of flagged cells ', ncells)
    
    efc = EFC[fcondition[EFC].all(axis=1),:]
    nlinks = efc.shape[0]
    #print('Total number of internal flow links ', nlinks)
    
    anychange = True
    while anychange:
        partEFC = partition[efc]
        anychange = False

        for j in range(nlinks):
            m = partition[efc[j]].min()
            if not (partition[efc[j]] == m).all():
                anychange = True
                partition[efc[j]] = m
    
    parts, ipart = numpy.unique(partition, return_inverse=True)
    ipart = ipart-1
    
    return ipart, len(parts)-1
