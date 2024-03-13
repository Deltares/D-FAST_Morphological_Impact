from dfastmi.batch.DflowfmLoggers import ReporterDflowfmLogger
import dfastmi.plotting
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.GridOperations import GridOperations
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm

import netCDF4
import numpy
import os

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
    
    def report(self, outputdir, plotops, report_data : OutputDataDflowfm):
        """
        write report data to a netCDF UGRID file similar to D-Flow FM.

        Arguments
        ---------
        outputdir : str
            Name of output directory.
        plotops : Dict
            Dictionary of plot settings
        report_data  : OutputDataDflowfm
            DTO with the data which is needed to create a report.
        """
        self._logger.log_writing_output()
        meshname, facedim = GridOperations.get_mesh_and_facedim_names(report_data.one_fm_filename)
        dst = outputdir + os.sep + ApplicationSettingsHelper.get_filename("netcdf.out")
        GridOperations.copy_ugrid(report_data.one_fm_filename, meshname, dst)
        nc_fill = netCDF4.default_fillvals['f8']
        projmesh = outputdir + os.sep + 'projected_mesh.nc'

        self._grid_update(report_data, report_data.xykm_data.iface, meshname, facedim, dst, nc_fill, projmesh)

        if report_data.xykm_data.xykm is not None:
            self._replace_coordinates_in_destination_file(report_data.xn, report_data.xykm_data.inode, report_data.xykm_data.sni, report_data.xykm_data.nni, meshname, nc_fill, projmesh)

        self._plot_data(plotops, report_data.xykm_data.xni, report_data.xykm_data.yni, report_data.xykm_data.face_node_connectivity_index, report_data.xykm_data.xmin, report_data.xykm_data.xmax, report_data.xykm_data.ymin, report_data.xykm_data.ymax, report_data.xykm_data.xykline, report_data.dzgemi)

        self._logger.log_compute_initial_year_dredging()

        if report_data.xykm_data.xykm is not None:
            self._grid_update_xykm(outputdir, report_data.one_fm_filename, report_data.face_node_connectivity, report_data.xykm_data.iface, report_data.xykm_data.interest_region, meshname, facedim, nc_fill, report_data.sedimentation_data)



    def _grid_update(self, report_data : OutputDataDflowfm, iface, meshname, facedim, dst, nc_fill, projmesh):
        
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

    def _replace_coordinates_in_destination_file(self, xn, inode, sni, nni, meshname, nc_fill, projmesh):
        self._logger.print_replacing_coordinates()
        sn = numpy.repeat(nc_fill, xn.shape[0])
        sn[inode]=sni
        nn = numpy.repeat(nc_fill, xn.shape[0])
        nn[inode]=nni

        # open destination file
        dst = netCDF4.Dataset(projmesh, "a")
        dst.variables[meshname + '_node_x'][:] = sn[:]
        dst.variables[meshname + '_node_y'][:] = nn[:]
        dst.close()

    def _plot_data(self, plotops, xni, yni, face_node_connectivity_index, xmin, xmax, ymin, ymax, xykline, dzgemi):
        if plotops['plotting']:
            if face_node_connectivity_index.mask.shape == ():
                    # all faces have the same number of nodes
                nnodes = numpy.ones(face_node_connectivity_index.data.shape[0], dtype=numpy.int64) * face_node_connectivity_index.data.shape[1]
            else:
                    # varying number of nodes
                nnodes = face_node_connectivity_index.mask.shape[1] - face_node_connectivity_index.mask.sum(axis=1)
            fig, ax = dfastmi.plotting.plot_overview(
                    (xmin, ymin, xmax, ymax),
                    xykline,
                    face_node_connectivity_index,
                    nnodes,
                    xni,
                    yni,
                    dzgemi,
                    "x-coordinate [km]",
                    "y-coordinate [km]",
                    "change to year-averaged equilibrium",
                    "erosion and sedimentation [m]",
                    plotops['xyzoom'],
                )

            if plotops['saveplot']:
                figbase = plotops['figdir'] + os.sep + "overview"
                if plotops['saveplot_zoomed']:
                    dfastmi.plotting.zoom_xy_and_save(fig, ax, figbase, plotops['plot_ext'], plotops['xyzoom'], scale=1000)
                figfile = figbase + plotops['plot_ext']
                dfastmi.plotting.savefig(fig, figfile)

    def _grid_update_xykm(self, outputdir, one_fm_filename, face_node_connectivity, iface, interest_region, meshname, facedim, nc_fill, sedimentation_data : SedimentationData):
        self._logger.print_sedimentation_and_erosion(sedimentation_data)

        projmesh = outputdir + os.sep + 'sedimentation_weights.nc'
        GridOperations.copy_ugrid(one_fm_filename, meshname, projmesh)
        GridOperations.ugrid_add(
                    projmesh,
                    "interest_region",
                    interest_region,
                    meshname,
                    facedim,
                    long_name="Region on which the sedimentation analysis was performed",
                units="1",
                )
        sed_area = numpy.repeat(nc_fill, face_node_connectivity.shape[0])

        for i in range(len(sedimentation_data.sed_area_list)):
            sed_area[iface[sedimentation_data.sed_area_list[i] == 1]] = i+1
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
            ero_area[iface[sedimentation_data.ero_area_list[i] == 1]] = i+1
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
        wght_estimate1[iface] = sedimentation_data.wght_estimate1i
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
        wbin[iface] = sedimentation_data.wbini
        GridOperations.ugrid_add(
                    projmesh,
                    "wbin",
                    wbin,
                    meshname,
                    facedim,
                    long_name="Index of width bin",
                    units="1",
                )