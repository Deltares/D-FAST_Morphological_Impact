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
import configparser
from typing import List, Tuple
import zlib
from packaging.version import Version
from dfastmi.io.IReach import IReach
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.CelerObject import CelerDischarge, CelerProperties
from dfastmi.io.IBranch import IBranch
from dfastmi.io.Reach import Reach

from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser
from dfastmi.io.ReachLegacy import ReachLegacy

class RiversObject():
    branches: List[IBranch]
    version: Version

    def __init__(self, filename: str = "rivers.ini"):
        self._read_rivers_file(filename)
    
    def get_branch(self, branch_name : str) -> IBranch:
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

        river_data = DFastMIConfigParser(config)

        # initialize rivers dictionary
        iversion = self._validate_version_in_file(filename, config)

        self._verify_checksum_rivers(config, filename)
        
        # parse branches
        self.branches = []
        self._parse_branches(config)

        # parse reaches and discharge locations
        self._parse_reaches(config, iversion)
        
        # call the specific reader for the file version
        if iversion == 1:
            self._read_rivers_legacy(river_data)
            
        else: # iversion == 2
            self._read_rivers(river_data) 

    def _parse_reaches(self, config : configparser.ConfigParser, iversion):
        for branch in self.branches:
            i = 0
            while True:
                i = i + 1
                try:
                    reach_config_key_name = "Reach" + str(i)
                    reach_name = config[branch.name][reach_config_key_name]
                    if iversion == 1:
                        reach = ReachLegacy(reach_name, i)
                    else:    
                        reach = Reach(reach_name, i)
                    branch.reaches.append(reach)
                except:
                    break

    def _parse_branches(self, config : configparser.ConfigParser):
        # Keys to remove
        keys_to_remove = ["DEFAULT", "General"]

        # Using list comprehension
        branch_names = [branch_name for branch_name in config.keys() if branch_name not in keys_to_remove]
        for branch_name in branch_names:
            branch = Branch(branch_name)
            branch.qlocation = config[branch.name]["QLocation"]
            self.branches.append(branch)      

    def _validate_version_in_file(self, filename, config):
        try:
            file_version = config["General"]["Version"]
        except:
            raise Exception("No version information in the file {}!".format(filename))

        if Version(file_version) == Version("1"):
            iversion = 1
        elif Version(file_version) == Version("2"):
            iversion = 2
        else:
            raise Exception("Unsupported version number {} in the file {}!".format(file_version, filename))
        return iversion       

    def _read_rivers_legacy(self, river_data):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.
        """
              
        self.version = Version("1.0")
        for branch in self.branches:
            for reach in branch.reaches:
                self._initialize_base(river_data, reach)
                self._initialize_legacy(river_data, reach)

    def _initialize_legacy(self, river_data : DFastMIConfigParser, reach : ReachLegacy):
        reach.proprate_high = river_data.read_key(float, "PrHigh", reach)
        reach.proprate_low = river_data.read_key(float, "PrLow", reach)
        reach.qbankfull = river_data.read_key(float, "QBankfull", reach)
        reach.qmin = river_data.read_key(float, "QMin", reach)
        reach.qfit = river_data.read_key(Tuple[float, ...], "QFit", reach, expected_number_of_values=2)
        reach.qlevels = river_data.read_key(Tuple[float, ...], "QLevels", reach, expected_number_of_values=4)
        reach.dq = river_data.read_key(Tuple[float, ...], "dQ", reach, expected_number_of_values=2)

    def _initialize_base(self, river_data : DFastMIConfigParser, reach:IReach):
        reach.normal_width = river_data.read_key(float, "NWidth", reach)
        reach.ucritical = river_data.read_key(float, "UCrit", reach)
        reach.qstagnant = river_data.read_key(float, "QStagnant", reach)
        
    def _read_rivers(self, river_data : DFastMIConfigParser):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.

        Parameters
        ----------
        filename : str
            The name of the river configuration file (default "rivers.ini").    
        """
        self.version = Version("2.0")
        for branch in self.branches:
            for reach in branch.reaches:
                self._initialize_base(river_data, reach)
                self._initialize(river_data, reach)
                reach.verify()
        
        #self._verify_reaches()
        
    

    def _initialize(self, river_data : DFastMIConfigParser, reach : Reach):
        reach.hydro_q = river_data.read_key(Tuple[float, ...], "HydroQ", reach)

        reach.auto_time = river_data.read_key(bool, "AutoTime", reach, False)
        # for AutoTime = True
        reach.qfit = river_data.read_key(Tuple[float, ...], "QFit", reach, (0.0, 0.0), 2)
        # for AutoTime = False
        reach.hydro_t = river_data.read_key(Tuple[float, ...], "HydroT", reach)

        reach.use_tide = river_data.read_key(bool, "Tide", reach, False)
        # for Tide = True
        reach.tide_boundary_condition = river_data.read_key(Tuple[str, ...], "TideBC", reach)

        reach.celer_form = river_data.read_key(int, "CelerForm", reach, 2)
        if reach.celer_form == 1:
            celerProperties = CelerProperties()
            celerProperties.prop_q = river_data.read_key(Tuple[float, ...], "PropQ", reach)
            celerProperties.prop_c = river_data.read_key(Tuple[float, ...], "PropC", reach)
            reach.celer_object = celerProperties
        elif reach.celer_form == 2:
            celerDischarge = CelerDischarge()
            celerDischarge.cdisch = river_data.read_key(Tuple[float, ...], "CelerQ", reach, (0.0, 0.0), 2)
            reach.celer_object = celerDischarge       
    
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
                    checkval = zlib.adler32(ini_value.encode("utf-8"), checkval) & 0xffffffff
        #print("Expected checksum: ", checkval)
        if checksum == "":
            ApplicationSettingsHelper.log_text("checksum", dict = {"filename": filename})
        else:
            checkval2 = int(checksum)
            if checkval2 != checkval:
                raise Exception("Checksum mismatch: configuration file {} has been modified!".format(filename))

    
