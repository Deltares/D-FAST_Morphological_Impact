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

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple, Union

import numpy
from shapely.geometry.linestring import LineString

from dfastmi.batch.DflowfmReporters import AnalyserDflowfmReporter
from dfastmi.batch.Face import face_mean
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.batch.SedimentationVolume import comp_sedimentation_volume
from dfastmi.batch.XykmData import XykmData
from dfastmi.config.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.io.OutputFile import OutputFile
from dfastmi.io.OutputFileFactory import OutputFileFactory
from dfastmi.kernel.core import dzq_from_du_and_h, main_computation
from dfastmi.kernel.typehints import Vector


class AnalyserDflowfm:
    """
    Class that analyses the Dflowfm data.
    """

    @property
    def missing_data(self) -> bool:
        """
        Flag indicating whether data was missing after analysis.
        """
        return self._missing_data

    _reporter: AnalyserDflowfmReporter

    def __init__(
        self,
        display: bool,
        report: TextIO,
        old_zmin_zmax: bool,
        outputdir: Path,
        config: AConfigurationInitializerBase,
    ):
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
        self._reporter = AnalyserDflowfmReporter(display, report)

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

        self._missing_data = False

    def analyse(
        self,
        nwidth: float,
        filenames: Dict[Any, Tuple[str, str]],
        xykm: LineString,
        plotting_options: PlotOptions,
    ) -> OutputDataDflowfm:
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
            names is given: a reference file and a file with interventions to the river.
        xykm : shapely.geometry.linestring.LineString
            Original river chainage line.
        plotting_options : PlotOptions
            Class containing the plot options.

        Returns
        -------
        Output data : OutputDataDflowfm
            DTO with the data which is needed to create a report.
            None will be returned if data is missing.
        """
        rsigma = self._rsigma
        one_fm_filename = self._get_first_fm_data_filename(filenames)

        if self._missing_data:
            return None

        self._reporter.report_load_mesh()
        output_file = OutputFileFactory.generate(one_fm_filename)
        xn = output_file.node_x_coordinates
        yn = output_file.node_y_coordinates
        face_node_connectivity = self._get_face_node_connectivity(output_file)

        xykm_data = self._get_xykm_data(xykm, xn, yn, face_node_connectivity)

        if xykm is None and self._needs_tide:
            self._reporter.print_riverkm_needed_for_tidal()
            self._missing_data = True
            return None

        dzq = self._get_dzq(filenames, xykm_data.iface, xykm_data.dxi, xykm_data.dyi)

        if not self._missing_data:
            self._reporter.report_char_bed_changes()

            dzq = self._determine_dzq(dzq)
            time_fraction_of_year = self._get_time_fractions_of_the_year()
            rsigma = self._get_rsigma()

            # main_computation now returns new pointwise zmin and zmax
            dzgemi, dzmaxi, dzmini, dzbi = main_computation(
                dzq, time_fraction_of_year, rsigma
            )

            minimum_bedlevel_value = self._get_minimum_bedlevel_value(dzmini, dzbi)
            maximum_bedlevel_value = self._get_maximum_bedlevel_value(dzmaxi, dzbi)
            maximum_bedlevel_messsage = self._get_maximum_bedlevel_message()
            minimum_bedlevel_message = self._get_minimum_bedlevel_message()

        sedimentation_data = None
        if xykm is not None:
            sedimentation_data = comp_sedimentation_volume(
                xykm_data,
                dzgemi,
                self._slength,
                nwidth,
                self._outputdir,
                plotting_options,
            )

        return OutputDataDflowfm(
            rsigma,
            one_fm_filename,
            xn,
            face_node_connectivity,
            dzq,
            dzgemi,
            maximum_bedlevel_value,
            minimum_bedlevel_value,
            dzbi,
            maximum_bedlevel_messsage,
            minimum_bedlevel_message,
            xykm_data,
            sedimentation_data,
        )

    def _determine_dzq(self, dzq: numpy.ndarray) -> numpy.ndarray:
        if self._tstag > 0:
            return (dzq[0], 0, dzq[1], dzq[2])
        return dzq

    def _get_time_fractions_of_the_year(self) -> Vector:
        if self._tstag > 0:
            return (
                self._time_fractions_of_the_year[0],
                self._tstag,
                self._time_fractions_of_the_year[1],
                self._time_fractions_of_the_year[2],
            )
        return self._time_fractions_of_the_year

    def _get_rsigma(self) -> Vector:
        if self._tstag > 0:
            return (self._rsigma[0], 1.0, self._rsigma[1], self._rsigma[2])
        return self._rsigma

    def _get_maximum_bedlevel_value(
        self, dzmaxi: numpy.ndarray, dzbi: List[numpy.ndarray]
    ) -> numpy.ndarray:
        if self._old_zmin_zmax:
            return dzbi[0]
        return dzmaxi

    def _get_minimum_bedlevel_value(
        self, dzmini: numpy.ndarray, dzbi: List[numpy.ndarray]
    ) -> numpy.ndarray:
        if self._old_zmin_zmax:
            return dzbi[1]
        return dzmini

    def _get_maximum_bedlevel_message(self) -> str:
        if self._old_zmin_zmax:
            return "maximum bed level change after flood without dredging"
        return "maximum value of bed level change without dredging"

    def _get_minimum_bedlevel_message(self) -> str:
        if self._old_zmin_zmax:
            return "minimum bed level change after low flow without dredging"
        return "minimum value of bed level change without dredging"

    def _get_first_fm_data_filename(self, filenames: Dict[Any, Tuple[str, str]]) -> str:
        one_fm_filename: Union[None, str] = None
        self._missing_data = False

        # determine the name of the first FM data file that will be used
        if 0 in filenames.keys():  # the keys are 0,1,2
            one_fm_filename = self._get_first_fm_data_filename_based_on_numbered_keys(
                filenames
            )
        else:  # the keys are the conditions
            one_fm_filename = self._get_first_fm_data_filename_based_on_conditions_keys(
                filenames
            )

        if one_fm_filename is None:
            self._reporter.print_intervention_not_active_for_checked_conditions()
            self._missing_data = True

        return one_fm_filename

    def _get_first_fm_data_filename_based_on_numbered_keys(
        self, filenames: Dict[Any, Tuple[str, str]]
    ) -> Optional[str]:
        for i in range(3):
            if (
                self._discharges[i] is not None
                and self._discharges[i] > self._q_threshold
            ):
                return filenames[i][0]
        return None

    def _get_first_fm_data_filename_based_on_conditions_keys(
        self, filenames: Dict[Any, Tuple[str, str]]
    ) -> Optional[str]:
        key: Union[Tuple[float, int], float]
        self._missing_data = False
        for i in range(len(self._discharges)):
            if not self._missing_data and self._discharges[i] is not None:
                key, q, t = self._get_condition_key(self._discharges, self._tide_bc, i)
                if self._rsigma[i] == 1 or self._discharges[i] <= self._q_threshold:
                    # no celerity or intervention not active, so ignore field
                    pass
                elif key in filenames:
                    return filenames[key][0]
                else:
                    self._reporter.report_missing_calculation_values(
                        self._needs_tide, q, t
                    )
                    self._missing_data = True
        return None

    def _get_xykm_data(
        self,
        xykm: LineString,
        xn: numpy.ndarray,
        yn: numpy.ndarray,
        face_node_connectivity: numpy.ndarray,
    ) -> XykmData:
        xykm_data = XykmData(self._reporter.xykm_data_logger)
        xykm_data.initialize_data(xykm, xn, yn, face_node_connectivity)
        return xykm_data

    def _get_dzq(
        self,
        filenames: Dict[Any, Tuple[str, str]],
        iface: numpy.ndarray,
        dxi: numpy.ndarray,
        dyi: numpy.ndarray,
    ) -> numpy.ndarray:
        if 0 in filenames.keys():  # the keys are 0,1,2
            return self._get_dzq_based_on_numbered_keys(filenames, dxi, dyi, iface)
        else:  # the keys are the conditions
            return self._get_dzq_based_on_conditions_keys(filenames, dxi, dyi, iface)

    def _get_dzq_based_on_numbered_keys(
        self,
        filenames: Dict[Any, Tuple[str, str]],
        dxi: numpy.ndarray,
        dyi: numpy.ndarray,
        iface: numpy.ndarray,
    ) -> numpy.ndarray:
        dzq = [None] * len(self._discharges)
        for i in range(3):
            if self._discharges[i] is None:
                # ignore period
                dzq[i] = 0
            elif self._discharges[i] <= self._q_threshold:
                # intervention inactive, so zero-effect for this period
                dzq[i] = numpy.zeros_like(iface, dtype=float)
            else:
                dzq[i] = self._get_values_fm(
                    self._discharges[i], filenames[i], self._n_fields, dxi, dyi, iface
                )
                if dzq[i] is None:
                    self._missing_data = True
        return dzq

    def _get_dzq_based_on_conditions_keys(
        self,
        filenames: Dict[Any, Tuple[str, str]],
        dxi: numpy.ndarray,
        dyi: numpy.ndarray,
        iface: numpy.ndarray,
    ) -> numpy.ndarray:
        dzq = [None] * len(self._discharges)
        for i in range(len(self._discharges)):
            if self._discharges[i] is None:
                # ignore period
                dzq[i] = 0
            else:
                key, q, t = self._get_condition_key(self._discharges, self._tide_bc, i)
                if q <= self._q_threshold:
                    # intervention inactive, so zero-effect for this period
                    dzq[i] = numpy.zeros_like(iface, dtype=float)
                elif key in filenames.keys():
                    if t:
                        n_fields_request = self._n_fields
                    else:
                        n_fields_request = 1
                    dzq[i] = self._get_values_fm(
                        q, filenames[key], n_fields_request, dxi, dyi, iface
                    )
                else:
                    self._reporter.report_missing_calculation_dzq_values(q, t)
                    self._missing_data = True
        return dzq

    def _get_condition_key(self, discharges: Vector, tide_bc: Tuple[str, ...], i: int):
        q = discharges[i]
        if self._needs_tide:
            t = tide_bc[i]
            key = (q, t)
        else:
            t = None
            key = q
        return key, q, t

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
            Names of the reference simulation file and file with the implemented intervention.
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
            self._reporter.report_file_not_specified(q)
            return None
        elif not os.path.isfile(filenames[0]):
            self._reporter.report_file_not_found(filenames[0])
            return None

        # file with intervention implemented
        if not os.path.isfile(filenames[1]):
            self._reporter.report_file_not_found(filenames[1])
            return None

        output_file1 = OutputFileFactory.generate(filenames[0])
        output_file2 = OutputFileFactory.generate(filenames[1])

        grids_match, i1, i2 = self._map_grids(output_file1, output_file2, iface)

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
            u1 = output_file1.x_velocity(time_index_from_last=ifld)[iface]
            v1 = output_file1.y_velocity(time_index_from_last=ifld)[iface]
            umag1 = numpy.sqrt(u1**2 + v1**2)
            h1 = output_file1.water_depth(time_index_from_last=ifld)[iface]

            # data with intervention
            u2 = output_file2.x_velocity(time_index_from_last=ifld)
            v2 = output_file2.y_velocity(time_index_from_last=ifld)
            umag2 = numpy.sqrt(u2**2 + v2**2)

            # map intervention data to reference mesh
            if not grids_match:
                umag_temp = umag2[i2]
                umag2 = umag1.copy()
                umag2[i1] = umag_temp

            # compute the equilibrium bed level change
            dzq2 = dzq_from_du_and_h(umag1, h1, umag2, self._ucrit, default=0.0)

            # in case of tides: determine values for maximum ebb and flood conditions
            if n_fields > 1:
                ustream = u1 * dx + v1 * dy

                # positive flow -> flow in downstream direction -> biggest flow in positive direction during peak ebb flow
                ipos = ustream > 0.0
                t_pos[ipos] = t_pos[ipos] + 1

                ipos = ustream > ustream_pos
                ustream_pos[ipos] = ustream[ipos]
                dzq_pos[ipos] = dzq2[ipos]

                # negative flow -> flow in upstream direction -> biggest flow in negative direction during peak flood flow
                ineg = ustream < 0.0
                t_neg[ineg] = t_neg[ineg] + 1

                ineg = ustream < ustream_neg
                ustream_neg[ineg] = ustream[ineg]
                dzq_neg[ineg] = dzq2[ineg]

        # in case of tides: average over ebb and flood conditions
        if n_fields > 1:
            dzq = (t_pos * dzq_pos + t_neg * dzq_neg) / numpy.maximum(t_pos + t_neg, 1)
        else:
            dzq = dzq2

        return dzq

    def _map_grids(
        self,
        output_file1,
        output_file2,
        iface: numpy.ndarray,
    ) -> (bool, numpy.ndarray, numpy.ndarray):
        """
        Check whether the grids on two output files match, and return mapping.

        Arguments
        ---------
        output_file1 : OutputFile
            Reference simulation file.
        output_file2 : OutputFile
            Simulation file with intervention.
        iface : numpy.ndarray
            Array containing the subselection of cells.

        Returns
        -------
        grids_match : bool
            Flag indicating whether the two grids match.
        i1 : numpy.ndarray
            Matching indices in mesh1 (empty if grids_match = True).
        i2 : numpy.ndarray
            Matching indices in mesh2 (empty if grids_match = True).
        """
        xn1 = output_file1.node_x_coordinates
        yn1 = output_file1.node_y_coordinates
        FNC1 = self._get_face_node_connectivity(output_file1)[iface]

        xn2 = output_file2.node_x_coordinates
        yn2 = output_file2.node_y_coordinates
        FNC2 = self._get_face_node_connectivity(output_file2)

        grids_match = (
            numpy.array_equal(FNC1, FNC2)
            and numpy.array_equal(xn1, xn2)
            and numpy.array_equal(yn1, yn2)
        )

        if grids_match:
            i1 = numpy.zeros(0)
            i2 = numpy.zeros(0)
        else:
            xyf1 = face_mean(xn1, FNC1) + 1j * face_mean(yn1, FNC1)
            xyf2 = face_mean(xn2, FNC2) + 1j * face_mean(yn2, FNC2)
            _, i1, i2 = numpy.intersect1d(xyf1, xyf2, return_indices=True)

        return grids_match, i1, i2

    def _get_face_node_connectivity(self, output_file: OutputFile) -> numpy.ndarray:
        face_node_connectivity = output_file.face_node_connectivity

        if face_node_connectivity.mask.shape == ():
            # all faces have the same number of nodes; empty mask
            face_node_connectivity.mask = face_node_connectivity < 0
        else:
            # varying number of nodes
            face_node_connectivity.mask = numpy.logical_or(
                face_node_connectivity.mask, face_node_connectivity < 0
            )

        return face_node_connectivity
