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
from packaging import version
import configparser
from typing import List
import zlib
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.CelerObject import CelerDischarge, CelerProperties
from dfastmi.io.Reach import Reach, ReachAdvanced, ReachLegacy

from dfastmi.io.RiverParameterData import RiverParameterData

class RiversObject():
    branches: List[Branch]
    version: version # type: ignore

    def __init__(self, filename: str = "rivers.ini"):
        self._read_rivers_file(filename)

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

        river_data = RiverParameterData(config)

        # initialize rivers dictionary
        iversion = self._validate_version_in_file(filename, config)

        self._verify_checksum_rivers(config, filename)
        
        # parse branches
        self.branches = []
        self._parse_branches(config)

        # parse reaches and discharge locations
        self._parse_reaches(config, iversion)

        # collect the values for all other quantities
        #self.nreaches = [len(x) for x in self.allreaches]

        # initialize river data object
        #river_data.initialize(self.branches, self.nreaches)
        
        # call the specific reader for the file version
        if iversion == 1:
            self._read_rivers_legacy(river_data)
            
        else: # iversion == 2
            self._read_rivers(river_data) 

    def _parse_reaches(self, config, iversion):
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
                        reach = ReachAdvanced(reach_name, i)
                    branch.reaches.append(reach)
                except:
                    break

    def _parse_branches(self, config):
        for branch_name in config.keys() - {"DEFAULT", "General"}:
            branch = Branch(branch_name)
            branch.qlocation = config[branch.name]["QLocation"]
            self.branches.append(branch)      

    def _validate_version_in_file(self, filename, config):
        try:
            file_version = config["General"]["Version"]
        except:
            raise Exception("No version information in the file {}!".format(filename))

        if version.parse(file_version) == version.parse("1"):
            iversion = 1
        elif version.parse(file_version) == version.parse("2"):
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
              
        self.version = version.parse("1.0")
        for branch in self.branches:
            for reach in branch.reaches:
                self._initialize(river_data, branch, reach)
                self._initialize_legacy(river_data, branch, reach)

    def _initialize_legacy(self, river_data : RiverParameterData, branch : Branch, reach : ReachLegacy):
        reach.proprate_high = river_data.read_key_float("PrHigh", branch, reach)
        reach.proprate_low = river_data.read_key_float("PrLow", branch, reach)
        reach.qbankfull = river_data.read_key_float("QBankfull", branch, reach)
        reach.qmin = river_data.read_key_float("QMin", branch, reach)
        reach.qfit = river_data.read_key_tuple_float_float("QFit", branch, reach)
        reach.qlevels = river_data.read_key_tuple_float_float_float_float("QLevels", branch, reach)
        reach.dq = river_data.read_key_tuple_float_float("dQ", branch, reach)
        

    def _initialize(self, river_data : RiverParameterData, branch: Branch, reach:Reach):
        reach.normal_width = river_data.read_key_float("NWidth", branch, reach)
        reach.ucritical = river_data.read_key_float("UCrit", branch, reach)
        reach.qstagnant = river_data.read_key_float("QStagnant", branch, reach)
        
    def _read_rivers(self, river_data : RiverParameterData):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.

        Parameters
        ----------
        filename : str
            The name of the river configuration file (default "rivers.ini").    
        """
        self.version = version.parse("2.0")
        for branch in self.branches:
            for reach in branch.reaches:
                self._initialize(river_data, branch, reach)
                self._initialize_advanced(river_data, branch, reach)
        
        
        self._verify_reaches()
        
    def _verify_reaches(self):
        for branch in self.branches:
            for reach in branch.reaches:
                hydro_q = reach.hydro_q
                hydro_t = reach.hydro_t
                auto_time = reach.autotime
                qfit = reach.qfit
                self._verify_consistency_HydroQ_and_HydroT(hydro_q, hydro_t, auto_time, qfit, branch.name, reach.name)

                use_tide = reach.tide
                tide_boundary_condition = reach.tide_bc
                self._verify_consistency_Hydro_and_TideBC(use_tide, hydro_q, tide_boundary_condition, branch.name, reach.name)
                
                celer_form = reach.cform
                prop_q = reach.prop_q
                prop_c = reach.prop_c
                celer_discharge = reach.cdisch
                self._verify_CelerForm_with_PropQ_and_PropC(celer_form, prop_q, prop_c, celer_discharge, branch.name, reach.name)

    def _verify_CelerForm_with_PropQ_and_PropC(self, celer_form, prop_q, prop_c, celer_discharge, branch, reach):
        if celer_form == 1:
            prop_q_length = len(prop_q)
            prop_c_lenght = len(prop_c)
            if prop_q_length != prop_c_lenght:
                raise Exception(
                            'Length of "PropQ" and "PropC" for branch "{}", reach "{}" are not consistent: {} and {} values read respectively.'.format(
                                branch,
                                reach,
                                prop_q_length,
                                prop_c_lenght,
                            )
                        )
            elif prop_q_length == 0:
                raise Exception(
                            'The parameters "PropQ" and "PropC" must be specified for branch "{}", reach "{}" since "CelerForm" is set to 1.'.format(
                                branch,
                                reach,
                            )
                        )
        elif celer_form == 2:            
            if celer_discharge == (0.0, 0.0):
                raise Exception(
                            'The parameter "CelerQ" must be specified for branch "{}", reach "{}" since "CelerForm" is set to 2.'.format(
                                branch,
                                reach,
                            )
                        )
                        
        else:
            raise Exception(
                        'Invalid value {} specified for "CelerForm" for branch "{}", reach "{}"; only 1 and 2 are supported.'.format(
                            celer_form,
                            branch,
                            reach,
                        )
                    )

    def _verify_consistency_Hydro_and_TideBC(self, use_tide, hydro_q, tide_boundary_condition, branch, reach):        
        """
            Verify consistent length of hydro discharge and tide boundary condition values for this branch on this reach.
        """
        if use_tide:
            hydro_q_length = len(hydro_q)
            tide_boundary_condition_length = len(tide_boundary_condition)
            if hydro_q_length != tide_boundary_condition_length:
                raise Exception(
                            'Length of "HydroQ" and "TideBC" for branch "{}", reach "{}" are not consistent: {} and {} values read respectively.'.format(
                                branch,
                                reach,
                                hydro_q_length,
                                tide_boundary_condition_length
                            )
                        )

    def _verify_consistency_HydroQ_and_HydroT(self, hydro_q, hydro_t, auto_time, qfit, branch, reach):
        """
            Verify consistent length of hydro_q and hydro_t for this branch on this reach.
        """        
        if auto_time:                        
            self._check_qfit_on_branch_on_reach_with_auto_time(qfit, branch, reach)
        else:            
            hydro_q_length = len(hydro_q)
            hydro_t_length = len(hydro_t)
            if hydro_q_length != hydro_t_length:
                raise Exception(
                            'Length of "HydroQ" and "HydroT" for branch "{}", reach "{}" are not consistent: {} and {} values read respectively.'.format(
                                branch,
                                reach,
                                hydro_q_length,
                                hydro_t_length,
                            )
                        )

    def _initialize_advanced(self, river_data : RiverParameterData, branch : Branch, reach : ReachAdvanced):
        reach.hydro_q = river_data.read_key_tuple_float_n("HydroQ", branch, reach)

        reach.autotime = river_data.read_key_bool("AutoTime", branch, reach, False)
        # for AutoTime = True
        reach.qfit = river_data.read_key_tuple_float_float("QFit", branch, reach, (0.0, 0.0))
        # for AutoTime = False
        reach.hydro_t = river_data.read_key_tuple_float_n("HydroT", branch, reach)

        reach.tide = river_data.read_key_bool("Tide", branch, reach, False)
        # for Tide = True
        reach.tide_bc = river_data.read_key_tuple_float_n("TideBC", branch, reach)

        reach.celer_form = river_data.read_key_float("CelerForm", branch, reach, 2)
        if reach.celer_form == 1:
            celerProperties = CelerProperties()
            celerProperties.prop_q = river_data.read_key_tuple_float_n("PropQ", branch, reach)
            celerProperties.prop_c = river_data.read_key_tuple_float_n("PropC", branch, reach)
            reach.celer_object = celerProperties
        elif reach.celer_form == 2:
            celerDischarge = CelerDischarge()
            celerDischarge.cdisch = river_data.read_key_tuple_float_float("CelerQ", branch, reach, (0.0, 0.0))
            reach.celer_object = celerDischarge
        
    def _check_qfit_on_branch_on_reach_with_auto_time(self, qfit, branch, reach):
        if qfit == (0.0, 0.0):
            raise Exception(
                            'The parameter "QFit" must be specified for branch "{}", reach "{}" since "AutoTime" is set to True.'.format(
                                branch,
                                reach,
                            )
                    )               

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

    
