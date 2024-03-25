from pathlib import Path
from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.batch.SedimentationVolume import comp_sedimentation_volume
from dfastmi.kernel.core import main_computation, dzq_from_du_and_h
from dfastmi.batch.DflowfmLoggers import AnalyserDflowfmLogger
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm
from dfastmi.batch.XykmData import XykmData
from dfastmi.io.GridOperations import GridOperations
from dfastmi.kernel.typehints import Vector, BoolVector
from shapely.geometry.linestring import LineString

import numpy
import os
from typing import Any, Dict, Optional, TextIO, Tuple, Union

class AnalyserDflowfm():
    """
    Class that analyses the Dflowfm data.
    """
    
    _logger : AnalyserDflowfmLogger
    
    def __init__(self, display : bool, report : TextIO, old_zmin_zmax : bool, outputdir : Path, config : AConfigurationInitializerBase):
        """
        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        report : TextIO
            Text stream for log file.
        needs_tide : bool
            Specifies whether the tidal boundary is needed.
        old_zmin_zmax : bool
            Specifies the minimum and maximum should follow old or new definition.
        outputdir : Path
            Path of output directory.
        config : AConfigurationInitializerBase
            DTO with discharges, times, etc. for analysis
        """
        self._logger = AnalyserDflowfmLogger(display, report)
        
        self._needs_tide = config.needs_tide
        self._q_threshold = config.q_threshold
        self._tstag = config.tstag
        self._discharges = config.discharges
        self._time_fractions_of_the_year = config.time_fractions_of_the_year
        self._rsigma = config.rsigma
        self._slength = config.slength
        self._ucrit = config.ucrit
        self._n_fields = config.n_fields
        self._tide_bc = config.tide_bc
        
        self._old_zmin_zmax = old_zmin_zmax
        self._outputdir = outputdir
    
    def analyse(self, 
                nwidth : float,
                filenames : Dict[Any, Tuple[str,str]],
                xykm : LineString,
                plotops : Dict
                ) -> Tuple[bool, OutputDataDflowfm]:
        """
        Perform analysis based on D-Flow FM data.
        Read data from D-Flow FM output files and perform analysis.

        Arguments
        ---------
        nwidth : float
            normal width of the reach.
        filenames : Dict[Any, Tuple[str,str]]
            Dictionary of the names of the data file containing the simulation
            results to be processed. The conditions (discharge, wave conditions,
            ...) are the key in the dictionary. Per condition a tuple of two file
            names is given: a reference file and a file with measure.
        xykm : shapely.geometry.linestring.LineString
            Original river chainage line.
        plotops : Dict
            Dictionary of plot settings

        Returns
        -------
        success : bool
            Flag indicating whether analysis could be carried out.
        Output data : OutputDataDflowfm
            DTO with the data which is needed to create a report.
        """
        rsigma = self._rsigma
        one_fm_filename, missing_data = self._get_first_fm_data_filename(filenames)

        if missing_data:
            return missing_data, None

        self._logger.log_load_mesh()
        xn, yn, face_node_connectivity = self._get_xynode_connect(one_fm_filename)

        xykm_data = self._get_xykm_data(xykm, xn, yn, face_node_connectivity)

        if xykm is None and self._needs_tide:
            self._logger.print_riverkm_needed_for_tidal()
            return True, None

        missing_data, dzq = self._get_dzq(filenames, missing_data, xykm_data.iface, xykm_data.dxi, xykm_data.dyi)

        if not missing_data:
            self._logger.log_char_bed_changes()
            
            dzq = self._determine_dzq(dzq)
            time_fraction_of_year = self._get_time_fractions_of_the_year()
            rsigma = self._get_rsigma()
            
            # main_computation now returns new pointwise zmin and zmax
            dzgemi, dzmaxi, dzmini, dzbi = main_computation(dzq, time_fraction_of_year, rsigma)

            if self._old_zmin_zmax:
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
            sedimentation_data = comp_sedimentation_volume(xykm_data.xni, xykm_data.yni, xykm_data.sni, xykm_data.nni, xykm_data.face_node_connectivity_index, dzgemi, self._slength, nwidth, xykm_data.xykline, self._outputdir, plotops)

        return missing_data, OutputDataDflowfm(rsigma, one_fm_filename, xn, face_node_connectivity, dzq, dzgemi, dzmaxi, dzmini, dzbi, zmax_str, zmin_str, xykm_data, sedimentation_data)

    def _determine_dzq(self, dzq : numpy.ndarray) -> numpy.ndarray:
        if self._tstag > 0:
            return (dzq[0], dzq[0], dzq[1], dzq[2])
        return dzq
    
    def _get_time_fractions_of_the_year(self) -> Vector:
        if self._tstag > 0:
            return (self._time_fractions_of_the_year[0], self._tstag, self._time_fractions_of_the_year[1], self._time_fractions_of_the_year[2])
        return self._time_fractions_of_the_year
            
    def _get_rsigma(self) -> Vector:
        if self._tstag > 0:
            return (self._rsigma[0], 1.0, self._rsigma[1], self._rsigma[2])
        return self._rsigma

    def _get_first_fm_data_filename(self, filenames: Dict[Any, Tuple[str,str]]) -> Tuple[str, bool]:
        missing_data = False
        one_fm_filename: Union[None, str] = None
        # determine the name of the first FM data file that will be used
        if 0 in filenames.keys(): # the keys are 0,1,2
            one_fm_filename = self._get_first_fm_data_filename_based_on_numbered_keys(filenames)
        else: # the keys are the conditions
            one_fm_filename, missing_data = self._get_first_fm_data_filename_based_on_conditions_keys(filenames)

        if one_fm_filename is None:
            self._logger.print_measure_not_active_for_checked_conditions()
            missing_data = True

        return one_fm_filename, missing_data
    
    def _get_first_fm_data_filename_based_on_numbered_keys(self, filenames : Dict[Any, Tuple[str,str]]) -> Optional[str]:
        for i in range(3):
            if self._discharges[i] is not None:
                return filenames[i][0]
        return None
    
    def _get_first_fm_data_filename_based_on_conditions_keys(self, filenames : Dict[Any, Tuple[str,str]]) -> Tuple[str, bool]:
        key: Union[Tuple[float, int], float]
        missing_data = False
        for i in range(len(self._discharges)):
            if not missing_data and self._discharges[i] is not None:
                key, q, t = self._get_condition_key(self._discharges, self._tide_bc, i)
                if self._rsigma[i] == 1 or self._discharges[i] <= self._q_threshold:
                    # no celerity or measure not active, so ignore field
                    pass
                elif key in filenames:
                    return filenames[key][0], missing_data
                else:
                    self._logger.report_missing_calculation_values(self._needs_tide, q, t)
                    missing_data = True
        return None, missing_data

    def _get_xykm_data(self, xykm : LineString, xn : numpy.ndarray, yn : numpy.ndarray, face_node_connectivity : numpy.ndarray) -> XykmData:
        xykm_data = XykmData(self._logger.xykm_data_logger)
        xykm_data.initialize_data(xykm, xn, yn, face_node_connectivity)
        return xykm_data

    def _get_dzq(self,
                 filenames: Dict[Any, Tuple[str,str]],
                 missing_data : bool,
                 iface : numpy.ndarray,
                 dxi : numpy.ndarray,
                 dyi : numpy.ndarray
                 ) -> Tuple[bool, numpy.ndarray]:
        if 0 in filenames.keys(): # the keys are 0,1,2
            return self._get_dzq_based_on_numbered_keys(missing_data, filenames, dxi, dyi, iface)
        else: # the keys are the conditions
            return self._get_dzq_based_on_conditions_keys(missing_data, filenames, dxi, dyi, iface)
    
    def _get_dzq_based_on_numbered_keys(self,
                                        missing_data : bool,
                                        filenames: Dict[Any, Tuple[str,str]],
                                        dxi : numpy.ndarray,
                                        dyi : numpy.ndarray,
                                        iface : numpy.ndarray
                                        ) -> Tuple[bool, numpy.ndarray]:
        dzq = [None] * len(self._discharges)
        for i in range(3):
                if not missing_data and self._discharges[i] is not None:
                    dzq[i] = self._get_values_fm(self._discharges[i], filenames[i], self._n_fields, dxi, dyi, iface)
                    if dzq[i] is None:
                        missing_data = True
                else:
                    dzq[i] = 0
        return missing_data, dzq
    
    def _get_dzq_based_on_conditions_keys(self,
                                          missing_data : bool,
                                          filenames : Dict[Any, Tuple[str,str]],
                                          dxi : numpy.ndarray,
                                          dyi : numpy.ndarray,
                                          iface : numpy.ndarray
                                          ) -> Tuple[bool, numpy.ndarray]:
        dzq = [None] * len(self._discharges)
        for i in range(len(self._discharges)):
            if not missing_data and self._discharges[i] is not None:
                key, q, t = self._get_condition_key(self._discharges, self._tide_bc, i)
                if self._rsigma[i] == 1:
                    # no celerity, so ignore field
                    dzq[i] = 0
                elif key in filenames.keys():
                    if t:
                        n_fields_request = self._n_fields
                    else:
                        n_fields_request = 1
                    dzq[i] = self._get_values_fm(q, filenames[key], n_fields_request, dxi, dyi, iface)
                else:
                    self._logger.report_missing_calculation_dzq_values(q, t)
                    missing_data = True
            else:
                dzq[i] = 0
        return missing_data, dzq
    
    def _get_condition_key(self, discharges : Vector, tide_bc : Tuple[str, ...], i : int):
        q = discharges[i]
        if self._needs_tide:
            t = tide_bc[i]
            key = (q,t)
        else:
            t = None
            key = q
        return key,q,t

    def _get_values_fm(
        self,
        q: float,
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

            dzq1 = dzq_from_du_and_h(umag0, h0, umag1, self._ucrit, default=0.0)

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