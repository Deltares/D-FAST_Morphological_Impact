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

from typing import List, Optional, TextIO, Tuple, Union
import os
import numpy

import dfastmi.kernel.core
from dfastmi.batch.OutputDataWaqua import OutputDataWaqua
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
from dfastmi.kernel.typehints import Vector

class _WaquaLogger():
    def __init__(self, display : bool, report : TextIO):
        self.display = display
        self.report = report
    
    def log_closing_statement_input(self):
        if self.display:
            ApplicationSettingsHelper.log_text("")

    def log_input_file_found(self, cifil : str):
        if self.display:
            ApplicationSettingsHelper.log_text("input_xyz_found", dict={"name": cifil})

    def log_input_name(self, discriptions : List[str], i : int):
        if self.display:
            ApplicationSettingsHelper.log_text("input_xyz_name", dict={"name": discriptions[i]})

    def log_input_initialization(self, stage : int, discharge_value : float):
        if self.display:
            ApplicationSettingsHelper.log_text("input_xyz", dict={"stage": stage, "q": discharge_value})
            ApplicationSettingsHelper.log_text("---")
            ApplicationSettingsHelper.log_text("")

    def log_file_not_found(self, cifil : str):
        ApplicationSettingsHelper.log_text("file_not_found", dict={"name": cifil})
        ApplicationSettingsHelper.log_text("file_not_found", dict={"name": cifil}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)
        
    def log_input_stage(self, stage : int):
        if self.display:
            ApplicationSettingsHelper.log_text("input_xyz_read", dict={"stage": stage})
            
    def log_dividers(self):
        if self.display:
            ApplicationSettingsHelper.log_text("---")
            
    def log_char_bed_changes(self):
        if self.display:
            ApplicationSettingsHelper.log_text("char_bed_changes")
            
    def print_cifil(self, cifil : str):
        if self.display:
            print(cifil)


class AnalyserWaqua():
    """
    Class that analyses information for waqua.
    """
    _logger : _WaquaLogger

    def __init__(self, display, report, reduced_output, tstag, discharges, apply_q, ucrit, old_zmin_zmax):
        """
        Init of the analyser.

        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        report : TextIO
            Text stream for log file.
        reduced_output : bool
            Flag to indicate whether WAQUA output should be reduced to the area of
            interest only.
        tstag : float
            Number of days that the river is stagnant.
        discharges : Vector
            Array of discharges; one for each forcing condition.
        apply_q : BoolVector
            A tuple of 3 flags indicating whether each value should be used or not.
        ucrit : float
            Critical flow velocity [m/s].
        old_zmin_zmax : bool
            Specifies the minimum and maximum should follow old or new definition.
        """
        self._logger = _WaquaLogger(display, report)
        self.reduced_output = reduced_output
        self.tstag = tstag
        self.discharges = discharges
        self.apply_q = apply_q
        self.ucrit = ucrit
        self.old_zmin_zmax = old_zmin_zmax

    def analyse(self, fraction_of_year : Vector, rsigma : Vector) -> OutputDataWaqua:
        """
        Read data from samples files exported from WAQUA simulations and performanalysis.

        Arguments
        ---------
        fraction_of_year : Vector
            Fraction of year represented by each forcing condition.
        rsigma : Vector
            Array of relaxation factors; one per forcing condition.

        Returns
        -------
        output_data : OutputDataWaqua
            data used to generate a report.
        """
        dzq, first_min_velocity_m, first_min_velocity_n = self._process_files()
        output_data = self._calculate_output_data(fraction_of_year, rsigma, dzq, first_min_velocity_m, first_min_velocity_n)
        return output_data

    def _process_files(self) -> Tuple[numpy.ndarray, int, int]:
        first_discharge = True
        dzq : List[Optional[Union[float, numpy.ndarray]]]
        dzq = [None] * len(self.discharges)
        for i in range(3):
            if self.apply_q[i]:
                stage = i+1
                discharge_value = self.discharges[i]

                files = self._search_files(stage, discharge_value)
                if not files:
                    dzq[i] = numpy.array([])
                    u0temp = None
                else:
                    u0temp, h0temp, u1temp = self._read_files(stage, files)
                    dzq[i] = self._calculate_waqua_bedlevel_values(u0temp, h0temp, u1temp)

                if first_discharge:
                    first_min_velocity_m, first_min_velocity_n = self.get_first_minimal_velocities(files, u0temp)
                    first_discharge = False
            else:
                dzq[i] = 0.0
        return dzq, first_min_velocity_m, first_min_velocity_n

    def get_first_minimal_velocities(self, files : list, u0temp : numpy.ndarray) -> Tuple[int, int]:
        if not files:
            first_min_velocity_m = 0
            first_min_velocity_n = 0
        else:
            first_min_velocity_m = self._calculate_waqua_values_minimal_velocity_m(u0temp)
            first_min_velocity_n = self._calculate_waqua_values_minimal_velocity_n(u0temp)

        return first_min_velocity_m,first_min_velocity_n

    def _search_files(self, stage: int, discharge_value: float) -> list:
        cblok = str(stage)

        self._logger.log_input_initialization(stage, discharge_value)

        discriptions = ApplicationSettingsHelper.get_text("file_descriptions")
        quantities = ["velocity-zeta.001", "waterdepth-zeta.001", "velocity-zeta.002"]
        files = []
        for i in range(3):
            self._logger.log_input_name(discriptions, i)
            cifil = "xyz_" + quantities[i] + ".Q" + cblok + ".xyz"
            self._logger.print_cifil(cifil)

            if not os.path.isfile(cifil):
                self._logger.log_file_not_found(cifil)
                return []
            else:
                self._logger.log_input_file_found(cifil)
            files.extend([cifil])
            self._logger.log_closing_statement_input()

        return files

    def _read_files(self, stage : int, files : list) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
        self._logger.log_input_stage(stage)

        u0temp = DataTextFileOperations.read_waqua_xyz(files[0], cols=(2, 3, 4))
        h0temp = DataTextFileOperations.read_waqua_xyz(files[1])
        u1temp = DataTextFileOperations.read_waqua_xyz(files[2])

        return u0temp, h0temp, u1temp

    def _calculate_waqua_values_minimal_velocity_m(self, velocity_u0temp : numpy.ndarray) -> int:
        if self.reduced_output:
            m = velocity_u0temp[:, 1].astype(int) - 1
            return min(m)
        else:
            return 0

    def _calculate_waqua_values_minimal_velocity_n(self, velocity_u0temp : numpy.ndarray) -> int:
        if self.reduced_output:
            n = velocity_u0temp[:, 2].astype(int) - 1
            return min(n)
        else:
            return 0

    def _calculate_waqua_bedlevel_values(self, u0temp : numpy.ndarray, h0temp : numpy.ndarray, u1temp : numpy.ndarray) -> numpy.ndarray:
        m = u0temp[:, 1].astype(int) - 1
        n = u0temp[:, 2].astype(int) - 1
        u0temp_first_column  = u0temp[:, 0]

        min_velocity_m = self._calculate_waqua_values_minimal_velocity_m(u0temp)
        min_velocity_n = self._calculate_waqua_values_minimal_velocity_n(u0temp)

        szm = max(m) + 1 - min_velocity_m
        szn = max(n) + 1 - min_velocity_n
        szk = szm * szn
        k = szn * m + n

        u0 = numpy.zeros([szk])
        h0 = numpy.zeros([szk])
        u1 = numpy.zeros([szk])

        u0[k] = u0temp_first_column
        h0[k] = h0temp
        u1[k] = u1temp

        sz = [szm, szn]
        u0 = u0.reshape(sz)
        h0 = h0.reshape(sz)
        u1 = u1.reshape(sz)

        dzq = dfastmi.kernel.core.dzq_from_du_and_h(u0, h0, u1, self.ucrit)

        self._logger.log_dividers()

        return dzq

    def _calculate_output_data(self, fraction_of_year : Vector, rsigma : Vector, dzq : numpy.ndarray, first_min_velocity_m : int, first_min_velocity_n : int) -> OutputDataWaqua:
        self._logger.log_char_bed_changes()

        if self.tstag > 0:
            dzq = [dzq[0], 0.0, dzq[1], dzq[2]]
            fraction_of_year = (fraction_of_year[0], self.tstag, fraction_of_year[1], fraction_of_year[2])
            rsigma = (rsigma[0], 1.0, rsigma[1], rsigma[2])

        # main_computation now returns new pointwise zmin and zmax
        data_zgem, data_zmax, data_zmin, dzb = dfastmi.kernel.core.main_computation(
                dzq, fraction_of_year, rsigma
            )

        if self.old_zmin_zmax:
            # get old zmax and zmin
            data_zmax = dzb[0]
            data_zmin = dzb[1]

        output_data = OutputDataWaqua(first_min_velocity_m, first_min_velocity_n, data_zgem, data_zmax, data_zmin)
        return output_data