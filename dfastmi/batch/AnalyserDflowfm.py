import dfastmi.batch.Distance
import dfastmi.batch.Face
import dfastmi.batch.SedimentationVolume
import dfastmi.kernel.core
from dfastmi.batch.ReportData import ReportData
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.GridOperations import GridOperations
from dfastmi.kernel.typehints import Vector, BoolVector

import numpy
import shapely
import math
import os
from typing import Any, Dict, Optional, TextIO, Tuple, Union

class AnalyserDflowfm():
    def analyse(self, display, report, q_threshold, tstag, Q, T, rsigma, slength, nwidth, ucrit, filenames, xykm, needs_tide, n_fields, tide_bc, old_zmin_zmax, outputdir, plotops):
        missing_data = False

        one_fm_filename, missing_data = self._get_first_fm_data_filename(report, q_threshold, Q, rsigma, filenames, needs_tide, tide_bc)

        if missing_data:
            return missing_data, None

        if display:
            ApplicationSettingsHelper.log_text('-- load mesh')
        xn, yn, FNC = self._get_xynode_connect(one_fm_filename)

        xykm_data = self._get_xykm_data(xykm, xn, yn, FNC, display)

        if xykm is None and needs_tide:
            print("RiverKM needs to be specified for tidal applications.")
            return True, None

        missing_data, dzq = self._get_dzq(report, Q, rsigma, ucrit, filenames, needs_tide, n_fields, tide_bc, missing_data, xykm_data.iface, xykm_data.dxi, xykm_data.dyi)

        if not missing_data:
            if display:
                ApplicationSettingsHelper.log_text("char_bed_changes")

            if tstag > 0:
                dzq = (dzq[0], dzq[0], dzq[1], dzq[2])
                T = (T[0], tstag, T[1], T[2])
                rsigma = (rsigma[0], 1.0, rsigma[1], rsigma[2])

            # main_computation now returns new pointwise zmin and zmax
            dzgemi, dzmaxi, dzmini, dzbi = dfastmi.kernel.core.main_computation(
                dzq, T, rsigma
            )

            if old_zmin_zmax:
                # get old zmax and zmin
                dzmaxi = dzbi[0]
                zmax_str = "maximum bed level change after flood without dredging"
                dzmini = dzbi[1]
                zmin_str = "minimum bed level change after low flow without dredging"
            else:
                zmax_str = "maximum value of bed level change without dredging"
                zmin_str = "minimum value of bed level change without dredging"

        sedimentation_data = None
        if xykm is not None:
            sedarea, sedvol, sed_area_list, eroarea, erovol, ero_area_list, wght_estimate1i, wbini = dfastmi.batch.SedimentationVolume.comp_sedimentation_volume(xykm_data.xni, xykm_data.yni, xykm_data.sni, xykm_data.nni, xykm_data.FNCi, dzgemi, slength, nwidth, xykm_data.xykline, one_fm_filename, outputdir, plotops)
            sedimentation_data = SedimentationData(sedarea, sedvol, sed_area_list, eroarea, erovol, ero_area_list, wght_estimate1i, wbini)

        return missing_data, ReportData(rsigma, one_fm_filename, xn, FNC, dzq, dzgemi, dzmaxi, dzmini, dzbi, zmax_str, zmin_str, xykm_data, sedimentation_data)

    def _get_first_fm_data_filename(self,
        report: TextIO,
        q_threshold: float,
        Q: Vector,
        rsigma: Vector,
        filenames: Dict[Any, Tuple[str,str]],
        needs_tide: bool,
        tide_bc: Tuple[str, ...],
    ):
        key: Union[Tuple[float, int], float]
        missing_data = False
        one_fm_filename: Union[None, str] = None
        # determine the name of the first FM data file that will be used
        if 0 in filenames.keys(): # the keys are 0,1,2
            for i in range(3):
                if not missing_data and not Q[i] is None:
                    one_fm_filename = filenames[i][0]
                    break
        else: # the keys are the conditions
            for i in range(len(Q)):
                if not missing_data and not Q[i] is None:
                    q = Q[i]
                    if needs_tide:
                        t = tide_bc[i]
                        key = (q,t)
                    else:
                        key = q
                    if rsigma[i] == 1 or Q[i] <= q_threshold:
                        # no celerity or measure not active, so ignore field
                        pass
                    elif key in filenames.keys():
                        one_fm_filename = filenames[key][0]
                        break
                    else:
                        if needs_tide:
                            ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=report)
                        else:
                            ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=report)
                        ApplicationSettingsHelper.log_text("end_program", file=report)
                        missing_data = True

        if one_fm_filename is None:
            print("The measure is not active for any of the checked conditions.")
            missing_data = True

        return one_fm_filename, missing_data

    def _get_xykm_data(self, xykm, xn, yn, FNC, display):
        if xykm is None:
            # keep all nodes and faces
            keep = numpy.full(xn.shape, True)
            xni, yni, FNCi, iface, inode = dfastmi.batch.Face.filter_faces_by_node_condition(xn, yn, FNC, keep)
            xmin = xn.min()
            xmax = xn.max()
            ymin = yn.min()
            ymax = yn.max()
            dxi = None
            dyi = None
            xykline = None

            interest_region = None
            sni = None
            nni = None
        else:
            dnmax = 3000.0
            if display:
                ApplicationSettingsHelper.log_text('-- identify region of interest')
            # add call to dfastbe.io.clip_path_to_kmbounds?
            print("buffer")
            xybuffer = xykm.buffer(dnmax)
            bbox = xybuffer.envelope.exterior
            print("prepare")
            xybprep = shapely.prepared.prep(xybuffer)

            print("prepare filter step 1")
            xmin = bbox.coords[0][0]
            xmax = bbox.coords[1][0]
            ymin = bbox.coords[0][1]
            ymax = bbox.coords[2][1]
            keep = (xn > xmin) & (xn < xmax) & (yn > ymin) & (yn < ymax)
            print("prepare filter step 2")
            for i in range(xn.size):
                if keep[i] and not xybprep.contains(shapely.geometry.Point((xn[i], yn[i]))):
                    keep[i] = False

            print("apply filter")
            xni, yni, FNCi, iface, inode = dfastmi.batch.Face.filter_faces_by_node_condition(xn, yn, FNC, keep)
            interest_region = numpy.zeros(FNC.shape[0], dtype=numpy.int64)
            interest_region[iface] = 1

            xykline = numpy.array(xykm.coords)

            # project all nodes onto the line, obtain the distance along (sni) and normal (dni) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            xyline = xykline[:,:2]

            # project all nodes onto the line, obtain the distance along (sfi) and normal (nfi) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            if display:
                ApplicationSettingsHelper.log_text('-- project')
            sni, nni = self._proj_xy_line(xni, yni, xyline)
            sfi = dfastmi.batch.Face.face_mean(sni, FNCi)

            # determine chainage values of each cell
            if display:
                ApplicationSettingsHelper.log_text('-- chainage')

            # determine line direction for each cell
            if display:
                ApplicationSettingsHelper.log_text('-- direction')
            dxi, dyi = self._get_direction(xyline, sfi)

            if display:
                ApplicationSettingsHelper.log_text('-- done')

        return XykmData(xykm, xni, yni, FNCi, iface, inode, xmin, xmax, ymin, ymax, dxi, dyi, xykline, interest_region, sni, nni)

    def _get_dzq(self, report, Q, rsigma, ucrit, filenames, needs_tide, n_fields, tide_bc, missing_data, iface, dxi, dyi):
        dzq = [None] * len(Q)
        if 0 in filenames.keys(): # the keys are 0,1,2
            for i in range(3):
                if not missing_data and not Q[i] is None:
                    dzq[i] = self._get_values_fm(i+1, Q[i], ucrit, report, filenames[i], n_fields, dxi, dyi, iface)
                    if dzq[i] is None:
                        missing_data = True
                else:
                    dzq[i] = 0
        else: # the keys are the conditions
            for i in range(len(Q)):
                if not missing_data and not Q[i] is None:
                    q = Q[i]
                    if needs_tide:
                        t = tide_bc[i]
                        key = (q,t)
                    else:
                        t = None
                        key = q
                    if rsigma[i] == 1:
                        # no celerity, so ignore field
                        dzq[i] = 0
                    elif key in filenames.keys():
                        if t:
                            n_fields_request = n_fields
                        else:
                            n_fields_request = 1
                        dzq[i] = self._get_values_fm(i+1, q, ucrit, report, filenames[key], n_fields_request, dxi, dyi, iface)
                    else:
                        if t > 0:
                            ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=report)
                        else:
                            ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=report)
                        ApplicationSettingsHelper.log_text("end_program", file=report)
                        missing_data = True
                else:
                    dzq[i] = 0
        return missing_data,dzq

    def _get_values_fm(
        self,
        stage: int,
        q: float,
        ucrit: float,
        report: TextIO,
        filenames: Tuple[str, str],
        n_fields: int,
        dx: numpy.ndarray,
        dy: numpy.ndarray,
        iface: numpy.ndarray,
    ) -> numpy.ndarray:
        """
        Read D-Flow FM data files for the specified stage, and return dzq.

        Arguments
        ---------
        stage : int
            Discharge level (1, 2 or 3).
        q : float
            Discharge value.
        ucrit : float
            Critical flow velocity.
        report : TextIO
            Text stream for log file.
        filenames : Tuple[str, str]
            Names of the reference simulation file and file with the implemented measure.
        n_fields : int
            Number of fields to process (e.g. to cover a tidal period).
        dx : numpy.ndarray
            Array containing the x-component of the direction vector at each cell.
        dy : numpy.ndarray
            Array containing the y-component of the direction vector at each cell.
        iface : numpy.ndarray
            Array containing the subselection of cells.

        Returns
        -------
        dzq : numpy.ndarray
            Array containing equilibrium bed level change.
        """
        cblok = str(stage)

        # reference file
        if filenames[0] == "":
            ApplicationSettingsHelper.log_text("no_file_specified", dict={"q": q}, file=report)
            ApplicationSettingsHelper.log_text("end_program", file=report)
            return None
        elif not os.path.isfile(filenames[0]):
            ApplicationSettingsHelper.log_text("file_not_found", dict={"name": filenames[0]}, file=report)
            ApplicationSettingsHelper.log_text("end_program", file=report)
            return None
        else:
            pass

        # file with measure implemented
        if not os.path.isfile(filenames[1]):
            ApplicationSettingsHelper.log_text("file_not_found", dict={"name": filenames[1]}, file=report)
            ApplicationSettingsHelper.log_text("end_program", file=report)
            return None
        else:
            pass

        dzq = 0.
        tot = 0.
        ifld: Optional[int]
        if n_fields > 1:
            ustream_pos = numpy.zeros(dx.shape)
            ustream_neg = numpy.zeros(dx.shape)
            dzq_pos = numpy.zeros(dx.shape)
            dzq_neg = numpy.zeros(dx.shape)
            t_pos = numpy.zeros(dx.shape)
            t_neg = numpy.zeros(dx.shape)
            wght_pos = numpy.zeros(dx.shape)
            wght_neg = numpy.zeros(dx.shape)

        ref = GridOperations.read_fm_map(filenames[0], "sea_water_x_velocity", ifld=0)

        for ifld in range(n_fields):
            # if last time step is needed, pass None to allow for files without time specification
            if n_fields == 1:
                ifld = None

            # reference data
            u0 = GridOperations.read_fm_map(filenames[0], "sea_water_x_velocity", ifld=ifld)[iface]
            v0 = GridOperations.read_fm_map(filenames[0], "sea_water_y_velocity", ifld=ifld)[iface]
            umag0 = numpy.sqrt(u0 ** 2 + v0 ** 2)
            h0 = GridOperations.read_fm_map(filenames[0], "sea_floor_depth_below_sea_surface", ifld=ifld)[iface]

            # data with measure
            u1 = GridOperations.read_fm_map(filenames[1], "sea_water_x_velocity", ifld=ifld)[iface]
            v1 = GridOperations.read_fm_map(filenames[1], "sea_water_y_velocity", ifld=ifld)[iface]
            umag1 = numpy.sqrt(u1**2 + v1**2)

            dzq1 = dfastmi.kernel.core.dzq_from_du_and_h(umag0, h0, umag1, ucrit, default=0.0)

            if n_fields > 1:
                ustream = u0*dx + v0*dy

                # positive flow -> flow in downstream direction -> biggest flow in positive direction during peak ebb flow
                ipos = ustream > 0.
                t_pos[ipos] = t_pos[ipos] + 1

                ipos = ustream > ustream_pos
                ustream_pos[ipos] = ustream[ipos]
                dzq_pos[ipos] = dzq1[ipos]

                # negative flow -> flow in upstream direction -> biggest flow in negative direction during peak flood flow
                ineg = ustream < 0.
                t_neg[ineg] = t_neg[ineg] + 1

                ineg = ustream < ustream_neg
                ustream_neg[ineg] = ustream[ineg]
                dzq_neg[ineg] = dzq1[ineg]

        if n_fields > 1:
            dzq = (t_pos * dzq_pos + t_neg * dzq_neg ) / numpy.maximum(t_pos + t_neg, 1)
        else:
            dzq = dzq1

        return dzq

    def _get_xynode_connect(self, filename: str) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
        xn = GridOperations.read_fm_map(filename, "x", location="node")
        yn = GridOperations.read_fm_map(filename, "y", location="node")
        FNC = GridOperations.read_fm_map(filename, "face_node_connectivity")
        if FNC.mask.shape == ():
            # all faces have the same number of nodes; empty mask
            FNC.mask = FNC<0
        else:
            # varying number of nodes
            FNC.mask = numpy.logical_or(FNC.mask,FNC<0)

        return xn, yn, FNC

    def _get_direction(self, xyline: numpy.ndarray, spnt: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
        """
        Determine the orientation of a line at a given set of points.

        Arguments
        ---------
        xyline : numpy.ndarray
            Array containing the x,y data of a line.
        spnt : numpy.ndarray
            Array of length N containing the location of points measured as distance along the same line.

        Results
        -------
        dxpnt : numpy.ndarray
            Array of length N containing x-component of the unit direction vector at the given points.
        dypnt : numpy.ndarray
            Array of length N containing y-component of the unit direction vector at the given points.
        """
        sline = dfastmi.batch.Distance.distance_along_line(xyline)
        M = len(sline)
        N = len(spnt)

        # make sure that spnt is sorted
        isort = numpy.argsort(spnt)
        unsort = numpy.argsort(isort)
        spnt_sorted = spnt[isort]

        dxpnt = numpy.zeros(N)
        dypnt = numpy.zeros(N)
        j = 0
        for i in range(N):
            s = spnt_sorted[i]
            while j < M:
                if sline[j] < s:
                    j = j+1
                else:
                    break
            if j == 0:
                # distance is less than the distance of the first point, use the direction of the first line segment
                dxy = xyline[1] - xyline[0]
            elif j == M:
                # distance is larger than the distance of all the points on the line, use the direction of the last line segment
                dxy = xyline[-1] - xyline[-2]
            else:
                # somewhere in the middle, get the direction of the line segment
                dxy = xyline[j] - xyline[j-1]
            ds = math.sqrt((dxy**2).sum())
            dxpnt[i] = dxy[0]/ds
            dypnt[i] = dxy[1]/ds

        return dxpnt[unsort], dypnt[unsort]

    def _proj_xy_line(self, xf: numpy.ndarray, yf: numpy.ndarray, xyline: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
        """
        Project points onto a line.

        For a set of points (xf, yf) the closest point P a line (xyline) is determined.
        The quantities returned are the distance (sf) measured along the line (xyline)
        for the closest point P, the signed distance (df) between the original point (xf, yf)
        and the projected point P. If the original point is located alongsize the line
        (xyline) then the distance (df) is the normal distance ... if the original point is
        located before or beyond the line (xyline), it will include an oblique distance component.
        The sign of the distance (df) is positive for points to the right and negative for points
        to the left of the line.

        Arguments
        ---------
        xf : numpy.ndarray
            Array containing the x coordinates of a set of points.
        yf : numpy.ndarray
            Array containing the y coordinates of a set of points.
        xyline : numpy.ndarray
            Array containing the x,y data of a line.

        Results
        -------
        sf : numpy.ndarray
            Array containing the distance along the line.
        df : numpy.ndarray
            Array containing the distance from the line (- for left, + for right).
        """
        # combine xf and yf
        nf = len(xf)
        xyf = numpy.concatenate([xf.reshape((nf,1)),yf.reshape((nf,1))], axis=1)

        # pre-allocate the output arrays
        sf = numpy.zeros(nf)
        df = numpy.zeros(nf)

        # compute distance coordinate along the line
        sline = dfastmi.batch.Distance.distance_along_line(xyline)

        # get an array with only the x,y coordinates of xyline
        last_node = xyline.shape[0] - 1

        # initialize sgn for the exceptional case of xyline containing just one node.
        sgn = 1

        # for each point xyp = xyf[i] ...
        for i,xyp in enumerate(xyf):
            # find the node on xyline closest to xyp
            imin = numpy.argmin(((xyp - xyline) ** 2).sum(axis=1))
            p0 = xyline[imin]

            # determine the distance between that node and xyp
            dist2 = ((xyp - p0) ** 2).sum()

            # distance value of that node
            s = sline[imin]

            if imin == 0:
                # we got the first node
                # check if xyp projects much before the first line segment.
                p1 = xyline[imin + 1]
                alpha = (
                    (p1[0] - p0[0]) * (xyp[0] - p0[0])
                    + (p1[1] - p0[1]) * (xyp[1] - p0[1])
                ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
                sgn = ((p1[0] - p0[0]) * (xyp[1] - p0[1])
                    - (p1[1] - p0[1]) * (xyp[0] - p0[0]))
                # if the closest point is before the segment ...
                if alpha < 0:
                    dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                        xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                    ) ** 2
                    dist2end = dist2 - dist2link
                    if dist2end > 100:
                        dist2 = 1e20

            else:
                # we didn't get the first node
                # project xyp onto the line segment before this node
                p1 = xyline[imin - 1]
                alpha = (
                    (p1[0] - p0[0]) * (xyp[0] - p0[0])
                    + (p1[1] - p0[1]) * (xyp[1] - p0[1])
                ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
                sgn = ((p0[0] - p1[0]) * (xyp[1] - p0[1])
                    - (p0[1] - p1[1]) * (xyp[0] - p0[0]))
                # if there is a closest point not coinciding with the nodes ...
                if alpha > 0 and alpha < 1:
                    dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                        xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                    ) ** 2
                    # if it's actually closer than the node ...
                    if dist2link < dist2:
                        # update the closest point information
                        dist2 = dist2link
                        s = sline[imin] + alpha * (sline[imin - 1] - sline[imin])

            if imin == last_node:
                # we got the last node
                # check if xyp projects much beyond the last line segment.
                p1 = xyline[imin - 1]
                alpha = (
                    (p1[0] - p0[0]) * (xyp[0] - p0[0])
                    + (p1[1] - p0[1]) * (xyp[1] - p0[1])
                ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
                sgn = ((p0[0] - p1[0]) * (xyp[1] - p0[1])
                    - (p0[1] - p1[1]) * (xyp[0] - p0[0]))
                # if the closest point is before the segment ...
                if alpha < 0:
                    dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                        xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                    ) ** 2
                    dist2end = dist2 - dist2link
                    if dist2end > 100:
                        dist2 = 1e20

            else:
                # we didn't get the last node
                # project rp onto the line segment after this node
                p1 = xyline[imin + 1]
                alpha = (
                    (p1[0] - p0[0]) * (xyp[0] - p0[0])
                    + (p1[1] - p0[1]) * (xyp[1] - p0[1])
                ) / ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
                sgn = ((p1[0] - p0[0]) * (xyp[1] - p0[1])
                    - (p1[1] - p0[1]) * (xyp[0] - p0[0]))
                # if there is a closest point not coinciding with the nodes ...
                if alpha > 0 and alpha < 1:
                    dist2link = (xyp[0] - p0[0] - alpha * (p1[0] - p0[0])) ** 2 + (
                        xyp[1] - p0[1] - alpha * (p1[1] - p0[1])
                    ) ** 2
                    # if it's actually closer than the previous value ...
                    if dist2link < dist2:
                        # update the closest point information
                        dist2 = dist2link
                        s = sline[imin] + alpha * (
                            sline[imin + 1] - sline[imin]
                        )

            # store the distance values, loop ... and return
            sf[i] = s
            df[i] = math.copysign(math.sqrt(dist2), sgn)

        return sf,df