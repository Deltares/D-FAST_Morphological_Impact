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
from typing import Any, Dict

from pydantic import BaseModel
import dfastmi
from dfastmi.batch.ConfigurationInitializer import ConfigurationInitializer
from dfastmi.batch.DFastUtils import get_progloc
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.AReach import AReach
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.ConfigFileOperations import ConfigFileOperations
from PyQt5 import QtCore

from dfastmi.io.IBranch import IBranch

class DialogViewModel(QtCore.QObject):
    branch_changed = QtCore.pyqtSignal(str)
    reach_changed = QtCore.pyqtSignal(str)
    _reference_files : Dict[float,str] = {}
    _measure_files : Dict[float,str] = {}
    _model : DialogModel
    slength : str = ""


    def __init__(self, model: DialogModel):
        super().__init__()
        self._current_branch : Branch = model.rivers.branches[0]
        self._current_reach : AReach = self._current_branch.reaches[0]
        self._model = model
        self._initialize_qthreshold()
        self._initialize_ucritical()
        
         
    @property
    def current_branch(self) -> IBranch:
        return self._current_branch

    @current_branch.setter
    def current_branch(self, value):
        self._current_branch = value
        # Notify the view of the change
        self.branch_changed.emit(self._current_branch.name)
    
    @property
    def current_reach(self) -> AReach:
        return self._current_reach

    @current_reach.setter
    def current_reach(self, value):
        self._current_reach = value
        # Notify the view of the change
        self.reach_changed.emit(self._current_reach.name)
    
    @property
    def qthreshold(self) -> float:
        return self._model.qthreshold
    
    @qthreshold.setter
    def qthreshold(self, value):
        self._model.qthreshold = value
        
    @property
    def ucritical(self) -> float:
        return self._model.ucritical
    
    @ucritical.setter
    def ucritical(self, value):
        self._model.ucritical = value        

    @property
    def output_dir(self) -> str:
        return self._model.output_dir
    
    @output_dir.setter
    def output_dir(self, value):
        self._model.output_dir = value        
    
    @property
    def figure_dir(self) -> str:
        return self._model.figure_dir
    
    @figure_dir.setter
    def figure_dir(self, value):
        self._model.figure_dir = value
        
    @property
    def plotting(self) -> bool:
        return self._model.plotting
    
    @plotting.setter
    def plotting(self, value):
        self._model.plotting = value
        
    @property
    def save_plots(self) -> bool:
        return self._model.save_plots
    
    @save_plots.setter
    def save_plots(self, value):
        self._model.save_plots = value
        
    @property
    def close_plots(self) -> bool:
        return self._model.close_plots
    
    @close_plots.setter
    def close_plots(self, value):
        self._model.close_plots = value
        
    @property
    def reference_files(self) -> Dict[float, str]:
        return self._reference_files
    
    @property
    def measure_files(self) -> Dict[float, str]:
        return self._measure_files

    def get_configuration(self) -> ConfigParser:
         return self._model.get_configuration(self._current_branch, self._current_reach, self.reference_files, self.measure_files)

    def run_analysis(self) -> bool:
        return self._model.run_analysis()
    
    @property
    def manual_filename(self) -> str:
        progloc = get_progloc()
        filename = progloc.joinpath("dfastmi_usermanual.pdf")
        return str(filename)
    
    @property
    def report(self) -> str:
        return ApplicationSettingsHelper.get_filename("report.out")


    def gui_text(self, key: str, prefix: str = "gui_", dict: Dict[str, Any] = {}):
        """
        Query the global dictionary of texts for a single string in the GUI.

        This routine concatenates the prefix and the key to query the global
        dictionary of texts. It selects the first line of the text obtained and
        expands and placeholders in the string using the optional dictionary
        provided.

        Arguments
        ---------
        key : str
            The key string used to query the dictionary (extended with prefix).
        prefix : str
            The prefix used in combination with the key (default "gui_").
        dict : Dict[str, Any]
            A dictionary used for placeholder expansions (default empty).

        Returns
        -------
            The first line of the text in the dictionary expanded with the keys.
        """
        cstr = ApplicationSettingsHelper.get_text(prefix + key)
        application_setting = cstr[0].format(**dict)
        return application_setting
    
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

        self.current_branch = self._model.rivers.get_branch(branch_name)
        self.current_reach = self._current_branch.reaches[0]

    def _initialize_ucritical(self):
        if self.ucritical < self._current_reach.ucritical:
            self.ucritical = self._current_reach.ucritical

    def _initialize_qthreshold(self):
        if self.qthreshold < self._current_reach.qstagnant:
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
        Adjust the GUI for updated characteristic discharges.

        Arguments
        ---------
        None
        """
                
        try:                    
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
        config = self._model.get_configuration()
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
        self._model.load_configuration(filename)
                
        self._initialize_qthreshold()
        self._initialize_ucritical()
        self._update_qvalues()
        
        self._reference_files = {}
        self._measure_files = {}
        for section_name in self._model.config.sections():
            if section_name.lower().startswith('c') :
                section = self._model.config[section_name]
                cond_discharge = section.getfloat("Discharge", 0.0)
                self._reference_files[cond_discharge] = section.get("Reference", "")
                self._measure_files[cond_discharge] = section.get("WithMeasure", "")
        
        self.current_branch = self._model.rivers.get_branch(self._model.branch_name)
        self.current_reach = self.current_branch.get_reach(self._model.reach_name)
        
        return True
    
    def check_configuration(self) -> bool :
        return self._model.check_configuration(self.current_branch, self.current_reach, self.reference_files, self.measure_files)
        
    