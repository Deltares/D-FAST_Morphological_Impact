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
This file is part of D-FAST Morphological Impact: https://github.com/Deltares/D-FAST_Morphological_Impact
"""

from typing import Optional, List, Union, Tuple, TextIO
from dfastmi.kernel.core import Vector, BoolVector
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations

import os
import numpy
import dfastmi.kernel.core
import dfastmi.plotting

def analyse_and_report_waqua(
    display: bool,
    report: TextIO,
    reduced_output: bool,
    reach: str,
    q_location: str,
    tstag: float,
    Q: Vector,
    apply_q: BoolVector,
    T: Vector,
    rsigma: Vector,
    slength: float,
    ucrit: float,
    old_zmin_zmax: bool,
    outputdir: str
) -> bool:
    """
    Perform analysis based on WAQUA data.

    Read data from samples files exported from WAQUA simulations, perform
    analysis and write the results to three SIMONA boxfiles.

    Arguments
    ---------
    display : bool
        Flag indicating text output to stdout.
    report : TextIO
        Text stream for log file.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    reach : str
        Name of the reach.
    q_location : str
        Name of the location at which the discharge is
    tstag : float
        Number of days that the river is stagnant.
    Q : Vector
        Array of discharges; one for each forcing condition.
    apply_q : BoolVector
        A tuple of 3 flags indicating whether each value should be used or not.
    T : Vector
        Fraction of year represented by each forcing condition.
    rsigma : Vector
        Array of relaxation factors; one per forcing condition.
    slength : float
        The expected yearly impacted sedimentation length.
    ucrit : float
        Critical flow velocity [m/s].
    old_zmin_zmax : bool
        Specifies the minimum and maximum should follow old or new definition.
    outputdir : str
        Name of the output directory.

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out.
    """
    waqua = AnalyzerWaqua()
    success, output_data = waqua.analyze(display, report, reduced_output, tstag, Q, apply_q, T, rsigma, ucrit, old_zmin_zmax)

    if success:
        waqua_reporter = ReporterWaqua(outputdir)
        waqua_reporter.write_report(output_data)

    return success

class OutputDataWaqua():
    def __init__(self, firstm, firstn, data_zgem, data_zmax, data_zmin):
        self.firstm = firstm
        self.firstn = firstn
        self.data_zgem = data_zgem
        self.data_zmax = data_zmax
        self.data_zmin = data_zmin

class ReporterWaqua():
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.avgdzb = "avgdzb.out"
        self.maxdzb = "maxdzb.out"
        self.mindzb = "mindzb.out"
    
    def write_report(self, output_data : OutputDataWaqua):
        avgdzb_file = self._get_file_location(self.avgdzb)
        DataTextFileOperations.write_simona_box(avgdzb_file, output_data.data_zgem, output_data.firstm, output_data.firstn)
        
        maxdzb_file = self._get_file_location(self.maxdzb)
        DataTextFileOperations.write_simona_box(maxdzb_file, output_data.data_zmax, output_data.firstm, output_data.firstn)
        
        mindzb_file = self._get_file_location(self.mindzb)
        DataTextFileOperations.write_simona_box(mindzb_file, output_data.data_zmin, output_data.firstm, output_data.firstn)
        
    def _get_file_location(self, file_name : str):
        return self.output_dir + os.sep + ApplicationSettingsHelper.get_filename(file_name)

class AnalyzerWaqua():
    def analyze(self, display, report, reduced_output, tstag, Q, apply_q, T, rsigma, ucrit, old_zmin_zmax):
           
        success, dzq, firstm, firstn = self._get_output_values(display, report, reduced_output, Q, apply_q, ucrit,)
        output_data = self._calculate_output_data(display, tstag, T, rsigma, old_zmin_zmax, dzq, firstm, firstn)      
               
        return success, output_data

    def _calculate_output_data(self, display, tstag, T, rsigma, old_zmin_zmax, dzq, firstm, firstn):
        if display:
            ApplicationSettingsHelper.log_text("char_bed_changes")
                
        if tstag > 0:
            dzq = [dzq[0], 0.0, dzq[1], dzq[2]]
            T = (T[0], tstag, T[1], T[2])
            rsigma = (rsigma[0], 1.0, rsigma[1], rsigma[2])
            
            # main_computation now returns new pointwise zmin and zmax
        data_zgem, data_zmax, data_zmin, dzb = dfastmi.kernel.core.main_computation(
                dzq, T, rsigma
            )
        
        if old_zmin_zmax:
                # get old zmax and zmin
            data_zmax = dzb[0]
            data_zmin = dzb[1]
                
        output_data = OutputDataWaqua(firstm, firstn, data_zgem, data_zmax, data_zmin)
        return output_data

    def _get_output_values(self, display, report, reduced_output, Q, apply_q, ucrit):
        success = True
        first_discharge = True
        dzq : List[Optional[Union[float, numpy.ndarray]]]
        dzq = [None] * len(Q)
        for i in range(3):
            if success and apply_q[i]:
                if first_discharge:
                    dzq[i], firstm, firstn = self._get_values_waqua3(i+1, Q[i], ucrit, display, report, reduced_output)
                    first_discharge = False
                else:
                    dzq[i], _, _ = self._get_values_waqua3(i+1, Q[i], ucrit, display, report, reduced_output)
                if dzq[i] is None:
                    success = False
            else:
                dzq[i] = 0.0
        return success,dzq,firstm,firstn

    def _get_values_waqua3(
        self, stage: int, q: float, ucrit: float, display: bool, report, reduced_output: bool
    ) -> Tuple[numpy.ndarray, int, int]:
        """
        Read data files exported from WAQUA for the specified stage, and return equilibrium bed level change and minimum M and N.

        Arguments
        ---------
        stage : int
            Discharge level (1, 2 or 3).
        q : float
            Discharge value.
        ucrit : float
            Critical flow velocity.
        display : bool
            Flag indicating text output to stdout.
        report : TextIO
            Text stream for log file.
        reduced_output : bool
            Flag to indicate whether WAQUA output should be reduced to the area of
            interest only.

        Returns
        -------
        dzq : numpy.ndarray
            Array containing equilibrium bed level change.
        firstm : int
            Minimum M index read (0 if reduced_output is False).
        firstn : int
            Minimum N index read (0 if reduced_output is False).
        """
        cblok = str(stage)
        if display:
            ApplicationSettingsHelper.log_text("input_xyz", dict={"stage": stage, "q": q})
            ApplicationSettingsHelper.log_text("---")
            ApplicationSettingsHelper.log_text("")

        discriptions = ApplicationSettingsHelper.get_text("file_descriptions")
        quantities = ["velocity-zeta.001", "waterdepth-zeta.001", "velocity-zeta.002"]
        files = []
        for i in range(3):
            if display:
                ApplicationSettingsHelper.log_text("input_xyz_name", dict={"name": discriptions[i]})
            cifil = "xyz_" + quantities[i] + ".Q" + cblok + ".xyz"
            if display:
                print(cifil)
            if not os.path.isfile(cifil):
                ApplicationSettingsHelper.log_text("file_not_found", dict={"name": cifil})
                ApplicationSettingsHelper.log_text("file_not_found", dict={"name": cifil}, file=report)
                ApplicationSettingsHelper.log_text("end_program", file=report)
                return numpy.array([]), 0, 0
            else:
                if display:
                    ApplicationSettingsHelper.log_text("input_xyz_found", dict={"name": cifil})
            files.extend([cifil])
            if display:
                ApplicationSettingsHelper.log_text("")

        if display:
            ApplicationSettingsHelper.log_text("input_xyz_read", dict={"stage": stage})
            
        u0temp = DataTextFileOperations.read_waqua_xyz(files[0], cols=(2, 3, 4))
        m = u0temp[:, 1].astype(int) - 1
        n = u0temp[:, 2].astype(int) - 1
        u0temp = u0temp[:, 0]
        h0temp = DataTextFileOperations.read_waqua_xyz(files[1])
        u1temp = DataTextFileOperations.read_waqua_xyz(files[2])

        if reduced_output:
            firstm = min(m)
            firstn = min(n)
        else:
            firstm = 0
            firstn = 0
            
        szm = max(m) + 1 - firstm
        szn = max(n) + 1 - firstn
        szk = szm * szn
        k = szn * m + n
        
        u0 = numpy.zeros([szk])
        h0 = numpy.zeros([szk])
        u1 = numpy.zeros([szk])

        u0[k] = u0temp
        h0[k] = h0temp
        u1[k] = u1temp

        sz = [szm, szn]
        u0 = u0.reshape(sz)
        h0 = h0.reshape(sz)
        u1 = u1.reshape(sz)

        dzq = dfastmi.kernel.core.dzq_from_du_and_h(u0, h0, u1, ucrit)
        
        if display:
            ApplicationSettingsHelper.log_text("---")
            
        return dzq, firstm, firstn