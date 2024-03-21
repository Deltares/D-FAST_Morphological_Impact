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
# ViewModel
from configparser import ConfigParser
import os
from typing import Any, Dict
import dfastmi
from dfastmi.batch.ConfigurationInitializer import ConfigurationInitializer
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.AReach import AReach
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.ConfigFileOperations import ConfigFileOperations
from dfastmi.io.FileUtils import FileUtils
from PyQt5 import QtCore



class DialogViewModel(QtCore.QObject):
    branch_changed = QtCore.pyqtSignal(str)
    reach_changed = QtCore.pyqtSignal(str)
    plot_flag : bool = False
    save_flag : bool = False

    def __init__(self, model: DialogModel):
        super().__init__()        
        self._current_branch : Branch = model.rivers.branches[0]
        self._current_reach : AReach = self._current_branch.reaches[0]
        self.slength : str = ""
        self.model = model

    # def load_configuration(self, filename: str) -> None:
    #     self.model.load_configuration(filename)
        
    @property
    def current_branch(self):
        return self._current_branch

    @current_branch.setter
    def current_branch(self, value):
        self._current_branch = value
        # Notify the view of the change
        self.branch_changed.emit(self._current_branch.name)
    
    @property
    def current_reach(self):
        return self._current_reach

    @current_reach.setter
    def current_reach(self, value):
        self._current_reach = value
        # Notify the view of the change
        self.reach_changed.emit(self._current_reach.name)
    
    
    def get_configuration(self) -> ConfigParser:
         return self.model.get_configuration(self._current_branch, self._current_reach)

    def run_analysis(self, config: ConfigParser) -> None:
        self.model.run_analysis(config, self._current_branch, self._current_reach)
    
    @property
    def manual_filename(self) -> str:
        progloc = FileUtils.get_progloc()
        filename = progloc + os.path.sep + "dfastmi_usermanual.pdf"
        return filename


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
        self.current_branch = self.model.rivers.get_branch(branch_name)
        self.current_reach = self._current_branch.reaches[0]
        self.update_qvalues()
        # reach = dialog["reach"]
        # reach.clear()    
        # reach.addItems([reach.name for reach in self.model.rivers.branches[ibranch].reaches])

        # dialog["qloc"].setText(self.model.branches[ibranch].qlocation)


    def updated_reach(self, reach_name: str) -> None:
        """
        Adjust the GUI for updated reach selection.

        Arguments
        ---------
        reach_name : str
            Newly selected reach.
        """
        if reach_name:
            self.current_reach = self._current_branch.get_reach(reach_name)
            # q_stagnant = reach.qstagnant
            # dialog["qthr"].setText(str(q_stagnant))
            # ucritical = reach.ucritical
            # dialog["ucrit"].setText(str(ucritical))
            self.update_qvalues()


    def update_qvalues(self) -> None:
        """
        Adjust the GUI for updated characteristic discharges.

        Arguments
        ---------
        None
        """
                
        try:        
            q_threshold = float(self._current_reach.qstagnant)
            time_fractions_of_the_year = ConfigurationInitializer.get_time_fractions_of_the_year(self._current_reach.hydro_t)
            time_mi = ConfigurationInitializer.calculate_time_mi(q_threshold, self._current_reach.hydro_q, time_fractions_of_the_year)
            celerity = ConfigurationInitializer.get_bed_celerity(self._current_reach, self._current_reach.hydro_q)
            slength = dfastmi.kernel.core.estimate_sedimentation_length(time_mi, celerity)
            #dialog["slength"].setText("{:.0f}".format(slength))
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
        config = self.model.get_configuration()
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
        try:
            config = ConfigFileOperations.load_configuration_file(filename)
        except:
            if filename != "dfastmi.cfg":
                return False                
            return True
    
        section = config["General"]
        self._current_branch = self.model.rivers.get_branch(section["Branch"])
        #dialog["branch"].setCurrentText(section["Branch"])
        #ibranch = dialog["branch"].currentIndex()
        #dialog["reach"].setCurrentText(section["Reach"])
        #ireach = dialog["reach"].currentIndex()
        #reach = rivers.branches[ibranch].reaches[ireach]
        self._current_reach = self._current_branch.get_reach(section["Reach"])

        # dialog["qthr"].setText(
        #     section.get("Qthreshold", str(reach.qstagnant))
        # )

        # dialog["ucrit"].setText(
        #     section.get("Ucrit", str(reach.ucritical))
        # )
        
        # dialog["outputDir"].setText(
        #     section.get("OutputDir", "output")
        # )
        # dialog["makePlotsEdit"].setChecked(
        #     str_to_bool(section.get("Plotting", "false"))
        # )
        # dialog["savePlotsEdit"].setChecked(
        #     str_to_bool(section.get("SavePlots", "false"))
        # )
        # dialog["figureDirEdit"].setText(
        #     section.get("FigureDir", "figure")
        # )
        # dialog["closePlotsEdit"].setChecked(
        #     str_to_bool(section.get("ClosePlots", "false"))
        # )
        self.update_qvalues()
        
        hydro_q = self._current_reach.hydro_q
        for i in range(len(hydro_q)):
            prefix = str(i)+"_"
            cond = "C{}".format(i+1)
            if cond in config.keys():
                cond_section = config[cond]
                file1 = cond_section.get("Reference", "")
                file2 = cond_section.get("WithMeasure", "")
            else:
                file1 = ""
                file2 = ""
            # dialog[prefix+"file1"].setText(file1)
            # dialog[prefix+"file2"].setText(file2)
        
        return True
    
    # Define other methods to prepare data for the View and handle user interactions