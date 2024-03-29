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
# ViewModel
from configparser import ConfigParser
from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal
import dfastmi
from dfastmi.batch.ConfigurationInitializer import ConfigurationInitializer
from dfastmi.batch.DFastUtils import get_progloc
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.AReach import AReach
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.ConfigFileOperations import ConfigFileOperations


from dfastmi.io.IBranch import IBranch

class DialogViewModel(QObject):
    """ Represents the ViewModel for the dialog interface. """
    branch_changed = pyqtSignal(str)
    reach_changed = pyqtSignal(str)
    _reference_files : Dict[float,str] = {}
    _measure_files : Dict[float,str] = {}
    model : DialogModel
    slength : str = ""

    def __init__(self, model: DialogModel):
        """
        Initializes the DialogViewModel.

        Arguments:
            model (DialogModel): The DialogModel to associate with the ViewModel.
        """
        super().__init__()
        self._current_branch : Branch = model.rivers.branches[0]
        self._current_reach : AReach = self._current_branch.reaches[0]
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
        self._current_branch = value
        # Notify the view of the change
        self.branch_changed.emit(self._current_branch.name)
    
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
        self._current_reach = value
        # Notify the view of the change
        self.reach_changed.emit(self._current_reach.name)
        
    @property
    def reference_files(self) -> Dict[float, str]:
        """
            Dict[float, str]: The reference files.
        """
        return self._reference_files
    
    @property
    def measure_files(self) -> Dict[float, str]:
        """
            Dict[float, str]: The measurement files.
        """
        return self._measure_files

    def get_configuration(self) -> ConfigParser:
        """
        Get the (loaded) DFastMI configuration.

        Returns:
            ConfigParser: The configuration.
        """
        return self.model.get_configuration(self._current_branch, self._current_reach, self.reference_files, self.measure_files)

    def run_analysis(self) -> bool:
        """
        Run the analysis.

        Returns:
            bool: True if analysis is successful, False otherwise.
        """
        return self.model.run_analysis()
    
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
        self._initialize_qthreshold()

        self._initialize_ucritical()
        self._update_qvalues()

        self.current_branch = self.model.rivers.get_branch(branch_name)
        self.current_reach = self._current_branch.reaches[0]

    def _initialize_ucritical(self):
        """
        Initialize the critical velocity.
        """
        if self.model.ucritical < self._current_reach.ucritical:
            self.ucritical = self._current_reach.ucritical

    def _initialize_qthreshold(self):
        """
        Initialize the threshold discharge.
        """
        if self.model.qthreshold < self._current_reach.qstagnant:
            self.qthreshold = self._current_reach.qstagnant

        
    def updated_reach(self, reach_name: str) -> None:
        """
        Adjust the GUI for updated reach selection.

        Arguments
        ---------
        reach_name : str
            Newly selected reach.
        """
        if reach_name:
            self._update_qvalues()
            self.current_reach = self._current_branch.get_reach(reach_name)
            

    def _update_qvalues(self) -> None:
        """
        Update the GUI for characteristic discharges.

        Arguments:
            None
        """
                
        try:
            if self.current_reach.auto_time:
                _, time_mi = ConfigurationInitializer.set_times(self._current_reach.hydro_q, self.current_reach.qfit, self.current_reach.qstagnant, self.qthreshold)
            else:
                time_fractions_of_the_year = ConfigurationInitializer.get_time_fractions_of_the_year(self._current_reach.hydro_t)
                time_mi = ConfigurationInitializer.calculate_time_mi(self.qthreshold, self._current_reach.hydro_q, time_fractions_of_the_year)
            celerity = ConfigurationInitializer.get_bed_celerity(self._current_reach, self._current_reach.hydro_q)
            slength = dfastmi.kernel.core.estimate_sedimentation_length(time_mi, celerity)
            self.slength = "{:.0f}".format(slength)
        except:
            self.slength = "---"
    
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
        config = self.model.get_configuration(self.current_branch, self.current_reach, self.reference_files, self.measure_files)
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
                
        self._initialize_qthreshold()
        self._initialize_ucritical()
        self._update_qvalues()
        
        self._reference_files = {}
        self._measure_files = {}
        for section_name in self.model.config.sections():
            if section_name.lower().startswith('c') :
                section = self.model.config[section_name]
                cond_discharge = section.getfloat("Discharge", 0.0)
                self._reference_files[cond_discharge] = section.get("Reference", "")
                self._measure_files[cond_discharge] = section.get("WithMeasure", "")
        
        self.current_branch = self.model.rivers.get_branch(self.model.branch_name)
        self.current_reach = self.current_branch.get_reach(self.model.reach_name)
        
        return True
    
    def check_configuration(self) -> bool:
        """
        Check the validity of the current configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        return self.model.check_configuration(self.current_branch, self.current_reach, self.reference_files, self.measure_files)
