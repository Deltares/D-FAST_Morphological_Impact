from typing import List
import numpy
import os
from dfastmi.plotting import plot_sedimentation, zoom_x_and_save, savefig


def report_areas(dzgemi, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, plotops, xyzfil, area_str, total_str, pos_up, plot_n, sbin_length, volume, sub_area_list):
    binvol = comp_binned_volumes(numpy.maximum( dzgemi, 0.0), areai, wbin, siface, afrac, sbin, wthresh, sthresh)

    write_xyz_file(wbin_labels, kmid, xyzfil, binvol)

    plot_data(dzgemi, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, plotops, area_str, total_str, pos_up, plot_n, sbin_length, volume, sub_area_list, binvol)

def write_xyz_file(wbin_labels, kmid, xyzfil, binvol):
    if xyzfil != "":
        # write a table of chainage and volume per width bin to file
        binvol2 = numpy.stack(binvol)
        with open(xyzfil, "w") as file:
            vol_str = " ".join('"{}"'.format(str) for str in wbin_labels)
            file.write('"chainage" ' + vol_str + "\n")
            for i in range(binvol2.shape[1]):
                vol_str = " ".join("{:8.2f}".format(j) for j in binvol2[:,i])
                file.write("{:8.2f} ".format(kmid[i]) + vol_str + "\n")
    
def plot_data(dzgemi, areai, wbin, wbin_labels, wthresh, siface, afrac, sbin, sthresh, kmid, plotops, area_str, total_str, pos_up, plot_n, sbin_length, volume, sub_area_list, binvol):
    if plotops['plotting']:
        fig, ax = plot_sedimentation(
            kmid,
            "chainage [km]",
            binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            total_str,
            wbin_labels,
            positive_up = pos_up,
        )

        figure_base_name = total_str.replace(" ","_")
        save_figure(plotops, fig, ax, figure_base_name)

        if plot_n > 0:
            # plot the figures with details for the N areas with largest volumes
            volume_mean = volume[1:,:].mean(axis=0)
            sorted_list = numpy.argsort(volume_mean)[::-1]
            if len(sorted_list) <= plot_n:
                vol_thresh = 0.0
            else:
                vol_thresh = volume_mean[sorted_list[plot_n]]
            plot_certain_areas(volume_mean > vol_thresh,  dzgemi, sub_area_list, areai, wbin, wbin_labels, siface, afrac, sbin, wthresh, sthresh, kmid, area_str, pos_up, plotops)

def save_figure(plotops, figure, axes, figure_base_name):
    if plotops['saveplot']:
            figbase = plotops['figdir'] + os.sep + figure_base_name
            if plotops['saveplot_zoomed']:
                zoom_x_and_save(figure, axes, figbase, plotops['plot_ext'], plotops['kmzoom'])
            figfile = figbase + plotops['plot_ext']
            savefig(figure, figfile)     

def plot_certain_areas(condition, dzgemi, area_list, areai, wbin, wbin_labels, siface, afrac, sbin, wthresh, sthresh, kmid, area_str, pos_up, plotops):
    indices = numpy.where(condition)[0]
    sbin_length = sthresh[1] - sthresh[0]
    for ia in indices:
        dzgemi_filtered = dzgemi.copy()
        dzgemi_filtered[numpy.invert(area_list[ia])] = 0.0
        
        area_binvol = comp_binned_volumes(dzgemi_filtered, areai, wbin, siface, afrac, sbin, wthresh, sthresh)
        
        fig, ax = plot_sedimentation(
            kmid,
            "chainage [km]",
            area_binvol,
            "volume [m3] accumulated per {} m bin alongstream".format(sbin_length),
            area_str.format(ia+1),
            wbin_labels,
            positive_up = pos_up,
        )
            
        figure_base_name = area_str.replace(" ","_").format(ia+1) + "_volumes"
        save_figure(plotops, fig, ax, figure_base_name)
        
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