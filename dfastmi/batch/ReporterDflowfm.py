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

from pathlib import Path
from typing import Dict
from dfastmi.batch.DflowfmLoggers import ReporterDflowfmLogger
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.batch.XykmData import XykmData
from dfastmi.plotting import plot_overview, zoom_xy_and_save, savefig
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.GridOperations import GridOperations
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm

import netCDF4
import numpy

class ReporterDflowfm():
    
    _logger : ReporterDflowfmLogger
    
    def __init__(self, display : bool):
        """
        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        """
        self._logger = ReporterDflowfmLogger(display)
    
    def report(self, outputdir : Path, plotting_options : PlotOptions, report_data : OutputDataDflowfm):
        """
        write report data to a netCDF UGRID file similar to D-Flow FM.

        Arguments
        ---------
        outputdir : Path
            Path of output directory.
        plotting_options : PlotOptions
            Class containing the plot options.
        report_data  : OutputDataDflowfm
            DTO with the data which is needed to create a report.
        """
        self._logger.log_writing_output()
        meshname, facedim = GridOperations.get_mesh_and_facedim_names(report_data.one_fm_filename)
        dst = str(outputdir.joinpath(ApplicationSettingsHelper.get_filename("netcdf.out")))
        GridOperations.copy_ugrid(report_data.one_fm_filename, meshname, dst)
        nc_fill = netCDF4.default_fillvals['f8']
        projmesh = str(Path(outputdir).joinpath('projected_mesh.nc'))

        self._grid_update(report_data, report_data.xykm_data.iface, meshname, facedim, dst, nc_fill, projmesh)

        if report_data.xykm_data.xykm is not None:
            self._replace_coordinates_in_destination_file(report_data, report_data.xykm_data, meshname, nc_fill, projmesh)

        self._plot_data(plotting_options, report_data.xykm_data, report_data.dzgemi)

        self._logger.log_compute_initial_year_dredging()

        if report_data.xykm_data.xykm is not None:
            self._grid_update_xykm(outputdir, report_data.one_fm_filename, report_data.face_node_connectivity, meshname, facedim, nc_fill, report_data.sedimentation_data, report_data.xykm_data)

    def _grid_update(self, report_data : OutputDataDflowfm, iface : numpy.ndarray, meshname : str, facedim : str, dst : str, nc_fill : float, projmesh :str):
        
        rsigma = report_data.rsigma
        one_fm_filename = report_data.one_fm_filename
        face_node_connectivity = report_data.face_node_connectivity
        dzq = report_data.dzq
        dzgemi = report_data.dzgemi
        dzmaxi = report_data.dzmaxi
        dzmini = report_data.dzmini
        dzbi = report_data.dzbi
        zmax_str = report_data.zmax_str
        zmin_str = report_data.zmin_str
        
        dzgem = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        dzgem[iface]=dzgemi
        GridOperations.ugrid_add(
                dst,
                "avgdzb",
                dzgem,
                meshname,
                facedim,
                long_name="year-averaged bed level change without dredging",
                units="m",
            )
        dzmax = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        dzmax[iface]=dzmaxi
        GridOperations.ugrid_add(
                dst,
                "maxdzb",
                dzmax,
                meshname,
                facedim,
                long_name=zmax_str,
                units="m",
            )
        dzmin = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        dzmin[iface]=dzmini
        GridOperations.ugrid_add(
                dst,
                "mindzb",
                dzmin,
                meshname,
                facedim,
                long_name=zmin_str,
                units="m",
            )
        for i in range(len(dzbi)):
            j = (i + 1) % len(dzbi)
            dzb = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
            dzb[iface]=dzbi[j]
            GridOperations.ugrid_add(
                    dst,
                    "dzb_{}".format(i),
                    dzb,
                    meshname,
                    facedim,
                    long_name="bed level change at end of period {}".format(i+1),
                    units="m",
                )
            if rsigma[i]<1 and isinstance(dzq[i], numpy.ndarray):
                dzq_full = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
                dzq_full[iface]=dzq[i]
                GridOperations.ugrid_add(
                        dst,
                        "dzq_{}".format(i),
                        dzq_full,
                        meshname,
                        facedim,
                        long_name="equilibrium bed level change aimed for during period {}".format(i+1),
                        units="m",
                    )

        GridOperations.copy_ugrid(one_fm_filename, meshname, projmesh)
        GridOperations.ugrid_add(
                projmesh,
                "avgdzb",
                dzgem,
                meshname,
                facedim,
                long_name="year-averaged bed level change without dredging",
                units="m",
            )

    def _replace_coordinates_in_destination_file(self, report_data : OutputDataDflowfm, xykm_data : XykmData, meshname : str, nc_fill : float, projmesh : str):
        self._logger.print_replacing_coordinates()
        sn = numpy.repeat(nc_fill, report_data.xn.shape[0])
        sn[xykm_data.inode]=xykm_data.sni
        nn = numpy.repeat(nc_fill, report_data.xn.shape[0])
        nn[xykm_data.inode]=xykm_data.nni

        # open destination file
        dst = netCDF4.Dataset(projmesh, "a")
        node_x = meshname + '_node_x'
        node_y = meshname + '_node_y'
        dst.variables[node_x][:] = sn[:]
        dst.variables[node_y][:] = nn[:]
        dst.close()

    def _plot_data(self, plotting_options : PlotOptions, xykm_data : XykmData, dzgemi : numpy.ndarray):
        if plotting_options.plotting:
            if xykm_data.face_node_connectivity_index.mask.shape == ():
                    # all faces have the same number of nodes
                nnodes = numpy.ones(xykm_data.face_node_connectivity_index.data.shape[0], dtype=numpy.int64) * xykm_data.face_node_connectivity_index.data.shape[1]
            else:
                    # varying number of nodes
                nnodes = xykm_data.face_node_connectivity_index.mask.shape[1] - xykm_data.face_node_connectivity_index.mask.sum(axis=1)
            fig, ax = plot_overview(
                    (xykm_data.xmin, xykm_data.ymin, xykm_data.xmax, xykm_data.ymax),
                    xykm_data.xykline,
                    xykm_data.face_node_connectivity_index,
                    nnodes,
                    xykm_data.xni,
                    xykm_data.yni,
                    dzgemi,
                    "x-coordinate [km]",
                    "y-coordinate [km]",
                    "change to year-averaged equilibrium",
                    "erosion and sedimentation [m]",
                    plotting_options.xyzoom,
                )

            if plotting_options.saveplot:
                figbase = Path(plotting_options.figure_save_directory) / "overview"
                if plotting_options.saveplot_zoomed:
                    zoom_xy_and_save(fig, ax, figbase, plotting_options.plot_extension, plotting_options.xyzoom, scale=1000)
                figfile = figbase.with_suffix(plotting_options.plot_extension)
                savefig(fig, figfile)

    def _grid_update_xykm(self, outputdir : str, one_fm_filename : str, face_node_connectivity : numpy.ndarray, meshname : str, facedim : str, nc_fill : float, sedimentation_data : SedimentationData, xykm_data : XykmData):
        self._logger.print_sedimentation_and_erosion(sedimentation_data)

        projmesh = str(outputdir.joinpath('sedimentation_weights.nc'))
        GridOperations.copy_ugrid(one_fm_filename, meshname, projmesh)
        GridOperations.ugrid_add(
                    projmesh,
                    "interest_region",
                    xykm_data.interest_region,
                    meshname,
                    facedim,
                    long_name="Region on which the sedimentation analysis was performed",
                units="1",
                )
        
        sed_area = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        for i in range(len(sedimentation_data.sed_area_list)):
            sed_area[xykm_data.iface[sedimentation_data.sed_area_list[i] == 1]] = i+1
        GridOperations.ugrid_add(
                    projmesh,
                    "sed_area",
                    sed_area,
                    meshname,
                    facedim,
                    long_name="Sedimentation area",
                    units="1",
                )
        
        ero_area = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        for i in range(len(sedimentation_data.ero_area_list)):
            ero_area[xykm_data.iface[sedimentation_data.ero_area_list[i] == 1]] = i+1
        GridOperations.ugrid_add(
                    projmesh,
                    "ero_area",
                    ero_area,
                    meshname,
                    facedim,
                    long_name="Erosion area",
                    units="1",
                )
        
        wght_estimate1 = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        wght_estimate1[xykm_data.iface] = sedimentation_data.wght_estimate1i
        GridOperations.ugrid_add(
                    projmesh,
                    "wght_estimate1",
                    wght_estimate1,
                    meshname,
                    facedim,
                    long_name="Weight per cell for determining initial year sedimentation volume estimate 1",
                    units="1",
                )
        
        wbin = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        wbin[xykm_data.iface] = sedimentation_data.wbini
        GridOperations.ugrid_add(
                    projmesh,
                    "wbin",
                    wbin,
                    meshname,
                    facedim,
                    long_name="Index of width bin",
                    units="1",
                )