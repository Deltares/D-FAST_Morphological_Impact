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
import configparser
import zlib
from typing import List

from packaging.version import Version

from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.CelerObject import CelerDischarge, CelerProperties
from dfastmi.io.DFastRiverConfigFileParser import DFastRiverConfigFileParser
from dfastmi.io.IBranch import IBranch
from dfastmi.io.IReach import IReach
from dfastmi.io.Reach import Reach
from dfastmi.io.ReachLegacy import ReachLegacy


class RiversObject:
    branches: List[IBranch]
    version: Version

    def __init__(self, filename: str = "rivers.ini"):
        self._read_rivers_file(filename)

    def get_branch(self, branch_name: str) -> Branch:
        """
        Return the branch from the read branches list
        Arguments
        ---------
        branch_name : str
            The name of the branch in the river configuration
        """
        for branch in self.branches:
            if branch.name == branch_name:
                return branch
        return None  # Return None if the branch with the given name is not found

    def _read_rivers_file(self, filename):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.

        Parameters
        ----------
        filename : str
            The name of the river configuration file (default "rivers.ini").

        """
        config: configparser.ConfigParser

        # read the file
        config = configparser.ConfigParser()
        with open(filename, "r") as configfile:
            config.read_file(configfile)

        river_data = DFastRiverConfigFileParser(config)

        # initialize rivers dictionary
        self.version = self._validate_version_in_file(filename, config)

        self._verify_checksum_rivers(config, filename)

        # parse branches
        self.branches = []
        self._parse_branches(config)

        # parse reaches and discharge locations
        self._parse_reaches(config)

        # call the specific reader for the file version
        if self.version == Version("1"):
            self._read_rivers_legacy(river_data)

        else:
            self._read_rivers(river_data)

    def _parse_reaches(self, config: configparser.ConfigParser):
        for branch in self.branches:
            i = 0
            while True:
                i = i + 1
                try:
                    reach_config_key_name = "Reach" + str(i)
                    reach_name = config[branch.name][reach_config_key_name]
                    if self.version == Version("1"):
                        reach = ReachLegacy(reach_name, i)
                    else:
                        reach = Reach(reach_name, i)
                    branch.reaches.append(reach)
                except Exception:
                    break

    def _parse_branches(self, config: configparser.ConfigParser):
        # Keys to remove
        keys_to_remove = ["DEFAULT", "General"]

        # Using list comprehension
        branch_names = [
            branch_name
            for branch_name in config.keys()
            if branch_name not in keys_to_remove
        ]
        for branch_name in branch_names:
            branch = Branch(branch_name)
            branch.qlocation = config[branch.name]["QLocation"]
            self.branches.append(branch)

    def _validate_version_in_file(self, filename, config) -> Version:
        try:
            file_version = config["General"]["Version"]
        except:
            raise Exception("No version information in the file {}!".format(filename))

        if Version(file_version) not in [Version("1"), Version("2"), Version("3")]:
            raise Exception(
                "Unsupported version number {} in the file {}!".format(
                    file_version, filename
                )
            )
        return Version(file_version)

    def _read_rivers_legacy(self, river_data: DFastRiverConfigFileParser):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.
        """

        for branch in self.branches:
            for reach in branch.reaches:
                self._initialize_base(river_data, reach)
                self._initialize_legacy(river_data, reach)

    def _initialize_legacy(
        self, river_data: DFastRiverConfigFileParser, reach: ReachLegacy
    ):
        reach.proprate_high = river_data.getfloat("PrHigh", reach)
        reach.proprate_low = river_data.getfloat("PrLow", reach)
        reach.qbankfull = river_data.getfloat("QBankfull", reach)
        reach.qmin = river_data.getfloat("QMin", reach)
        reach.qfit = river_data.getfloats("QFit", reach, expected_number_of_values=2)
        reach.qlevels = river_data.getfloats(
            "QLevels", reach, expected_number_of_values=4
        )
        reach.dq = river_data.getfloats("dQ", reach, expected_number_of_values=2)

    def _initialize_base(self, river_data: DFastRiverConfigFileParser, reach: IReach):
        reach.normal_width = river_data.getfloat("NWidth", reach)
        reach.ucritical = river_data.getfloat("UCrit", reach)
        reach.qstagnant = river_data.getfloat("QStagnant", reach)

    def _read_rivers(self, river_data: DFastRiverConfigFileParser):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.

        Parameters
        ----------
        river_data : DFastRiverConfigFileParser
            The read data from the river configuration file.
        """
        for branch in self.branches:
            for reach in branch.reaches:
                self._initialize_base(river_data, reach)
                self._initialize(river_data, reach)
                reach.model_validate(reach)

    def _initialize(self, river_data: DFastRiverConfigFileParser, reach: Reach):
        reach.hydro_q = river_data.getfloats("HydroQ", reach)
        reach.auto_time = river_data.getboolean("AutoTime", reach, False)
        # for AutoTime = True
        reach.qfit = river_data.getfloats("QFit", reach, (0.0, 0.0), 2)
        # for AutoTime = False
        reach.hydro_t = river_data.getfloats("HydroT", reach)

        reach.use_tide = river_data.getboolean("Tide", reach, False)
        # for Tide = True
        reach.tide_boundary_condition = river_data.getstrings("TideBC", reach)

        reach.celer_form = river_data.getint("CelerForm", reach, 2)
        if reach.celer_form == 1:
            celerity_properties = CelerProperties()
            celerity_properties.prop_q = river_data.getfloats("PropQ", reach)
            celerity_properties.prop_c = river_data.getfloats("PropC", reach)
            reach.celer_object = celerity_properties
        elif reach.celer_form == 2:
            celerity_discharge = CelerDischarge()
            celerity_discharge.cdisch = river_data.getfloats(
                "CelerQ", reach, (0.0, 0.0), 2
            )
            reach.celer_object = celerity_discharge

    def _verify_checksum_rivers(
        self,
        config: configparser.ConfigParser,
        filename: str,
    ):
        chapters = [k for k in config.keys()]
        checksum = ""
        checkval = 1
        for chapter in chapters:
            keys = [k for k in config[chapter].keys()]
            for key in keys:
                ini_value = config[chapter][key]
                if chapter == "General" and key == "checksum":
                    checksum = ini_value
                else:
                    checkval = (
                        zlib.adler32(ini_value.encode("utf-8"), checkval) & 0xFFFFFFFF
                    )
        # print("Expected checksum: ", checkval)
        if checksum == "":
            ApplicationSettingsHelper.log_text("checksum", dict={"filename": filename})
        else:
            checkval2 = int(checksum)
            if checkval2 != checkval:
                raise Exception(
                    "Checksum mismatch: configuration file {} has been modified!".format(
                        filename
                    )
                )
