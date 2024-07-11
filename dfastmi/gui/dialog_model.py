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
from configparser import ConfigParser, SectionProxy
from typing import Optional

from packaging.version import Version
from pydantic import BaseModel

import dfastmi
from dfastmi.config.ConfigFileOperations import (
    ConfigFileOperations,
    check_configuration,
)
from dfastmi.io.AReach import AReach
from dfastmi.io.Branch import Branch
from dfastmi.io.ConfigBooleans import BOOLEAN_STATES
from dfastmi.io.Reach import Reach
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import FilenameDict


class GeneralConfig(BaseModel):
    """Represents the general configuration settings."""

    Version: str = "3.0"
    CaseDescription: str = ""
    Branch: str = ""
    Reach: str = ""
    Qthreshold: float = 0.0
    Ucrit: float = 0.3
    OutputDir: str = ""
    Plotting: bool = False
    SavePlots: bool = False
    FigureDir: str = ""
    ClosePlots: bool = False
    RiverKM: str = ""


class ConditionConfig(BaseModel):
    """Represents the configuration settings for a specific condition."""

    Discharge: float
    Reference: str
    WithIntervention: str


class DialogModel:
    """Class for handling dialog model."""

    config: ConfigParser = None
    section: SectionProxy = None
    case_description: str = ""

    def __init__(self, rivers_configuration: RiversObject):
        """
        Initialize the DialogModel.

        Args:
            rivers_configuration (RiversObject): Configuration of rivers.
        """
        self.rivers = rivers_configuration

        self.create_configuration()

        self.config.BOOLEAN_STATES = BOOLEAN_STATES

    @property
    def case_description(self) -> str:
        """Get case description."""
        return self.section.get("CaseDescription", "")

    @case_description.setter
    def case_description(self, value: str):
        """Set case description."""
        self.section["CaseDescription"] = value

    @property
    def branch_name(self) -> str:
        """Get branch name."""
        return self.section.get("Branch", "")

    @property
    def reach_name(self) -> str:
        """Get reach name."""
        return self.section.get("Reach", "")

    @property
    def qthreshold(self) -> float:
        """Get Qthreshold."""
        return self.section.getfloat("Qthreshold", 0.0)

    @property
    def ucritical(self) -> float:
        """Get Ucritical."""
        return self.section.getfloat("Ucrit", 0.3)

    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self.section.get("OutputDir", "")

    @output_dir.setter
    def output_dir(self, value: str):
        """Set output directory."""
        self.section["OutputDir"] = value

    @property
    def figure_dir(self) -> str:
        """Get figure directory."""
        return self.section.get("FigureDir", "")

    @figure_dir.setter
    def figure_dir(self, value: str):
        """Set figure directory."""
        self.section["FigureDir"] = value

    @property
    def plotting(self) -> bool:
        """Get plotting flag."""
        return self.section.getboolean("Plotting", False)

    @plotting.setter
    def plotting(self, value: bool):
        """Set plotting flag."""
        self.section["Plotting"] = str(value)

    @property
    def save_plots(self) -> bool:
        """Get save plots flag."""
        return self.section.getboolean("SavePlots", False)

    @save_plots.setter
    def save_plots(self, value: bool):
        self.section["SavePlots"] = str(value)

    @property
    def close_plots(self) -> bool:
        """Get close plots flag."""
        return self.section.getboolean("ClosePlots", False)

    @close_plots.setter
    def close_plots(self, value: bool):
        """Set close plots flag."""
        self.section["ClosePlots"] = str(value)

    @property
    def riverkm_file(self) -> str:
        """Get RiverKM file to specify the chainage along the reach of interest."""
        return self.section.get("RiverKM", "")

    def create_configuration(self) -> bool:
        """Create configuration."""
        self.config = ConfigParser()
        self.config.optionxform = str
        self.config["General"] = GeneralConfig().model_dump()
        self.section = self.config["General"]

    def load_configuration(self, filename: str) -> bool:
        """Load configuration."""
        try:
            self.config = ConfigFileOperations.load_configuration_file(filename)
        except (SystemExit, KeyboardInterrupt) as exception:
            raise exception
        except:
            if filename != "dfastmi.cfg":
                return False
            return True

        self.section = self.config["General"]
        return True

    def check_configuration(
        self,
        branch: Branch,
        reach: AReach,
        reference_files: FilenameDict,
        intervention_files: FilenameDict,
        ucritical: float,
        qthreshold: float,
    ) -> bool:
        """
        Check if configuration can be created.

        Arguments
        ---------
        branch: Branch
            Selected branch which is used and should be in this config.
        reach: AReach
            Selected reach which is used and should be in this config.
        reference_files: FilenameDict
            Selected reference files which is used and should be in this config.
        intervention_files: FilenameDict
            Selected intervention files which is used and should be in this config.
        ucritical : float
            Selected minimal critical flow value which is used and should be in this config.
        qthreshold : float
            Selected discharge threshold value which is used and should be in this config.

        Returns
        -------
            Boolean indicating whether the (D-FAST MI analysis) configuration can be created.
        """
        config = self.get_configuration(
            branch, reach, reference_files, intervention_files, ucritical, qthreshold
        )
        return check_configuration(self.rivers, config)

    def get_configuration(
        self,
        branch: Branch,
        reach: AReach,
        reference_files: FilenameDict,
        intervention_files: FilenameDict,
        ucritical: float,
        qthreshold: float,
    ) -> ConfigParser:
        """
        Extract a configuration from the GUI.

        Arguments
        ---------
        branch: Branch
            Selected branch which is used and should be in this config.
        reach: AReach
            Selected reach which is used and should be in this config.
        reference_files: FilenameDict
            Selected reference files which is used and should be in this config.
        intervention_files: FilenameDict
            Selected intervention files which is used and should be in this config.
        ucritical : float
            Selected minimal critical flow value which is used and should be in this config.
        qthreshold : float
            Selected discharge threshold value which is used and should be in this config.

        Returns
        -------
        config : Optional[configparser.ConfigParser]
            Configuration for the D-FAST Morphological Impact analysis.
        """
        config = ConfigParser()
        config.optionxform = str
        config.add_section("General")
        config["General"] = GeneralConfig(
            Version=str(self.rivers.version),
            CaseDescription=self.case_description,
            Branch=branch.name,
            Reach=reach.name,
            Qthreshold=qthreshold,
            Ucrit=ucritical,
            OutputDir=self.output_dir,
            Plotting=self.plotting,
            SavePlots=self.save_plots,
            FigureDir=self.figure_dir,
            ClosePlots=self.close_plots,
            RiverKM=self.riverkm_file,
        ).model_dump()

        if isinstance(reach, Reach):
            self._get_condition_configuration(
                config, reach, reference_files, intervention_files
            )
        self._add_unknown_read_config_key_values(config)
        return config

    def _get_condition_configuration(
        self,
        config: ConfigParser,
        reach: Reach,
        reference_files: FilenameDict,
        intervention_files: FilenameDict,
    ) -> None:
        """Get condition configuration."""
        for i, discharge in enumerate(reach.hydro_q):
            if (
                discharge in reference_files.keys()
                or discharge in intervention_files.keys()
            ):
                cond = f"C{i+1}"

                condition = ConditionConfig(
                    Discharge=discharge,
                    Reference=reference_files.get(discharge, ""),
                    WithIntervention=intervention_files.get(discharge, ""),
                )

                config[cond] = condition.model_dump()

    def _add_unknown_read_config_key_values(self, config: ConfigParser) -> None:
        """
        When the config has keys and values which are not known yet in the application
        we should also write them back in the new config file
        """
        for section in self.config:
            if not config.has_section(section):
                config[section] = {}

            for key, value in self.config.items(section):
                if not config.has_option(section, key):
                    config[section][key] = value
