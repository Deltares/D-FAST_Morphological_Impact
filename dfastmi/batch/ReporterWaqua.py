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
from dfastmi.batch.OutputDataWaqua import OutputDataWaqua
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations

class ReporterWaqua():
    """
    Class writes the report for waqua.
    """
    def __init__(self, output_dir):
        """
        Init of the reporter.

        Arguments
        ---------
        outputdir : str
            Name of the output directory.
        """
        self.output_dir = output_dir
        self.avgdzb = "avgdzb.out"
        self.maxdzb = "maxdzb.out"
        self.mindzb = "mindzb.out"

    def write_report(self, output_data : OutputDataWaqua):
        """
        Writes the reports to the retrieved output files and location based on the outputdir.

        Arguments
        ---------
        output_data : OutputDataWaqua
            Output data that is to be writen to the related files.
        """
        avgdzb_file = self._get_file_location(self.avgdzb)
        DataTextFileOperations.write_simona_box(avgdzb_file, output_data.data_zgem, output_data.first_min_velocity_m, output_data.first_min_velocity_n)

        maxdzb_file = self._get_file_location(self.maxdzb)
        DataTextFileOperations.write_simona_box(maxdzb_file, output_data.data_zmax, output_data.first_min_velocity_m, output_data.first_min_velocity_n)

        mindzb_file = self._get_file_location(self.mindzb)
        DataTextFileOperations.write_simona_box(mindzb_file, output_data.data_zmin, output_data.first_min_velocity_m, output_data.first_min_velocity_n)

    def _get_file_location(self, output_file_name : str) -> str:
        return str(Path(self.output_dir).joinpath(ApplicationSettingsHelper.get_filename(output_file_name)))