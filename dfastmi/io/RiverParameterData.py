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
from typing import Tuple, List, Optional

class RiverParameterData:
    """
        Collect river parameter data from river configuration object.
    """

    _branches: List[str]
    """
       The list of river branches. The length of this list is nBranches.
    """

    _nreaches: List[int]
    """ 
        The number of reaches per river branch. The length of this list is nBranches.
    """
        
    _config: configparser.ConfigParser
    """ 
        The dictionary containing river data.
    """
    _is_initialized : bool

    def __init__(self, config: configparser.ConfigParser):
        self._config = config
        self._is_initialized = False
    
    def initialize(self, branches: List[str], nreaches: List[int]) : 
        """
            This routine initialize the object with required objects
        """
        self._branches = branches
        self._nreaches = nreaches
        self._is_initialized = True
    
    def is_initialized(self):
        if self._is_initialized :
            return
        else:
            raise Exception('RiverParameterData object is not initialized')


    def collect_int_values1(
        self,                
        key: str,
        default: Optional[int] = None,
    ) -> List[List[int]]:
        """
        This routines collects entries of type integer.

        Arguments
        ---------
        config : configparser.ConfigParser
            The dictionary containing river data.
        key : str
            The name of the parameter for which the values are to be retrieved.

        Raises
        ------
        Exception
            If the number of values read from the file doesn't match 1.

        Returns
        -------
        data : List[List[int]]
            A list of lists. Each list contains per reach within the corresponding
            branch one integer.
        """
        self.is_initialized()
        try:
            g_val = self._config["General"][key]
        except:
            g_val = ""

        all_values = []
        for ib in range(len(self._branches)):
            branch = self._branches[ib]
            try:
                b_val = self._config[branch][key]
            except:
                b_val = g_val

            values_per_branch = []
            for i in range(self._nreaches[ib]):
                stri = str(i + 1)
                try:
                    val = self._config[branch][key + stri]
                except:
                    val = b_val
                if val == "" and default is not None:
                    ival = default
                else:
                    try:
                        vals = tuple(int(x) for x in val.split())
                    except:
                        vals = ()
                    if len(vals) != 1:
                        raise Exception(
                            'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                                key, i+1, self._branches[ib], val, 1
                            )
                        )
                    ival = vals[0]
                values_per_branch.append(ival)

            all_values.append(values_per_branch)

        return all_values


    def collect_values_logical(
        self,
        key: str,
        default: Optional[bool] = None,
    ) -> List[List[bool]]:
        """
        This routines collects entries of type bool.

        Arguments
        ---------
        key : str
            The name of the parameter for which the values are to be retrieved.

        Raises
        ------
        Exception
            If the number of values read from the file doesn't match 1.

        Returns
        -------
        data : List[List[bool]]
            A list of lists. Each list contains per reach within the corresponding
            branch one bool or a list of booleans depending on input argument nval.
        """
        self.is_initialized()
        try:
            g_val = self._config["General"][key]
        except:
            g_val = ""
        all_values = []
        for ib in range(len(self._branches)):
            branch = self._branches[ib]
            try:
                b_val = self._config[branch][key]
            except:
                b_val = g_val
            values_per_branch = []
            for i in range(self._nreaches[ib]):
                stri = str(i + 1)
                try:
                    val = self._config[branch][key + stri]
                except:
                    val = b_val
                if val == "" and default is not None:
                    bval = default
                else:
                    try:
                        vals = tuple(x.lower() in ['true', '1', 't', 'y', 'yes'] for x in val.split())
                    except:
                        vals = ()
                    if len(vals) != 1:
                        raise Exception(
                            'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                                key, i+1, self._branches[ib], val, 1
                            )
                        )
                    bval = vals[0]
                values_per_branch.append(bval)
            all_values.append(values_per_branch)
        return all_values
    
    def collect_values1(
            self,
            key: str,
            default: Optional[float] = None,
        ) -> List[List[float]]:
        """
        This routines collects entries of type float.

        Arguments
        ---------
        key : str
            The name of the parameter for which the values are to be retrieved.

        Raises
        ------
        Exception
            If the number of values read from the file doesn't match 1.

        Returns
        -------
        data : List[List[float]]
            A list of lists. Each list contains per reach within the corresponding
            branch one float.
        """
        self.is_initialized()
        try:
            g_val = self._config["General"][key]
        except:
            g_val = ""

        all_values = []
        for ib in range(len(self._branches)):
            branch = self._branches[ib]
            try:
                b_val = self._config[branch][key]
            except:
                b_val = g_val

            values_per_branch = []
            for i in range(self._nreaches[ib]):
                stri = str(i + 1)
                try:
                    val = self._config[branch][key + stri]
                except:
                    val = b_val
                if val == "" and default is not None:
                    fval = default
                else:
                    try:
                        vals = tuple(float(x) for x in val.split())
                    except:
                        vals = ()
                    if len(vals) != 1:
                        raise Exception(
                            'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                                key, i+1, self._branches[ib], val, 1
                            )
                        )
                    fval = vals[0]
                values_per_branch.append(fval)

            all_values.append(values_per_branch)

        return all_values
    
    def collect_values2(
        self,
        key: str,
        default: Optional[Tuple[float, float]] = None,
    ) -> List[List[Tuple[float, float]]]:
        """
        Collect river parameter data from river configuration object.

        This routines collects entries of type Tuple[float, float].

        Arguments
        ---------
        key : str
            The name of the parameter for which the values are to be retrieved.
        default : Optional[Tuple[float, float]]
            Default tuple if not specified in file.

        Raises
        ------
        Exception
            If the number of values read from the file doesn't match 2.

        Returns
        -------
        data : List[List[Tuple[float, float]]]
            A list of lists. Each list contains per reach within the corresponding
            branch a list of 2 floats.
        """
        vals: Tuple[float, ...]
        self.is_initialized()
        try:
            g_val = self._config["General"][key]
        except:
            g_val = ""
        all_values = []
        for ib in range(len(self._branches)):
            branch = self._branches[ib]
            try:
                b_val = self._config[branch][key]
            except:
                b_val = g_val
            values_per_branch = []
            for i in range(self._nreaches[ib]):
                stri = str(i + 1)
                try:
                    val = self._config[branch][key + stri]
                except:
                    val = b_val
                if val == "" and default is not None:
                    vals = default
                else:
                    try:
                        vals = tuple(float(x) for x in val.split())
                    except:
                        vals = ()
                    if len(vals) != 2:
                        raise Exception(
                            'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                                key, i+1, self._branches[ib], val, 2
                            )
                        )
                values_per_branch.append((vals[0], vals[1]))
            all_values.append(values_per_branch)
        return all_values
    
    def collect_values4(
        self,
        key: str,
        default: Optional[Tuple[float, float, float, float]] = None,
    ) -> List[List[Tuple[float, float, float, float]]]:
        """
        This routines collects entries of type Tuple[float, float, float, float].

        Arguments
        ---------
        key : str
            The name of the parameter for which the values are to be retrieved.
        default : Optional[Tuple[float, float, float, float]]
            Default tuple if not specified in file.

        Raises
        ------
        Exception
            If the number of values read from the file doesn't match 4.

        Returns
        -------
        data : List[List[Tuple[float, float, float, float]]]
            A list of lists. Each list contains per reach within the corresponding
            branch a list of 4 floats.
        """
        vals: Tuple[float, ...]
        self.is_initialized()        
        try:
            g_val = self._config["General"][key]
        except:
            g_val = ""
        all_values = []
        for ib in range(len(self._branches)):
            branch = self._branches[ib]
            try:
                b_val = self._config[branch][key]
            except:
                b_val = g_val
            values_per_branch = []
            for i in range(self._nreaches[ib]):
                stri = str(i + 1)
                try:
                    val = self._config[branch][key + stri]
                except:
                    val = b_val
                if val == "" and default is not None:
                    vals = default
                else:
                    try:
                        vals = tuple(float(x) for x in val.split())
                    except:
                        vals = ()
                    if len(vals) != 4:
                        raise Exception(
                            'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                                key, i+1, self._branches[ib], val, 4
                            )
                        )
                values_per_branch.append((vals[0], vals[1], vals[2], vals[3]))
            all_values.append(values_per_branch)
        return all_values

    def collect_valuesN(
        self,
        key: str
    ) -> List[List[Tuple[float, ...]]]:
        """
        This routines collects entries of type Tuple[float, ...]

        Arguments
        ---------
        key : str
            The name of the parameter for which the values are to be retrieved.

        Returns
        -------
        data : List[List[Tuple[float, ...]]]
            A list of lists. Each list contains per reach within the corresponding
            branch a list of floats.
        """
        vals: Tuple[float, ...]
        self.is_initialized()        
        try:
            g_val = self._config["General"][key]
        except:
            g_val = ""
        all_values = []
        for ib in range(len(self._branches)):
            branch = self._branches[ib]
            try:
                b_val = self._config[branch][key]
            except:
                b_val = g_val
            values_per_branch = []
            for i in range(self._nreaches[ib]):
                stri = str(i + 1)
                try:
                    val = self._config[branch][key + stri]
                except:
                    val = b_val
                vals = tuple(float(x) for x in val.split())
                values_per_branch.append(vals)
            all_values.append(values_per_branch)
        return all_values
    
    def config_get_bool(
        self,
        group: str,
        key: str,
        default: Optional[bool] = None,
    ) -> bool:
        """
        Get a boolean from a selected group and keyword in the analysis settings.

        Arguments
        ---------
        group : str
            Name of the group from which to read.
        key : str
            Name of the keyword from which to read.
        default : Optional[bool]
            Optional default value.

        Raises
        ------
        Exception
            If the keyword isn't specified and no default value is given.

        Returns
        -------
        val : bool
            Boolean value.
        """
        try:
            str = self._config[group][key].lower()
            val = (
                (str == "yes")
                or (str == "y")
                or (str == "true")
                or (str == "t")
                or (str == "1")
            )
        except:
            if not default is None:
                val = default
            else:
                raise Exception(
                    'No boolean value specified for required keyword "{}" in block "{}".'.format(
                        key, group
                    )
                )
        return val

    def config_get_int(
        self,
        group: str,
        key: str,
        default: Optional[int] = None,
        positive: bool = False,
    ) -> int:
        """
        Get an integer from a selected group and keyword in the analysis settings.

        Arguments
        ---------
        group : str
            Name of the group from which to read.
        key : str
            Name of the keyword from which to read.
        default : Optional[int]
            Optional default value.
        positive : bool
            Flag specifying whether all integers are accepted (if False), or only strictly positive integers (if True).

        Raises
        ------
        Exception
            If the keyword isn't specified and no default value is given.
            If a negative or zero value is specified when a positive value is required.

        Returns
        -------
        val : int
            Integer value.
        """
        try:
            val = int(self._config[group][key])
        except:
            if not default is None:
                val = default
            else:
                raise Exception(
                    'No integer value specified for required keyword "{}" in block "{}".'.format(
                        key, group
                    )
                )
        if positive:
            if val <= 0:
                raise Exception(
                    'Value for "{}" in block "{}" must be positive, not {}.'.format(
                        key, group, val
                    )
                )
        return val

    def config_get_float(
        self,
        group: str,
        key: str,
        default: Optional[float] = None,
        positive: bool = False,
    ) -> float:
        """
        Get a floating point value from a selected group and keyword in the analysis settings.

        Arguments
        ---------
        group : str
            Name of the group from which to read.
        key : str
            Name of the keyword from which to read.
        default : Optional[float]
            Optional default value.
        positive : bool
            Flag specifying whether all floats are accepted (if False), or only positive floats (if True).

        Raises
        ------
        Exception
            If the keyword isn't specified and no default value is given.
            If a negative value is specified when a positive value is required.

        Returns
        -------
        val : float
            Floating point value.
        """
        try:
            val = float(self._config[group][key])
        except:
            if not default is None:
                val = default
            else:
                raise Exception(
                    'No floating point value specified for required keyword "{}" in block "{}".'.format(
                        key, group
                    )
                )
        if positive:
            if val < 0.0:
                raise Exception(
                    'Value for "{}" in block "{}" must be positive, not {}.'.format(
                        key, group, val
                    )
                )
        return val

    def config_get_str(
        self,
        group: str,
        key: str,
        default: Optional[str] = None,
    ) -> str:
        """
        Get a string from a selected group and keyword in the analysis settings.

        Arguments
        ---------
        group : str
            Name of the group from which to read.
        key : str
            Name of the keyword from which to read.
        default : Optional[str]
            Optional default value.

        Raises
        ------
        Exception
            If the keyword isn't specified and no default value is given.

        Returns
        -------
        val : str
            String.
        """
        try:
            val = self._config[group][key]
        except:
            if not default is None:
                val = default
            else:
                raise Exception(
                    'No value specified for required keyword "{}" in block "{}".'.format(
                        key, group
                    )
                )
        return val

    def config_get_range(
        self,
        group: str,
        key: str,
        default: Optional[Tuple[float,float]] = None,
    ) -> Tuple[float, float]:
        """
        Get a start and end value from a selected group and keyword in the analysis settings.

        Arguments
        ---------
        group : str
            Name of the group from which to read.
        key : str
            Name of the keyword from which to read.
        default : Optional[Tuple[float,float]]
            Optional default range.

        Returns
        -------
        val : Tuple[float,float]
            Lower and upper limit of the range.
        """
        try:
            ini_value = self.config_get_str(group, key, "")
            obrack = ini_value.find("[")
            cbrack = ini_value.find("]")
            if obrack >= 0 and cbrack >= 0:
                ini_value = ini_value[obrack + 1 : cbrack - 1]
            vallist = [float(fstr) for fstr in ini_value.split(":")]
            if vallist[0] > vallist[1]:
                val = (vallist[1], vallist[0])
            else:
                val = (vallist[0], vallist[1])
        except:
            if not default is None:
                val = default
            else:
                raise Exception(
                    'Invalid range specification "{}" for required keyword "{}" in block "{}".'.format(
                        ini_value, key, group
                    )
                )
        return val
