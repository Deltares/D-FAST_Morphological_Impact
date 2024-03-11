import dfastmi.batch.Distance
import dfastmi.batch.Face
import dfastmi.batch.SedimentationVolume
import dfastmi.batch.Projection
import dfastmi.kernel.core
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm
from dfastmi.batch.XykmData import XykmData
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.GridOperations import GridOperations
from dfastmi.kernel.typehints import Vector, BoolVector

import numpy
import shapely
import os
from typing import Any, Dict, Optional, TextIO, Tuple, Union

class _AnalyserDflowfmLogger():
    def __init__(self, display : bool, report : TextIO):
        self.display = display
        self.report = report

    def log_char_bed_changes(self):
        if self.display:
            ApplicationSettingsHelper.log_text("char_bed_changes")

    def log_load_mesh(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- load mesh')

    def log_done(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- done')

    def log_direction(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- direction')

    def log_chainage(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- chainage')

    def log_project(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- project')

    def log_identify_region_of_interest(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- identify region of interest')

    def report_missing_calculation_values(self, needs_tide, q, t):
        if needs_tide:
            ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=self.report)
        else:
            ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_missing_calculation_dzq_values(self, q, t):
        if t > 0:
            ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=self.report)
        else:
            ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_file_not_specified(self, q):
        ApplicationSettingsHelper.log_text("no_file_specified", dict={"q": q}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_file_not_found(self, filename):
        ApplicationSettingsHelper.log_text("file_not_found", dict={"name": filename}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def print_riverkm_needed_for_tidal(self):
        print("RiverKM needs to be specified for tidal applications.")

    def print_measure_not_active_for_checked_conditions(self):
        print("The measure is not active for any of the checked conditions.")

    def print_apply_filter(self):
        print("apply filter")

    def print_prepare_filter(self, step : int):
        print(f"prepare filter step {step}")

    def print_prepare(self):
        print("prepare")

    def print_buffer(self):
        print("buffer")

class AnalyserDflowfm():
    
    _logger : _AnalyserDflowfmLogger
    
    def __init__(self, display : bool, report : TextIO):
        self._logger = _AnalyserDflowfmLogger(display, report)
    
    def analyse(self, q_threshold, tstag, discharges, fraction_of_year, rsigma, slength, nwidth, ucrit, filenames, xykm, needs_tide, n_fields, tide_bc, old_zmin_zmax, outputdir, plotops):
        missing_data = False

        one_fm_filename, missing_data = self._get_first_fm_data_filename(q_threshold, discharges, rsigma, filenames, needs_tide, tide_bc)

        if missing_data:
            return missing_data, None

        self._logger.log_load_mesh()
        xn, yn, face_node_connectivity = self._get_xynode_connect(one_fm_filename)

        xykm_data = self._get_xykm_data(xykm, xn, yn, face_node_connectivity)

        if xykm is None and needs_tide:
            self._logger.print_riverkm_needed_for_tidal()
            return True, None

        missing_data, dzq = self._get_dzq(discharges, rsigma, ucrit, filenames, needs_tide, n_fields, tide_bc, missing_data, xykm_data.iface, xykm_data.dxi, xykm_data.dyi)

        if not missing_data:
            self._logger.log_char_bed_changes()

            if tstag > 0:
                dzq = (dzq[0], dzq[0], dzq[1], dzq[2])
                fraction_of_year = (fraction_of_year[0], tstag, fraction_of_year[1], fraction_of_year[2])
                rsigma = (rsigma[0], 1.0, rsigma[1], rsigma[2])

            # main_computation now returns new pointwise zmin and zmax
            dzgemi, dzmaxi, dzmini, dzbi = dfastmi.kernel.core.main_computation(
                dzq, fraction_of_year, rsigma
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
            sedimentation_data = dfastmi.batch.SedimentationVolume.comp_sedimentation_volume(xykm_data.xni, xykm_data.yni, xykm_data.sni, xykm_data.nni, xykm_data.FNCi, dzgemi, slength, nwidth, xykm_data.xykline, outputdir, plotops)

        return missing_data, OutputDataDflowfm(rsigma, one_fm_filename, xn, face_node_connectivity, dzq, dzgemi, dzmaxi, dzmini, dzbi, zmax_str, zmin_str, xykm_data, sedimentation_data)

    def _get_first_fm_data_filename(self,
        q_threshold: float,
        discharges: Vector,
        rsigma: Vector,
        filenames: Dict[Any, Tuple[str,str]],
        needs_tide: bool,
        tide_bc: Tuple[str, ...],
    ):
        missing_data = False
        one_fm_filename: Union[None, str] = None
        # determine the name of the first FM data file that will be used
        if 0 in filenames.keys(): # the keys are 0,1,2
            one_fm_filename = self._get_first_fm_data_filename_based_on_numbered_keys(discharges, filenames)
        else: # the keys are the conditions
            one_fm_filename, missing_data = self._get_first_fm_data_filename_based_on_conditions_keys(discharges, filenames, needs_tide, tide_bc, rsigma, q_threshold)

        if one_fm_filename is None:
            self._logger.print_measure_not_active_for_checked_conditions()
            missing_data = True

        return one_fm_filename, missing_data
    
    def _get_first_fm_data_filename_based_on_numbered_keys(self, discharges, filenames):
        for i in range(3):
            if discharges[i] is not None:
                return filenames[i][0]
        return None
    
    def _get_first_fm_data_filename_based_on_conditions_keys(self, discharges, filenames, needs_tide, tide_bc, rsigma, q_threshold):
        key: Union[Tuple[float, int], float]
        missing_data = False
        for i in range(len(discharges)):
            if not missing_data and discharges[i] is not None:
                key, q, t = self._get_condition_key(discharges, needs_tide, tide_bc, i)
                if rsigma[i] == 1 or discharges[i] <= q_threshold:
                    # no celerity or measure not active, so ignore field
                    pass
                elif key in filenames:
                    return filenames[key][0], missing_data
                else:
                    self._logger.report_missing_calculation_values(needs_tide, q, t)
                    missing_data = True
        return None, missing_data

    def _get_condition_key(self, discharges, needs_tide, tide_bc, i):
        q = discharges[i]
        if needs_tide:
            t = tide_bc[i]
            key = (q,t)
        else:
            t = None
            key = q
        return key,q,t

    def _get_xykm_data(self, xykm, xn, yn, face_node_connectivity):
        if xykm is None:
            # keep all nodes and faces
            keep = numpy.full(xn.shape, True)
            xni, yni, FNCi, iface, inode = dfastmi.batch.Face.filter_faces_by_node_condition(xn, yn, face_node_connectivity, keep)
            return XykmData(xykm, xni, yni, FNCi, iface, inode, xn.min(), xn.max(), yn.min(), yn.max(), None, None, None, None, None, None)
        else:
            dnmax = 3000.0
            self._logger.log_identify_region_of_interest()
            self._logger.print_buffer()
            xybuffer = xykm.buffer(dnmax)
            bbox = xybuffer.envelope.exterior
            self._logger.print_prepare()
            xybprep = shapely.prepared.prep(xybuffer)

            self._logger.print_prepare_filter(1)
            xmin = bbox.coords[0][0]
            xmax = bbox.coords[1][0]
            ymin = bbox.coords[0][1]
            ymax = bbox.coords[2][1]
            keep = (xn > xmin) & (xn < xmax) & (yn > ymin) & (yn < ymax)
            self._logger.print_prepare_filter(2)
            for i in range(xn.size):
                if keep[i] and not xybprep.contains(shapely.geometry.Point((xn[i], yn[i]))):
                    keep[i] = False

            self._logger.print_apply_filter()
            xni, yni, FNCi, iface, inode = dfastmi.batch.Face.filter_faces_by_node_condition(xn, yn, face_node_connectivity, keep)
            interest_region = numpy.zeros(face_node_connectivity.shape[0], dtype=numpy.int64)
            interest_region[iface] = 1

            xykline = numpy.array(xykm.coords)

            # project all nodes onto the line, obtain the distance along (sni) and normal (dni) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            xyline = xykline[:,:2]

            # project all nodes onto the line, obtain the distance along (sfi) and normal (nfi) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            self._logger.log_project()
            sni, nni = dfastmi.batch.Projection.project_xy_point_onto_line(xni, yni, xyline)
            sfi = dfastmi.batch.Face.face_mean(sni, FNCi)

            # determine chainage values of each cell
            self._logger.log_chainage()

            # determine line direction for each cell
            self._logger.log_direction()
            dxi, dyi = dfastmi.batch.Distance.get_direction(xyline, sfi)

            self._logger.log_done()

            return XykmData(xykm, xni, yni, FNCi, iface, inode, xmin, xmax, ymin, ymax, dxi, dyi, xykline, interest_region, sni, nni)

    def _get_dzq(self, discharges, rsigma, ucrit, filenames, needs_tide, n_fields, tide_bc, missing_data, iface, dxi, dyi):
        dzq = [None] * len(discharges)
        if 0 in filenames.keys(): # the keys are 0,1,2
            for i in range(3):
                if not missing_data and discharges[i] is not None:
                    dzq[i] = self._get_values_fm(discharges[i], ucrit, filenames[i], n_fields, dxi, dyi, iface)
                    if dzq[i] is None:
                        missing_data = True
                else:
                    dzq[i] = 0
        else: # the keys are the conditions
            for i in range(len(discharges)):
                if not missing_data and discharges[i] is not None:
                    key, q, t = self._get_condition_key(discharges, needs_tide, tide_bc, i)
                    if rsigma[i] == 1:
                        # no celerity, so ignore field
                        dzq[i] = 0
                    elif key in filenames.keys():
                        if t:
                            n_fields_request = n_fields
                        else:
                            n_fields_request = 1
                        dzq[i] = self._get_values_fm(q, ucrit, filenames[key], n_fields_request, dxi, dyi, iface)
                    else:
                        self._logger.report_missing_calculation_dzq_values(q, t)
                        missing_data = True
                else:
                    dzq[i] = 0
        return missing_data, dzq

    def _get_values_fm(
        self,
        q: float,
        ucrit: float,
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
        q : float
            Discharge value.
        ucrit : float
            Critical flow velocity.
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
        # reference file
        if filenames[0] == "":
            self._logger.report_file_not_specified(q)
            return None
        elif not os.path.isfile(filenames[0]):
            self._logger.report_file_not_found(filenames[0])
            return None

        # file with measure implemented
        if not os.path.isfile(filenames[1]):
            self._logger.report_file_not_found(filenames[1])
            return None

        ifld: Optional[int]
        if n_fields > 1:
            ustream_pos = numpy.zeros(dx.shape)
            ustream_neg = numpy.zeros(dx.shape)
            dzq_pos = numpy.zeros(dx.shape)
            dzq_neg = numpy.zeros(dx.shape)
            t_pos = numpy.zeros(dx.shape)
            t_neg = numpy.zeros(dx.shape)

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
        face_node_connectivity = GridOperations.read_fm_map(filename, "face_node_connectivity")
        if face_node_connectivity.mask.shape == ():
            # all faces have the same number of nodes; empty mask
            face_node_connectivity.mask = face_node_connectivity<0
        else:
            # varying number of nodes
            face_node_connectivity.mask = numpy.logical_or(face_node_connectivity.mask,face_node_connectivity<0)

        return xn, yn, face_node_connectivity