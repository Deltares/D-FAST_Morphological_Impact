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
from configparser import ConfigParser, SectionProxy
from typing import List, Optional

from pydantic import BaseModel
import dfastmi
from dfastmi.io.AReach import AReach
from dfastmi.io.Branch import Branch
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.ConfigFileOperations import ConfigFileOperations, check_configuration

class GeneralConfig(BaseModel):
    Version: str = "2.0"
    Branch: str = ""
    Reach: str = ""
    Qthreshold: float = 0.0
    Ucrit: float = 0.3
    OutputDir: str = ""
    Plotting: bool = False
    SavePlots: bool = False
    FigureDir: str = ""
    ClosePlots: bool = False

class ConditionConfig(BaseModel):
    Discharge: float
    Reference: str
    WithMeasure: str

class DialogModel():
    config : ConfigParser = None
    section : SectionProxy = None
    def __init__(self, rivers_configuration: RiversObject, config_file: Optional[str] = None):
        self.rivers = rivers_configuration
        
        if config_file:
            self.load_configuration(config_file)
                
        if not self.config:
            self.create_configuration()
        
        BOOLEAN_STATES = {  '1': True,  'yes': True,  'true' : True,  'on' : True,  't':True,  'y':True,
                            '0': False, 'no' : False, 'false': False, 'off': False, 'f':False, 'n':False}
        self.config.BOOLEAN_STATES = BOOLEAN_STATES
    
    @property
    def branch_name(self) -> str:
        return self.section['Branch']
    
    @property
    def reach_name(self) -> str:
        return self.section['Reach']
    
    @property
    def qthreshold(self) -> float:
        return self.section.getfloat('Qthreshold', 0.0)
    
    @qthreshold.setter
    def qthreshold(self, value):
        self.section['Qthreshold'] = str(value)
    
    @property
    def ucritical(self) -> float:
        return self.section.getfloat('Ucrit', 0.3)
    
    @ucritical.setter
    def ucritical(self, value):
        self.section['Ucrit'] = str(value)
    
    @property
    def output_dir(self) -> str:
        return self.section['OutputDir']
    
    @output_dir.setter
    def output_dir(self, value):
        self.section['OutputDir'] = value
    
    @property
    def figure_dir(self) -> str:
        return self.section['FigureDir']
    
    @figure_dir.setter
    def figure_dir(self, value):
        self.section['FigureDir'] = value
    
    @property
    def plotting(self):
        return self.section.getboolean('Plotting')
    
    @plotting.setter
    def plotting(self, value):
        self.section['Plotting'] = str(value)
    
    @property
    def save_plots(self) -> bool:
        return self.section.getboolean('SavePlots')
    
    @save_plots.setter
    def save_plots(self, value):
       self.section['SavePlots'] = str(value)
    
    @property
    def close_plots(self) -> bool:
        return self.section.getboolean('ClosePlots')
    
    @close_plots.setter
    def close_plots(self, value):
        self.section['ClosePlots'] = str(value)
    
    def create_configuration(self) -> bool:
        self.config = ConfigParser()
        self.config['General'] = GeneralConfig().model_dump()
        self.section = self.config['General']

    def load_configuration(self, filename: str) -> bool:
        try:
            self.config = ConfigFileOperations.load_configuration_file(filename)
        except:
            if filename != "dfastmi.cfg":
                return False                
            return True
    
        self.section = self.config["General"]
        return True

    def check_configuration(self, branch : Branch, reach: AReach, reference_files: List, measure_files : List) -> bool :
        config = self.get_configuration(branch, reach, reference_files, measure_files)
        return check_configuration(self.rivers, config)
    

    def run_analysis(self) -> bool:
        # Logic to run analysis based on configuration
        """
        Run the D-FAST Morphological Impact analysis based on settings in the GUI.

        Arguments
        ---------
        None

        Return
        ---------
        succes : bool
            If the analysis could be run successfully. 
            We call batch_mode_core which can throw and log an exception. 
            If thrown, analysis has failed.
        """
        try:
            success = dfastmi.batch.core.batch_mode_core(self.rivers, False, self.config)
        except:
            success = False
        return success
    
    
    def get_configuration(self, branch : Branch, reach: AReach, reference_files: List, measure_files : List) -> ConfigParser:
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
        config["General"] = GeneralConfig(
            Branch=branch.name,
            Reach=reach.name,
            Qthreshold=self.qthreshold,
            Ucrit=self.ucritical,
            OutputDir=self.output_dir,
            Plotting=self.plotting,
            SavePlots=self.save_plots,
            FigureDir=self.figure_dir,
            ClosePlots=self.close_plots
        ).model_dump()        

        self._get_condition_configuration(config, reach, reference_files, measure_files)
        return config
    
    def _get_condition_configuration(self, config: ConfigParser, reach: AReach, reference_files: List, measure_files: List) -> None:
        num_files = min(len(reference_files), len(measure_files))
        
        i = 0
        for discharge in enumerate(reach.hydro_q[:num_files]):
            if discharge[1] in reference_files.keys():
                i += 1
                cond = f"C{i}"
                condition = ConditionConfig(Discharge=discharge[1], Reference="", WithMeasure="")
                if i < len(reference_files):
                    condition.Reference = reference_files[discharge[1]]
                if i < len(measure_files):
                    condition.WithMeasure = measure_files[discharge[1]]
                
                config[cond] = condition.model_dump()
