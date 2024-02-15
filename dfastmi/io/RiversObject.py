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
from typing import Tuple, List
import zlib
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

from dfastmi.io.RiverParameterData import RiverParameterData

class RiversObject():    
    version: version # type: ignore
    branches: List[str]
    reaches: List[List[str]]
    allreaches : List[str]
    qlocations: List[str]
    normal_width: List[List[float]]
    ucritical: List[List[float]]
    qstagnant: List[List[float]]
    tide: List[List[bool]]
    hydro_q: List[List[Tuple[float, ...]]]
    autotime: List[List[bool]]
    hydro_t: List[List[Tuple[float, ...]]]
    qfit: List[List[Tuple[float, float]]]
    tide_bc: List[List[Tuple[float, ...]]]
    cform: List[List[int]]
    cdisch: List[List[Tuple[float, float]]]
    prop_q: List[List[Tuple[float, ...]]]
    prop_c: List[List[Tuple[float, ...]]]
    proprate_high: List[List[float]] # only for version = 1
    proprate_low: List[List[float]] # only for version = 1
    qbankfull: List[List[float]] # only for version = 1
    qmin: List[List[float]] # only for version = 1
    qlevels: List[List[Tuple[float, float, float, float]]] # only for version = 1
    dq: List[List[Tuple[float, float]]] # only for version = 1
    
    _river_data : RiverParameterData


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

        self._river_data = RiverParameterData(config)

        # initialize rivers dictionary
        iversion = self._validate_version_in_file(filename, config)

        self._verify_checksum_rivers(config, filename)
        
        # parse branches
        self._parse_branches(config)

        # parse reaches and discharge locations
        self._parse_reaches_and_discharge_locations(config)

        # collect the values for all other quantities
        self.nreaches = [len(x) for x in self.allreaches]

        # initialize river data object
        self._river_data.initialize(self.branches, self.nreaches)
        
        # call the specific reader for the file version
        if iversion == 1:
            self._read_rivers_legacy()
            
        else: # iversion == 2
            self._read_rivers() 

    def _parse_reaches_and_discharge_locations(self, config):
        self.allreaches = []
        self.qlocations = []
        for branch in self.branches:
            qlocation = config[branch]["QLocation"]
            self.qlocations.extend([qlocation])

            i = 0
            reaches = []
            while True:
                i = i + 1
                try:
                    reach = config[branch]["Reach" + str(i)]
                    reaches.extend([reach])
                except:
                    break
            self.allreaches.extend([reaches])

    def _parse_branches(self, config):
        self.branches = [k for k in config.keys()]
        self.branches.remove("DEFAULT")
        self.branches.remove("General")

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

    def _read_rivers_legacy(self):
        """
        Read a configuration file containing the river data.

        Read the configuration file containing the listing of various branches/reaches
        and their associated default parameter settings.
        """
              
        self.version = version.parse("1.0")
        self._initialize()        
        self._initialize_legacy() 

    def _initialize_legacy(self):
        self.proprate_high = self._river_data.collect_values1("PrHigh")
        self.proprate_low = self._river_data.collect_values1("PrLow")
        self.qbankfull = self._river_data.collect_values1("QBankfull")
        self.qmin = self._river_data.collect_values1("QMin")
        self.qfit = self._river_data.collect_values2("QFit")
        self.qlevels = self._river_data.collect_values4("QLevels")
        self.dq = self._river_data.collect_values2("dQ")

    def _initialize(self):
        self.normal_width = self._river_data.collect_values1("NWidth")
        self.ucritical = self._river_data.collect_values1("UCrit")
        self.qstagnant = self._river_data.collect_values1("QStagnant")      
        
    def _read_rivers(self):
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
        self._initialize()        
        self._initialize_advanced()
        
        
        for ib in range(len(self.branches)):
            reaches = self.allreaches[ib]
            branch = self.branches[ib]                
            for i in range(len(reaches)):
                reach = reaches[i]
                
                hydro_q = self.hydro_q[ib][i]
                hydro_t = self.hydro_t[ib][i]
                auto_time = self.autotime[ib][i]
                qfit = self.qfit[ib][i]
                self._verify_consistency_HydroQ_and_HydroT(hydro_q, hydro_t, auto_time, qfit, branch, reach)

                use_tide = self.tide[ib][i]
                tide_boundary_condition = self.tide_bc[ib][i]
                self._verify_consistency_Hydro_and_TideBC(use_tide, hydro_q, tide_boundary_condition, branch, reach)
                
                celer_form = self.cform[ib][i]
                prop_q = self.prop_q[ib][i]
                prop_c = self.prop_c[ib][i]
                celer_discharge = self.cdisch[ib][i]    
                self._verify_CelerForm_with_PropQ_and_PropC(celer_form, prop_q, prop_c, celer_discharge, branch, reach) 

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

    def _initialize_advanced(self):
        self.hydro_q = self._river_data.collect_valuesN("HydroQ")

        self.autotime = self._river_data.collect_values_logical("AutoTime", False)
        # for AutoTime = True
        self.qfit = self._river_data.collect_values2("QFit", (0.0, 0.0))
        # for AutoTime = False
        self.hydro_t = self._river_data.collect_valuesN("HydroT")

        self.tide = self._river_data.collect_values_logical("Tide", False)
        # for Tide = True
        self.tide_bc = self._river_data.collect_valuesN("TideBC")

        self.cform = self._river_data.collect_int_values1("CelerForm", 2)
        # for CelerForm = 1
        self.prop_q = self._river_data.collect_valuesN("PropQ")
        self.prop_c = self._river_data.collect_valuesN("PropC")
        # for CelerForm = 2
        self.cdisch = self._river_data.collect_values2("CelerQ", (0.0, 0.0))

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

    
