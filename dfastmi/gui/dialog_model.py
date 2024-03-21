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
# Define other methods for interacting with the model data and performing business logic
from configparser import ConfigParser, SectionProxy
from typing import Optional
import dfastmi
from dfastmi.io.AReach import AReach
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.ConfigFileOperations import ConfigFileOperations, check_configuration


class DialogModel:
    config : ConfigParser = None
    section : SectionProxy = None
    def __init__(self, rivers_configuration: RiversObject, config_file: Optional[str] = None):
        self.rivers = rivers_configuration
        
        if config_file:
            self.load_configuration(config_file)


    def load_configuration(self, filename: str) -> None:
        try:
            self.config = ConfigFileOperations.load_configuration_file(filename)
        except:
            if filename != "dfastmi.cfg":
                return False                
            return True
    
        self.section = self.config["General"]

    def run_analysis(self, config: ConfigParser, branch: Branch, reach:AReach) -> bool:
        # Logic to run analysis based on configuration
        """
        Run the D-FAST Morphological Impact analysis based on settings in the GUI.

        Arguments
        ---------
        None
        """
        config = self.get_configuration(branch, reach)
        if check_configuration(self.rivers, config):
            try:
                success = dfastmi.batch.core.batch_mode_core(self.rivers, False, config)
            except:
                success = False
            report = ApplicationSettingsHelper.get_filename("report.out")
            if success:
                #showMessage(gui_text("end_of_analysis", dict={"report": report},))
                True
            else:
                False
                #showError(gui_text("error_during_analysis", dict={"report": report},))
        else:
            False
            #showError(gui_text("analysis_config_incomplete",))

    
    
    def get_configuration(self, branch : Branch, reach: AReach) -> ConfigParser:
        """
        Extract a configuration from the GUI.

        Arguments
        ---------
        None

        Returns
        -------
        config : Optional[configparser.ConfigParser]
            Configuration for the D-FAST Morphological Impact analysis.
        """
        config = ConfigParser()
        config.optionxform = str
        config.add_section("General")
        config["General"]["Version"] = "2.0"
        config["General"]["Branch"] = branch.name
        config["General"]["Reach"] = reach.name
        config["General"]["Qthreshold"] = reach.qstagnant
        config["General"]["Ucrit"] = reach.ucritical
        # config["General"]["OutputDir"] = dialog["outputDir"].text()
        # config["General"]["Plotting"] = str(dialog["makePlotsEdit"].isChecked())
        # config["General"]["SavePlots"] = str(dialog["savePlotsEdit"].isChecked())
        # config["General"]["FigureDir"] = dialog["figureDirEdit"].text()
        # config["General"]["ClosePlots"] = str(dialog["closePlotsEdit"].isChecked())

        # loop over conditions cond = "C1", "C2", ...
        hydro_q = reach.hydro_q
        for i in range(len(hydro_q)):
            cond = "C{}".format(i+1)
            config.add_section(cond)
            prefix = str(i)+"_"
            #config[cond]["Discharge"] = dialog[prefix+"qval"].text()
            #config[cond]["Reference"] = dialog[prefix+"file1"].text()
            #config[cond]["WithMeasure"] = dialog[prefix+"file2"].text()
        
        return config
