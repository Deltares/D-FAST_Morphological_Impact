import dfastmi.plotting
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.GridOperations import GridOperations
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm

import netCDF4
import numpy
import os

class ReporterDflowfm():
    def report(self, display, outputdir, plotops, report_data : OutputDataDflowfm):
        if display:
            ApplicationSettingsHelper.log_text('writing_output')
        meshname, facedim = GridOperations.get_mesh_and_facedim_names(report_data.one_fm_filename)
        dst = outputdir + os.sep + ApplicationSettingsHelper.get_filename("netcdf.out")
        GridOperations.copy_ugrid(report_data.one_fm_filename, meshname, dst)
        nc_fill = netCDF4.default_fillvals['f8']
        projmesh = outputdir + os.sep + 'projected_mesh.nc'

        self._grid_update(report_data.rsigma, report_data.one_fm_filename, report_data.FNC, report_data.xykm_data.iface, report_data.dzq, report_data.dzgemi, report_data.dzmaxi, report_data.dzmini, report_data.dzbi, report_data.zmax_str, report_data.zmin_str, meshname, facedim, dst, nc_fill, projmesh)

        if report_data.xykm_data.xykm is not None:
            self._replace_coordinates_in_destination_file(report_data.xn, report_data.xykm_data.inode, report_data.xykm_data.sni, report_data.xykm_data.nni, meshname, nc_fill, projmesh)

        self._plot_data(plotops, report_data.xykm_data.xni, report_data.xykm_data.yni, report_data.xykm_data.FNCi, report_data.xykm_data.xmin, report_data.xykm_data.xmax, report_data.xykm_data.ymin, report_data.xykm_data.ymax, report_data.xykm_data.xykline, report_data.dzgemi)

        if display:
            ApplicationSettingsHelper.log_text('compute_initial_year_dredging')

        if report_data.xykm_data.xykm is not None:
            self._grid_update_xykm(display, outputdir, report_data.one_fm_filename, report_data.FNC, report_data.xykm_data.iface, report_data.xykm_data.interest_region, meshname, facedim, nc_fill, report_data.sedimentation_data)

    def _grid_update(self, rsigma, one_fm_filename, FNC, iface, dzq, dzgemi, dzmaxi, dzmini, dzbi, zmax_str, zmin_str, meshname, facedim, dst, nc_fill, projmesh):
        dzgem = numpy.repeat(nc_fill, FNC.shape[0])
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
        dzmax = numpy.repeat(nc_fill, FNC.shape[0])
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
        dzmin = numpy.repeat(nc_fill, FNC.shape[0])
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
            dzb = numpy.repeat(nc_fill, FNC.shape[0])
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
                dzq_full = numpy.repeat(nc_fill, FNC.shape[0])
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
        print("replacing coordinates")
        sn = numpy.repeat(nc_fill, xn.shape[0])
        sn[inode]=sni
        nn = numpy.repeat(nc_fill, xn.shape[0])
        nn[inode]=nni

                # open destination file
        dst = netCDF4.Dataset(projmesh, "a")
        dst.variables[meshname + '_node_x'][:] = sn[:]
        dst.variables[meshname + '_node_y'][:] = nn[:]
        dst.close()

    def _plot_data(self, plotops, xni, yni, FNCi, xmin, xmax, ymin, ymax, xykline, dzgemi):
        if plotops['plotting']:
            if FNCi.mask.shape == ():
                    # all faces have the same number of nodes
                nnodes = numpy.ones(FNCi.data.shape[0], dtype=numpy.int64) * FNCi.data.shape[1]
            else:
                    # varying number of nodes
                nnodes = FNCi.mask.shape[1] - FNCi.mask.sum(axis=1)
            fig, ax = dfastmi.plotting.plot_overview(
                    (xmin, ymin, xmax, ymax),
                    xykline,
                    FNCi,
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

    def _grid_update_xykm(self, display, outputdir, one_fm_filename, FNC, iface, interest_region, meshname, facedim, nc_fill, sedimentation_data : SedimentationData):
        if display:
            if sedimentation_data.sedvol.shape[1] > 0:
                print("Estimated sedimentation volume per area using 3 methods")
                print("                              Max:             Method 1:        Method 2:       ")
                print("                                sum area*dzeqa      sum_L dzeqa   L*W*avg(dzeqa)")
                for i in range(sedimentation_data.sedvol.shape[1]):
                    print("Area{:3d} ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(i+1, sedimentation_data.sedarea[i], sedimentation_data.sedvol[0,i], sedimentation_data.sedvol[1,i], sedimentation_data.sedvol[2,i]))
                print("Max                         : {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(sedimentation_data.sedvol[0,:].max(), sedimentation_data.sedvol[1,:].max(), sedimentation_data.sedvol[2,:].max()))
                print("Total   ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(sedimentation_data.sedarea.sum(), sedimentation_data.sedvol[0,:].sum(), sedimentation_data.sedvol[1,:].sum(), sedimentation_data.sedvol[2,:].sum()))

            if sedimentation_data.sedvol.shape[1] > 0 and sedimentation_data.erovol.shape[1] > 0:
                print("")

            if sedimentation_data.erovol.shape[1] > 0:
                print("Estimated erosion volume per area using 3 methods")
                print("                              Max:             Method 1:        Method 2:       ")
                print("                                sum area*dzeqa      sum_L dzeqa   L*W*avg(dzeqa)")
                for i in range(sedimentation_data.erovol.shape[1]):
                    print("Area{:3d} ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(i+1, sedimentation_data.eroarea[i], sedimentation_data.erovol[0,i], sedimentation_data.erovol[1,i], sedimentation_data.erovol[2,i]))
                print("Max                         : {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(sedimentation_data.erovol[0,:].max(), sedimentation_data.erovol[1,:].max(), sedimentation_data.erovol[2,:].max()))
                print("Total   ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(sedimentation_data.eroarea.sum(), sedimentation_data.erovol[0,:].sum(), sedimentation_data.erovol[1,:].sum(), sedimentation_data.erovol[2,:].sum()))

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
        sed_area = numpy.repeat(nc_fill, FNC.shape[0])

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
        ero_area = numpy.repeat(nc_fill, FNC.shape[0])

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
        wght_estimate1 = numpy.repeat(nc_fill, FNC.shape[0])
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
        wbin = numpy.repeat(nc_fill, FNC.shape[0])
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