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

from typing import Any, Dict, TextIO

from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper


class XykmDataReporter:
    "This reporter reports events occuring in the XykmData class."

    def __init__(self, display: bool):
        """
        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        """
        self.display = display

    def print_apply_filter(self):
        print("apply filter")

    def print_prepare_filter(self, step: int):
        print(f"prepare filter step {step}")

    def print_prepare(self):
        print("prepare")

    def print_buffer(self):
        print("buffer")

    def report_done(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- done")

    def report_direction(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- direction")

    def report_chainage(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- chainage")

    def report_project(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- project")

    def report_identify_region_of_interest(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- identify region of interest")


class AnalyserDflowfmReporter:
    "This reporter reports events occuring in the AnalyserDflowfm class."

    xykm_data_logger: XykmDataReporter

    def __init__(self, display: bool, report: TextIO):
        """
        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        report : TextIO
            TextIO to report to.
        """
        self.display = display
        self.report = report
        self.xykm_data_logger = XykmDataReporter(display)

    def report_char_bed_changes(self):
        if self.display:
            ApplicationSettingsHelper.log_text("char_bed_changes")

    def report_load_mesh(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- load mesh")

    def report_identify_region_of_interest(self):
        if self.display:
            ApplicationSettingsHelper.log_text("-- identify region of interest")

    def report_missing_calculation_values(self, needs_tide, q, t):
        if needs_tide:
            ApplicationSettingsHelper.log_text(
                "no_file_specified_q_and_t", dict={"q": q, "t": t}, file=self.report
            )
        else:
            ApplicationSettingsHelper.log_text(
                "no_file_specified_q_only", dict={"q": q}, file=self.report
            )
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_missing_calculation_dzq_values(self, q, t):
        if t > 0:
            ApplicationSettingsHelper.log_text(
                "no_file_specified_q_and_t", dict={"q": q, "t": t}, file=self.report
            )
        else:
            ApplicationSettingsHelper.log_text(
                "no_file_specified_q_only", dict={"q": q}, file=self.report
            )
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_file_not_specified(self, q):
        ApplicationSettingsHelper.log_text(
            "no_file_specified", dict={"q": q}, file=self.report
        )
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_file_not_found(self, filename):
        ApplicationSettingsHelper.log_text(
            "file_not_found", dict={"name": filename}, file=self.report
        )
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def print_riverkm_needed_for_tidal(self):
        print("RiverKM needs to be specified for tidal applications.")

    def print_measure_not_active_for_checked_conditions(self):
        print("The measure is not active for any of the checked conditions.")


class ReporterDflowfmReporter:
    "This reporter reports events occuring in the ReporterDflowfm class."

    def __init__(
        self, display: bool, config: AConfigurationInitializerBase, report: TextIO
    ):
        """
        Arguments
        ---------
        display : bool
            Flag indicating text output to stdout.
        config : AConfigurationInitializerBase
            DTO with discharges, times, etc. for analysis
        report : TextIO
            Text stream for log file.
        """
        self.display = display
        self.config = config
        self.report = report

    def report_compute_initial_year_dredging(self):
        if self.display:
            ApplicationSettingsHelper.log_text("compute_initial_year_dredging")

    def report_writing_output(self):
        if self.display:
            ApplicationSettingsHelper.log_text("writing_output")

    def report_analysis_configuration(self):
        self._report_to_file("===")
        settings = {
            "branch": "branch_name",
            "reach": "reach_name",
            "q_threshold": self.config.q_threshold,
            "u_critical": self.config.ucrit,
        }
        self._report_to_file("analysis_settings", settings)

    def _report_to_file(self, resources_key: str, dict: Dict[str, Any] = {}):
        ApplicationSettingsHelper.log_text(resources_key, file=self.report, dict=dict)

    def print_sedimentation_and_erosion(self, sedimentation_data):
        if self.display:
            if sedimentation_data.sedvol.shape[1] > 0:
                print("Estimated sedimentation volume per area using 3 methods")
                print(
                    "                              Max:             Method 1:        Method 2:       "
                )
                print(
                    "                                sum area*dzeqa      sum_L dzeqa   L*W*avg(dzeqa)"
                )
                for i in range(sedimentation_data.sedvol.shape[1]):
                    print(
                        "Area{:3d} ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(
                            i + 1,
                            sedimentation_data.sedarea[i],
                            sedimentation_data.sedvol[0, i],
                            sedimentation_data.sedvol[1, i],
                            sedimentation_data.sedvol[2, i],
                        )
                    )
                print(
                    "Max                         : {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(
                        sedimentation_data.sedvol[0, :].max(),
                        sedimentation_data.sedvol[1, :].max(),
                        sedimentation_data.sedvol[2, :].max(),
                    )
                )
                print(
                    "Total   ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(
                        sedimentation_data.sedarea.sum(),
                        sedimentation_data.sedvol[0, :].sum(),
                        sedimentation_data.sedvol[1, :].sum(),
                        sedimentation_data.sedvol[2, :].sum(),
                    )
                )

            if (
                sedimentation_data.sedvol.shape[1] > 0
                and sedimentation_data.erovol.shape[1] > 0
            ):
                print("")

            if sedimentation_data.erovol.shape[1] > 0:
                print("Estimated erosion volume per area using 3 methods")
                print(
                    "                              Max:             Method 1:        Method 2:       "
                )
                print(
                    "                                sum area*dzeqa      sum_L dzeqa   L*W*avg(dzeqa)"
                )
                for i in range(sedimentation_data.erovol.shape[1]):
                    print(
                        "Area{:3d} ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(
                            i + 1,
                            sedimentation_data.eroarea[i],
                            sedimentation_data.erovol[0, i],
                            sedimentation_data.erovol[1, i],
                            sedimentation_data.erovol[2, i],
                        )
                    )
                print(
                    "Max                         : {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(
                        sedimentation_data.erovol[0, :].max(),
                        sedimentation_data.erovol[1, :].max(),
                        sedimentation_data.erovol[2, :].max(),
                    )
                )
                print(
                    "Total   ({:15.3f} m2): {:13.6f} m3 {:13.6f} m3 {:13.6f} m3".format(
                        sedimentation_data.eroarea.sum(),
                        sedimentation_data.erovol[0, :].sum(),
                        sedimentation_data.erovol[1, :].sum(),
                        sedimentation_data.erovol[2, :].sum(),
                    )
                )

    def print_replacing_coordinates(self):
        print("replacing coordinates")
