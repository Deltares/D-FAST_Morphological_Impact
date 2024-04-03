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

from pathlib import Path
from dfastmi.batch.DflowfmReporters import ReporterDflowfmReporter
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.batch.XykmData import XykmData
from dfastmi.plotting import plot_overview, zoom_xy_and_save, savefig
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.map_file import MapFile
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm

import netCDF4
import numpy

class ReporterDflowfm():
    
    _reporter : ReporterDflowfmReporter
    
    def __init__(self, display : bool):
        """
        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        """
        self._reporter = ReporterDflowfmReporter(display)
    
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
        self._reporter.report_writing_output()
        map_file = MapFile(report_data.one_fm_filename)
        meshname = map_file.mesh2d_name
        facedim = map_file.face_dimension_name
        dst = Path(outputdir) / ApplicationSettingsHelper.get_filename("netcdf.out")
        map_file.copy_ugrid(dst)
        nc_fill = netCDF4.default_fillvals['f8']
        projmesh = Path(outputdir) / 'projected_mesh.nc'

        self._grid_update(report_data, report_data.xykm_data.iface, meshname, facedim, dst, nc_fill, projmesh, map_file)

        if report_data.xykm_data.xykm is not None:
            self._replace_coordinates_in_destination_file(report_data, report_data.xykm_data, meshname, nc_fill, projmesh)

        self._plot_data(plotting_options, report_data.xykm_data, report_data.dzgemi)

        self._reporter.report_compute_initial_year_dredging()

        if report_data.xykm_data.xykm is not None:
            self._grid_update_xykm(outputdir, report_data.face_node_connectivity, meshname, facedim, nc_fill, report_data.sedimentation_data, report_data.xykm_data, map_file)

    def _grid_update(self, report_data : OutputDataDflowfm, iface : numpy.ndarray, meshname : str, facedim : str, dst : Path, nc_fill : float, projmesh :Path, map_file : MapFile):
        
        rsigma = report_data.rsigma
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
        dst_map_file = MapFile(dst)
        dst_map_file.add_variable(
                "avgdzb",
                dzgem,
                meshname,
                facedim,
                long_name="year-averaged bed level change without dredging",
                unit="m",
            )
        dzmax = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        dzmax[iface]=dzmaxi
        dst_map_file.add_variable(
                "maxdzb",
                dzmax,
                meshname,
                facedim,
                long_name=zmax_str,
                unit="m",
            )
        dzmin = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        dzmin[iface]=dzmini
        dst_map_file.add_variable(
                "mindzb",
                dzmin,
                meshname,
                facedim,
                long_name=zmin_str,
                unit="m",
            )
        for i in range(len(dzbi)):
            j = (i + 1) % len(dzbi)
            dzb = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
            dzb[iface]=dzbi[j]
            dst_map_file.add_variable(
                    "dzb_{}".format(i),
                    dzb,
                    meshname,
                    facedim,
                    long_name="bed level change at end of period {}".format(i+1),
                    unit="m",
                )
            if rsigma[i]<1 and isinstance(dzq[i], numpy.ndarray):
                dzq_full = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
                dzq_full[iface]=dzq[i]
                dst_map_file.add_variable(
                        "dzq_{}".format(i),
                        dzq_full,
                        meshname,
                        facedim,
                        long_name="equilibrium bed level change aimed for during period {}".format(i+1),
                        unit="m",
                    )

        map_file.copy_ugrid(projmesh)
        projmesh_map_file = MapFile(projmesh)
        projmesh_map_file.add_variable(
                "avgdzb",
                dzgem,
                meshname,
                facedim,
                long_name="year-averaged bed level change without dredging",
                unit="m",
            )

    def _replace_coordinates_in_destination_file(self, report_data : OutputDataDflowfm, xykm_data : XykmData, meshname : str, nc_fill : float, projmesh : Path):
        self._reporter.print_replacing_coordinates()
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

    def _grid_update_xykm(self, outputdir : str, face_node_connectivity : numpy.ndarray, meshname : str, facedim : str, nc_fill : float, sedimentation_data : SedimentationData, xykm_data : XykmData, map_file : MapFile):
        self._reporter.print_sedimentation_and_erosion(sedimentation_data)

        projmesh = Path(outputdir) / 'sedimentation_weights.nc'
        projmesh_map_file = MapFile(projmesh)
        map_file.copy_ugrid(projmesh)
        projmesh_map_file.add_variable(
            "interest_region",
            xykm_data.interest_region,
            meshname,
            facedim,
            long_name="Region on which the sedimentation analysis was performed",
            unit="1",
        )
        
        sed_area = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        for i in range(len(sedimentation_data.sed_area_list)):
            sed_area[xykm_data.iface[sedimentation_data.sed_area_list[i] == 1]] = i+1
        projmesh_map_file.add_variable(
            "sed_area",
            sed_area,
            meshname,
            facedim,
            long_name="Sedimentation area",
            unit="1",
        )
        
        ero_area = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        for i in range(len(sedimentation_data.ero_area_list)):
            ero_area[xykm_data.iface[sedimentation_data.ero_area_list[i] == 1]] = i+1
        projmesh_map_file.add_variable(
            "ero_area",
            ero_area,
            meshname,
            facedim,
            long_name="Erosion area",
            unit="1",
        )
        
        wght_estimate1 = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        wght_estimate1[xykm_data.iface] = sedimentation_data.wght_estimate1i
        projmesh_map_file.add_variable(
            "wght_estimate1",
            wght_estimate1,
            meshname,
            facedim,
            long_name="Weight per cell for determining initial year sedimentation volume estimate 1",
            unit="1",
        )
        
        wbin = numpy.repeat(nc_fill, face_node_connectivity.shape[0])
        wbin[xykm_data.iface] = sedimentation_data.wbini
        projmesh_map_file.add_variable(
            "wbin",
            wbin,
            meshname,
            facedim,
            long_name="Index of width bin",
            unit="1",
        )