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
This file is part of D-FAST Bank Erosion: https://github.com/Deltares/D-FAST_Bank_Erosion
"""

from typing import List, Optional, Tuple, Union

import matplotlib
import matplotlib.pyplot
import numpy


def savefig(fig: matplotlib.figure.Figure, filename: str) -> None:
    """
    Save a single figure to file.

    Arguments
    ---------
    fig : matplotlib.figure.Figure
        Figure to a be saved.
    filename : str
        Name of the file to be written.
    """
    print("saving figure {file}".format(file=filename))
    matplotlib.pyplot.show(block=False)
    fig.savefig(filename, dpi=300)


def setsize(fig: matplotlib.figure.Figure) -> None:
    """
    Set the size of a figure.

    Currently the size is hardcoded, but functionality may be extended in the
    future.

    Arguments
    ---------
    fig : matplotlib.figure.Figure
        Figure to a be saved.
    """
    fig.set_size_inches(11.75, 8.25)  # a4
    # fig.set_size_inches(16.5, 11.75) # a3


def set_bbox(
    ax: matplotlib.axes.Axes,
    bbox: Tuple[float, float, float, float],
    scale: float = 1000,
) -> None:
    """
    Specify the bounding limits of an axes object.

    Arguments
    ---------
    ax : matplotlib.axes.Axes
        Axes object to be adjusted.
    bbox : Tuple[float, float, float, float]
        Tuple containing boundary limits (xmin, ymin, xmax, ymax); unit m.
    scale: float
        Indicates whether the axes are in m (1) or km (1000).
    """
    ax.set_xlim(xmin=bbox[0] / scale, xmax=bbox[2] / scale)
    ax.set_ylim(ymin=bbox[1] / scale, ymax=bbox[3] / scale)


def chainage_markers(
    xykm: numpy.ndarray, ax: matplotlib.axes.Axes, ndec: int = 1, scale: float = 1000
) -> None:
    """
    Add markers indicating the river chainage to a plot.

    Arguments
    ---------
    xykm : numpy.ndarray
        Array containing the x, y, and chainage; unit m for x and y, km for chainage.
    ax : matplotlib.axes.Axes
        Axes object in which to add the markers.
    ndec : int
        Number of decimals used for marks.
    scale: float
        Indicates whether the axes are in m (1) or km (1000).
    """
    step = 10 ** (-ndec)
    labelstr = " {:." + str(ndec) + "f}"
    km_rescaled = xykm[:, 2] / step
    mask = numpy.isclose(numpy.round(km_rescaled), km_rescaled)
    ax.plot(
        xykm[mask, 0] / scale,
        xykm[mask, 1] / scale,
        linestyle="None",
        marker="+",
        color="k",
    )
    for i in numpy.nonzero(mask)[0]:
        ax.text(
            xykm[i, 0] / scale,
            xykm[i, 1] / scale,
            labelstr.format(xykm[i, 2]),
            fontsize="x-small",
            clip_on=True,
        )


def plot_zoom_boxes(
    xyzoom: List[Tuple[float, float, float, float]],
    ax: matplotlib.axes.Axes,
    scale: float = 1000,
) -> None:
    """
    Add the zoom boxes to a plot.

    Arguments
    ---------
    xyzoom : List[Tuple[float, float, float, float]]
        List of xmin, xmax, ymin, ymax values to zoom into.
    ax : matplotlib.axes.Axes
        Axes object in which to add the mesh.
    scale : float
        Indicates whether the axes are in m (1) or km (1000).
    """
    for bbox in xyzoom:
        x_box = numpy.array((bbox[0], bbox[1], bbox[1], bbox[0], bbox[0]))
        y_box = numpy.array((bbox[2], bbox[2], bbox[3], bbox[3], bbox[2]))
        ax.plot(x_box / scale, y_box / scale, color=(0.0, 0.0, 0.0), linewidth=0.5)


def plot_mesh(
    ax: matplotlib.axes.Axes, xe: numpy.ndarray, ye: numpy.ndarray, scale: float = 1000
) -> None:
    """
    Add a mesh to a plot.

    Arguments
    ---------
    ax : matplotlib.axes.Axes
        Axes object in which to add the mesh.
    xe : numpy.ndarray
        M x 2 array of begin/end x-coordinates of mesh edges.
    ye : numpy.ndarray
        M x 2 array of begin/end y-coordinates of mesh edges.
    scale : float
        Indicates whether the axes are in m (1) or km (1000).
    """
    xe1 = xe[:, (0, 1, 1)] / scale
    xe1[:, 2] = numpy.nan
    xev = xe1.reshape((xe1.size,))

    ye1 = ye[:, (0, 1, 1)] / scale
    ye1[:, 2] = numpy.nan
    yev = ye1.reshape((ye1.size,))

    # to avoid OverflowError: In draw_path: Exceeded cell block limit
    # plot the data in chunks ...
    for i in range(0, len(xev), 3000):
        ax.plot(
            xev[i : i + 3000], yev[i : i + 3000], color=(0.5, 0.5, 0.5), linewidth=0.25
        )


def plot_mesh_patches(
    ax: matplotlib.axes.Axes,
    fn: numpy.ndarray,
    nnodes: numpy.ndarray,
    xn: numpy.ndarray,
    yn: numpy.ndarray,
    val: numpy.ndarray,
    minval: Optional[float] = None,
    maxval: Optional[float] = None,
    scale: float = 1000,
    cmap: Union[str, matplotlib.colors.LinearSegmentedColormap] = "Spectral",
) -> matplotlib.collections.PolyCollection:
    """
    Add a collection of patches to the plot one for every face of the mesh.

    Arguments
    ---------
    ax : matplotlib.axes.Axes
        Axes object in which to add the mesh.
    fn : numpy.ndarray
        N x M array listing the nodes (max M) per face (total N) of the mesh.
    nnodes : numpy.ndarray
        Number of nodes per face (max M).
    xn : numpy.ndarray
        X-coordinates of the mesh nodes.
    yn : numpy.ndarray
        Y-coordinates of the mesh nodes.
    val : numpy.ndarray
        Array of length N containing the value per face.
    minval : Optional[float]
        Lower limit for the color scale.
    maxval : Optional[float]
        Upper limit for the color scale.
    scale : float
        Indicates whether the axes are in m (1) or km (1000).
    cmap : Union[str, matplotlib.colors.LinearSegmentedColormap]
        Colormap or name of colormap.

    Returns
    -------
    p : matplotlib.collections.PolyCollection
        Patches object.
    """
    tfn_list = []
    tval_list = []
    for n in range(3, max(nnodes) + 1):
        mask = nnodes >= n
        fn_masked = fn[mask, :]
        tfn_list.append(fn_masked[:, (0, n - 2, n - 1)])
        tval_list.append(val[mask])
    tfn = numpy.concatenate(tfn_list, axis=0)
    tval = numpy.concatenate(tval_list, axis=0)
    # cmap = matplotlib.pyplot.get_cmap('Spectral')
    if minval is None:
        minval = numpy.min(tval)
    if maxval is None:
        maxval = numpy.max(tval)
    p = ax.tripcolor(
        xn / scale,
        yn / scale,
        tfn,
        facecolors=tval,
        cmap=cmap,
        vmin=minval,
        vmax=maxval,
    )
    return p


def plot_overview(
    bbox: Tuple[float, float, float, float],
    xykm: numpy.ndarray,
    fn: numpy.ndarray,
    nnodes: numpy.ndarray,
    xn: numpy.ndarray,
    yn: numpy.ndarray,
    dzgem: numpy.ndarray,
    xlabel_txt: str,
    ylabel_txt: str,
    title_txt: str,
    dzgem_txt: str,
    xyzoom: List[Tuple[float, float, float, float]],
) -> [matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """
    Create the erosion and sedimentation plot.

    The figure contains a map of the equilibrium erosion and sedimentation and the chainage.

    Arguments
    ---------
    bbox : Tuple[float, float, float, float]
        Tuple containing boundary limits (xmin, ymin, xmax, ymax); unit m.
    xykm : numpy.ndarray
        Array containing the x, y, and chainage; unit m for x and y, km for chainage.
    fn : numpy.ndarray
        N x M array listing the nodes (max M) per face (total N) of the mesh.
    nnodes : numpy.ndarray
        Number of nodes per face (max M).
    xn : numpy.ndarray
        X-coordinates of the mesh nodes.
    yn : numpy.ndarray
        Y-coordinates of the mesh nodes.
    dzgem : numpy.ndarray
        Array of sedimentation and erosion.
    xlabel_txt : str
        Label for the x-axis.
    ylabel_txt : str
        Label for the y-axis.
    title_txt : str
        Label for the axes title.
    dzgem_txt : str
        Label for the color bar.
    xyzoom : List[Tuple[float, float, float, float]]
        List of xmin, xmax, ymin, ymax values to zoom into.

    Returns
    -------
    fig : matplotlib.figure.Figure:
        Figure object.
    ax : matplotlib.axes.Axes
        Axes object.
    """
    fig, ax = matplotlib.pyplot.subplots()
    setsize(fig)
    ax.set_aspect(1)
    #
    colors = ["darkred", "red", "ghostwhite", "lawngreen", "darkgreen"]
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", colors)
    #
    scale = 1000
    if xykm is not None:
        chainage_markers(xykm, ax, ndec=0, scale=scale)
    dzgem_max = abs(dzgem).max()
    dzgem_min = -dzgem_max
    p = plot_mesh_patches(
        ax, fn, nnodes, xn, yn, dzgem, dzgem_min, dzgem_max, scale=scale, cmap=cmap
    )
    cbar = fig.colorbar(p, ax=ax, shrink=0.5, drawedges=False, label=dzgem_txt)
    #
    # plot_zoom_boxes(xyzoom, ax, scale=scale)
    #
    set_bbox(ax, bbox, scale=scale)
    ax.set_xlabel(xlabel_txt)
    ax.set_ylabel(ylabel_txt)
    ax.grid(True)
    ax.set_title(title_txt)
    # ax.legend(handles, labels, loc="upper right")
    return fig, ax


def plot_sedimentation(
    km_mid: numpy.ndarray,
    chainage_txt: str,
    dv: numpy.ndarray,
    ylabel_txt: str,
    title_txt: str,
    wlabels: List[str],
    positive_up: bool = True,
) -> Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]:
    """
    Create the sedimentation volumes plot with total sedimentation volume per width bin.

    Arguments
    ---------
    km_mid : numpy.ndarray
        Array containing the M mid points for the chainage bins.
    chainage_txt : str
        Label for the horizontal chainage axes.
    dv : numpy.ndarray
        Array of size M x N of sedimentation volumes for M chainage bins and N width bins
    ylabel_txt : str
        Label for the vertical erosion volume axes.
    title_txt : str
        Label for axes title.
    wlabels : List[str]
        Labels for the width bins.
    positive_up : bool
        Flag indicating whether the y axis should be positive up (sedimentation) or down (erosion).


    Results
    -------
    fig : matplotlib.figure.Figure
        Figure object.
    ax : matplotlib.axes.Axes
        Axes object.
    """
    fig, ax = matplotlib.pyplot.subplots()
    setsize(fig)
    #
    n_levels = len(dv)
    # clrs = get_colors("Blues", n_levels + 1)
    # matplotlib.pyplot.stackplot(km_mid, *dv, colors = clrs, labels = wlabels)
    matplotlib.pyplot.stackplot(km_mid, *dv, labels=wlabels)
    #
    ax.set_xlabel(chainage_txt)
    ax.set_ylabel(ylabel_txt)
    # ax.set_yscale("log")
    ax.grid(True)
    ax.set_title(title_txt)
    if positive_up:
        ax.legend(loc="upper right")
    else:
        ax.invert_yaxis()
        ax.legend(loc="lower right")
    return fig, ax


def get_colors(cmap_name: str, n: int) -> List[Tuple[float, float, float]]:
    """
    Obtain N colors from the specified colormap.

    Arguments
    ---------
    cmap_name : str
        Name of the color map.
    n : int
        Number of colors to be returned.

    Returns
    -------
    clrcyc : List[Tuple[float, float, float]]
        List of colour tuplets.
    """
    cmap = matplotlib.cm.get_cmap(cmap_name)
    clrs = [cmap(i / (n - 1)) for i in range(n)]
    return clrs


def zoom_x_and_save(
    fig: matplotlib.figure.Figure,
    ax: matplotlib.axes.Axes,
    figbase: str,
    plot_ext: str,
    xzoom: List[Tuple[float, float]],
) -> None:
    """
    Zoom in on subregions of the x-axis and save the figure.

    Arguments
    ---------
    fig : matplotlib.figure.Figure
        Figure to be processed.
    ax : matplotlib.axes.Axes
        Axes to be processed.
    fig_base : str
        Base name of the figure to be saved.
    plot_ext : str
        File extension of the figure to be saved.
    xzoom : List[list[float,float]]
        Values at which to split the x-axis.
    """
    xmin, xmax = ax.get_xlim()
    for ix in range(len(xzoom)):
        ax.set_xlim(xmin=xzoom[ix][0], xmax=xzoom[ix][1])
        figfile = figbase + ".sub" + str(ix + 1) + plot_ext
        savefig(fig, figfile)
    ax.set_xlim(xmin=xmin, xmax=xmax)


def zoom_xy_and_save(
    fig: matplotlib.figure.Figure,
    ax: matplotlib.axes.Axes,
    figbase: str,
    plot_ext: str,
    xyzoom: List[Tuple[float, float, float, float]],
    scale: float = 1000,
) -> None:
    """
    Zoom in on subregions in x,y-space and save the figure.

    Arguments
    ---------
    fig : matplotlib.figure.Figure
        Figure to be processed.
    ax : matplotlib.axes.Axes
        Axes to be processed.
    fig_base : str
        Base name of the figure to be saved.
    plot_ext : str
        File extension of the figure to be saved.
    xyzoom : List[List[float, float, float, float]]
        List of xmin, xmax, ymin, ymax values to zoom into.
    scale: float
        Indicates whether the axes are in m (1) or km (1000).
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    dx_zoom = 0.0
    xy_ratio = (ymax - ymin) / (xmax - xmin)
    for ix in range(len(xyzoom)):
        xmin0 = xyzoom[ix][0]
        xmax0 = xyzoom[ix][1]
        ymin0 = xyzoom[ix][2]
        ymax0 = xyzoom[ix][3]
        dx = xmax0 - xmin0
        dy = ymax0 - ymin0
        if dy < xy_ratio * dx:
            # x range limiting
            dx_zoom = max(dx_zoom, dx)
        else:
            # y range limiting
            dx_zoom = max(dx_zoom, dy / xy_ratio)
    dy_zoom = dx_zoom * xy_ratio

    for ix in range(len(xyzoom)):
        x0 = (xyzoom[ix][0] + xyzoom[ix][1]) / 2
        y0 = (xyzoom[ix][2] + xyzoom[ix][3]) / 2
        ax.set_xlim(xmin=(x0 - dx_zoom / 2) / scale, xmax=(x0 + dx_zoom / 2) / scale)
        ax.set_ylim(ymin=(y0 - dy_zoom / 2) / scale, ymax=(y0 + dy_zoom / 2) / scale)
        figfile = figbase + ".sub" + str(ix + 1) + plot_ext
        savefig(fig, figfile)

    ax.set_xlim(xmin=xmin, xmax=xmax)
    ax.set_ylim(ymin=ymin, ymax=ymax)
