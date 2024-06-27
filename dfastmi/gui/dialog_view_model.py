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
import traceback

# ViewModel
from configparser import ConfigParser
from typing import Dict, Tuple

from PyQt5.QtCore import QObject, pyqtSignal

import dfastmi
from dfastmi.batch.DFastUtils import get_progloc
from dfastmi.config.ConfigFileOperations import ConfigFileOperations
from dfastmi.config.ConfigurationInitializer import ConfigurationInitializer
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.AReach import AReach
from dfastmi.io.Branch import Branch
from dfastmi.io.IBranch import IBranch
from dfastmi.kernel.typehints import FilenameDict


class DialogViewModel(QObject):
    """Represents the ViewModel for the dialog interface."""

    branch_changed = pyqtSignal(str)
    reach_changed = pyqtSignal(AReach)
    ucritical_changed = pyqtSignal(float)
    qthreshold_changed = pyqtSignal(float)
    slength_changed = pyqtSignal(str)
    make_plot_changed = pyqtSignal(bool)
    save_plot_changed = pyqtSignal(bool)
    figure_dir_changed = pyqtSignal(str)
    output_dir_changed = pyqtSignal(str)
    analysis_exception = pyqtSignal(str, str)
    reference_files_changed = pyqtSignal(str, float, str)
    measure_files_changed = pyqtSignal(str, float, str)
    _reference_files: FilenameDict = {}
    _measure_files: FilenameDict = {}
    _ucrit_cache: Dict[Tuple[Branch, AReach], float] = {}
    _qthreshold_cache: Dict[Tuple[Branch, AReach], float] = {}
    model: DialogModel
    slength: str = ""

    def __init__(self, model: DialogModel):
        """
        Initializes the DialogViewModel.

        Arguments:
            model (DialogModel): The DialogModel to associate with the ViewModel.
        """
        super().__init__()
        self._current_branch: Branch = model.rivers.branches[0]
        self._current_reach: AReach = self._current_branch.reaches[0]
        self._qthreshold: float = 0.0
        self.model = model
        self._initialize_qthreshold()
        self._initialize_ucritical()

    @property
    def current_branch(self) -> IBranch:
        """
        IBranch: The current branch.
        """
        return self._current_branch

    @current_branch.setter
    def current_branch(self, value):
        """
        Setter for the current branch.
        After set notify the view of the change.

        Arguments:
            value (IBranch): The branch to set.
        """
        if value is self._current_branch:
            return

        self._current_branch = value
        # Notify the view of the change
        self.branch_changed.emit(self.current_branch.name)

    @property
    def current_reach(self) -> AReach:
        """
        AReach: The current reach.
        """
        return self._current_reach

    @current_reach.setter
    def current_reach(self, value):
        """
        Setter for the current reach.
        After set notify the view of the change.

        Arguments:
            value (AReach): The reach to set.
        """
        if value is self._current_reach:
            return

        self._current_reach = value
        self._initialize_qthreshold()
        self._initialize_ucritical()
        self._update_slength()
        # Notify the view of the change
        self.reach_changed.emit(self.current_reach)

    @property
    def ucritical(self) -> float:
        """
        The current critical (minimum) velocity [m/s] for sediment transport.
        """
        return self._ucritical

    @ucritical.setter
    def ucritical(self, value: float):
        """
        Setter for the current critical (minimum) velocity [m/s] for sediment transport.
        After set notify the view of the change.

        Arguments:
            value (float): The critical (minimum) velocity [m/s] for sediment transport to set.
        """
        if self._ucritical == value:
            return

        self._ucritical = value
        self._ucrit_cache[(self.current_branch, self.current_reach)] = value

        # Notify the view of the change
        self.ucritical_changed.emit(self.ucritical)

    @property
    def qthreshold(self) -> float:
        """
        The current threshold discharge.
        """
        return self._qthreshold

    @qthreshold.setter
    def qthreshold(self, value: float):
        """
        Setter for the current threshold discharge.
        After set notify the view of the change.

        Arguments:
            value (float): The threshold discharge to set.
        """
        if self._qthreshold == value:
            return

        value = max(value, self.current_reach.qstagnant)
        self._qthreshold = value
        self._qthreshold_cache[(self.current_branch, self.current_reach)] = value

        self._update_slength()
        # Notify the view of the change
        self.qthreshold_changed.emit(self.qthreshold)

    @property
    def reference_files(self) -> FilenameDict:
        """
        FilenameDict: The reference files.
        """
        return self._reference_files

    @property
    def measure_files(self) -> FilenameDict:
        """
        FilenameDict: The measurement files.
        """
        return self._measure_files

    @property
    def make_plot(self) -> bool:
        """
        Get of the make plot setting.
        """
        return self.model.plotting

    @make_plot.setter
    def make_plot(self, value: bool):
        """
        Set of the make plot setting.
        """
        self.model.plotting = value
        self.make_plot_changed.emit(value)
        if self.save_plot:
            self.save_plot_changed.emit(value)

    @property
    def save_plot(self) -> bool:
        """
        Get of the save plot setting.
        """
        return self.model.save_plots

    @save_plot.setter
    def save_plot(self, value: bool):
        """
        Set of the save plot setting.
        """
        self.model.save_plots = value
        self.save_plot_changed.emit(value)

    @property
    def output_dir(self) -> str:
        """
        Get the output directory.
        """
        return self.model.output_dir

    @output_dir.setter
    def output_dir(self, value: str):
        """
        Set the output directory.
        """
        self.model.output_dir = value
        self.output_dir_changed.emit(value)

    @property
    def figure_dir(self) -> str:
        """
        Get the figure directory.
        """
        return self.model.figure_dir

    @figure_dir.setter
    def figure_dir(self, value: str):
        """
        Set the figure directory.
        """
        self.model.figure_dir = value
        self.figure_dir_changed.emit(value)

    def get_configuration(self) -> ConfigParser:
        """
        Get the (loaded) DFastMI configuration.

        Returns:
            ConfigParser: The configuration.
        """
        return self.model.get_configuration(
            self.current_branch,
            self.current_reach,
            self.reference_files,
            self.measure_files,
            self.ucritical,
            self.qthreshold,
        )

    def run_analysis(self) -> bool:
        """
        Run the analysis.

        Return
        ---------
        succes : bool
            If the analysis could be run successfully.
            We call batch_mode_core which can throw and log an exception.
            If thrown, analysis has failed.
        """
        try:
            run_config = self.model.get_configuration(
                self.current_branch,
                self.current_reach,
                self.reference_files,
                self.measure_files,
                self.ucritical,
                self.qthreshold,
            )
            return dfastmi.batch.core.batch_mode_core(
                self.model.rivers, False, run_config, gui=True
            )
        except:
            stackTrace = traceback.format_exc()
            # Notify the view of the change
            self.analysis_exception.emit(
                "A run-time exception occurred. Press 'Show Details...' for the full stack trace.",
                stackTrace,
            )

        return False

    @property
    def manual_filename(self) -> str:
        """
        Get the manual filename.

        Returns:
            str: The manual filename.
        """
        progloc = get_progloc()
        filename = progloc.joinpath("dfastmi_usermanual.pdf")
        return str(filename)

    @property
    def report(self) -> str:
        """
        Get the report filename.

        Returns:
            str: The report filename.
        """
        return ApplicationSettingsHelper.get_filename("report.out")

    def updated_branch(self, branch_name: str) -> None:
        """
        Adjust the GUI for updated branch selection.

        Arguments
        ---------
        branch_name : str
            Newly selected branch.
        """
        self.current_branch = self.model.rivers.get_branch(branch_name)
        if self.current_reach.name != self.current_branch.reaches[0].name:
            self.current_reach = self.current_branch.reaches[0]

    def _initialize_ucritical(self):
        """
        Initialize the critical velocity.
        """
        self._ucritical = 0.0
        if (self.current_branch, self.current_reach) in self._ucrit_cache:
            self.ucritical = self._ucrit_cache[
                (self.current_branch, self.current_reach)
            ]
        else:
            self.ucritical = self.current_reach.ucritical

    def _initialize_qthreshold(self):
        """
        Initialize the threshold discharge.
        """
        self._qthreshold = 0.0
        if (self.current_branch, self.current_reach) in self._qthreshold_cache:
            self.qthreshold = max(
                self._qthreshold_cache[(self.current_branch, self.current_reach)],
                self.current_reach.qstagnant,
            )
        else:
            self.qthreshold = self.current_reach.qstagnant

    def updated_reach(self, reach_name: str) -> None:
        """
        Adjust the GUI for updated reach selection.

        Arguments
        ---------
        reach_name : str
            Newly selected reach.
        """
        if reach_name:
            self.current_reach = self.current_branch.get_reach(reach_name)

    def _update_slength(self) -> None:
        """
        Update the sedimentation length.

        Arguments:
            None
        """

        try:
            if self.current_reach.auto_time:
                _, time_mi = ConfigurationInitializer.set_times(
                    self.current_reach.hydro_q,
                    self.current_reach.qfit,
                    self.current_reach.qstagnant,
                    self.qthreshold,
                )
            else:
                time_fractions_of_the_year = (
                    ConfigurationInitializer.get_time_fractions_of_the_year(
                        self.current_reach.hydro_t
                    )
                )
                time_mi = ConfigurationInitializer.calculate_time_mi(
                    self.qthreshold,
                    self.current_reach.hydro_q,
                    time_fractions_of_the_year,
                )
            celerity = ConfigurationInitializer.get_bed_celerity(
                self.current_reach, self.current_reach.hydro_q
            )
            slength = dfastmi.kernel.core.estimate_sedimentation_length(
                time_mi, celerity
            )
            self.slength = str(int(slength))
        except:
            self.slength = "---"

        self.slength_changed.emit(self.slength)

    def save_configuration(self, filename: str) -> None:
        """
        Open a configuration file and update the GUI accordingly.

        This routines opens the specified configuration file and updates the GUI
        to reflect it contents.

        Arguments
        ---------
        filename : str
            Name of the configuration file to be saved.

        """
        config = self.model.get_configuration(
            self.current_branch,
            self.current_reach,
            self.reference_files,
            self.measure_files,
            self.ucritical,
            self.qthreshold,
        )
        ConfigFileOperations.save_configuration_file(filename, config)

    def load_configuration(self, filename: str) -> bool:
        """
        Open a configuration file and update the GUI accordingly.

        This routines opens the specified configuration file and updates the GUI
        to reflect it contents.

        Arguments
        ---------
        filename : str
            Name of the configuration file to be opened.
        """
        self.model.load_configuration(filename)

        branch = self.model.rivers.get_branch(self.model.branch_name)
        if not branch:
            branch = self.model.rivers.branches[0]
        self.current_branch = branch

        reach = self.current_branch.get_reach(self.model.reach_name)
        if not reach:
            reach = self.current_branch.reaches[0]
        self.current_reach = reach

        self._qthreshold_cache[(self.current_branch, self.current_reach)] = (
            self.model.qthreshold
        )
        self._initialize_qthreshold()

        self._ucrit_cache[(self.current_branch, self.current_reach)] = (
            self.model.ucritical
        )
        self._initialize_ucritical()
        self._update_slength()
        self._initialize_reference_and_measure()

        self.make_plot = self.model.plotting
        self.save_plot = self.model.save_plots
        self.figure_dir = self.model.figure_dir
        self.output_dir = self.model.output_dir

        return True

    def _initialize_reference_and_measure(self):
        self._reference_files = {}
        self._measure_files = {}
        for section_name in self.model.config.sections():
            if section_name.lower().startswith("c"):
                section = self.model.config[section_name]
                cond_discharge = section.getfloat("Discharge", 0.0)

                self._reference_files[cond_discharge] = section.get("Reference", "")
                self.reference_files_changed.emit(
                    "reference", cond_discharge, self._reference_files[cond_discharge]
                )

                self._measure_files[cond_discharge] = section.get("WithMeasure", "")
                self.measure_files_changed.emit(
                    "with_measure", cond_discharge, self._measure_files[cond_discharge]
                )

    def check_configuration(self) -> bool:
        """
        Check the validity of the current configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        return self.model.check_configuration(
            self.current_branch,
            self.current_reach,
            self.reference_files,
            self.measure_files,
            self.ucritical,
            self.qthreshold,
        )
