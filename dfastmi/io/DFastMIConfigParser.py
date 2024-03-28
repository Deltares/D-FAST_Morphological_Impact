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
from typing import Callable, Tuple, Type, TypeVar, Optional
from dfastmi.io.ConfigProcessor import ConfigProcessor
from dfastmi.io.AReach import AReach
from dfastmi.io.RiverConfigElementProcessor import RiverConfigElementProcessor


T = TypeVar('T')  # Define a type variable


class DFastMIConfigParser:
    """
    Class to process and parse both river and DFast MI application config files
    """
    _config: configparser.ConfigParser
    """ 
        The dictionary containing river data.
    """
    
    _processor : RiverConfigElementProcessor
    """
        Element processer object containing processing functions and parser methods per data type
        to retrieve River elements using DFast MI DTO Reach and branch from river config (files)
    """

    _config_processor : ConfigProcessor
    """
        Element processer object containing parser methods per data type
        to retrieve DFast MI key value from DFast MI config (files)
    """
    

    def __init__(self, config: configparser.ConfigParser):
        self._config = config
        self._processor = RiverConfigElementProcessor()
        self._processor.register_processor(bool, self._process_entry_value, self._parse_bool)
        self._processor.register_processor(int, self._process_entry_value, self._parse_int)
        self._processor.register_processor(float, self._process_entry_value, self._parse_float)
        self._processor.register_processor(Tuple[float, ...], self._process_tuple_entry_value, self._parse_float)
        self._processor.register_processor(Tuple[str, ...], self._process_tuple_entry_value, self._parse_str)
        self._config_processor = ConfigProcessor()
        self._config_processor.register_parser(bool, self._parse_bool)
        self._config_processor.register_parser(int, self._parse_int)
        self._config_processor.register_parser(float, self._parse_float)
        self._config_processor.register_parser(str, lambda input: [input])

    def _read_value(self, key: str, branch_name: str, reach_index: int):
        """
        reads the value from the general section, branch section or the reach section key
        """
        general_value = self._config.get("General", key, fallback='')
        branch_val = self._config.get(branch_name, key, fallback=general_value)
        val = self._config.get(branch_name, key + str(reach_index), fallback=branch_val)
        return val

    # default processor
    def _process_entry_value(self, key, entry_value: str, reach : AReach, parse: Callable[[str], Tuple[T, ...]], default: Optional[T], expected_number_of_values : Optional[int]) -> T:
        if entry_value == "" and default is not None:
            value_from_config = default
        else:
            try:
                vals = parse(entry_value)
            except:
                vals = ()

            if expected_number_of_values is None:
                expected_number_of_values = 1

            if len(vals) != expected_number_of_values:
                self._raise_exception_incorrect_value_entries(key, reach.name, reach.parent_branch.name, entry_value, expected_number_of_values)
            value_from_config = vals[0]
        return value_from_config

    def _parse_bool(self, entry_value) -> Tuple[bool, ...]:
        return tuple(x.lower() in ['true', '1', 't', 'y', 'yes'] for x in entry_value.split())

    def _parse_int(self, entry_value) -> Tuple[int, ...]:
        return tuple(int(x) for x in entry_value.split())

    def _parse_float(self, entry_value) -> Tuple[float, ...]:
        return tuple(float(x) for x in entry_value.split())

    def _parse_str(self, entry_value) -> Tuple[str, ...]:
        return tuple(x for x in entry_value.split())

    # tuple processor
    def _process_tuple_entry_value(self, key, entry_value: str, reach : AReach, parse: Callable[[str], Tuple[T, ...]], default: Optional[Tuple[T, ...]], expected_number_of_values : Optional[int]) -> Tuple[T, ...]:
        vals: Tuple[T, ...]
        if entry_value == "" and default is not None:
            vals = default
        else:
            try:
                vals = parse(entry_value)
            except:
                vals = ()

            if expected_number_of_values is not None:
                if len(vals) != expected_number_of_values:
                    self._raise_exception_incorrect_value_entries(key, reach.name, reach.parent_branch.name, entry_value, expected_number_of_values)
        return vals

    def read_key(
            self,
            value_type: Type[T],
            key: str,
            reach: AReach,
            default: Optional[T] = None,
            expected_number_of_values: Optional[int] = None
        ) -> T:
        """
        This routines collects entries of type int.

        Arguments
        ---------
        key : str
            The name of the parameter for which the values are to be retrieved.
        branch : Branch
            The branch where we want to read the parameter from


        Raises
        ------
        Exception
            If the number of values read from the file doesn't match 1.

        Returns
        -------
        data : int
            A list of lists. Each list contains per reach within the corresponding
            branch one float.
        """
        entry_value = self._read_value(key, reach.parent_branch.name, reach.config_key_index)
        return self._processor.process_river_element(value_type, key, entry_value, reach, default, expected_number_of_values)

    def _raise_exception_incorrect_value_entries(self, key, reach_name, branch_name, entry_value, expected_number_of_values):
        raise Exception(f'Reading {key} for reach {reach_name} on {branch_name} returns "{entry_value}". Expecting {expected_number_of_values} values.')

    def config_get(
        self,
        value_type: Type[T],
        group: str,
        key: str,
        default: Optional[T] = None,
        positive: bool = False
    ) -> T:
        """
        Get a value from a selected group and keyword in the analysis settings.

        Arguments
        ---------
        group : str
            Name of the group from which to read.
        key : str
            Name of the keyword from which to read.
        default : Optional[T]
            Optional default value.

        positive : bool
            Flag specifying whether all values are accepted (if False), or only strictly positive values (if True).

        Raises
        ------
        Exception
            If the keyword isn't specified and no default value is given.
            If a negative or zero value is specified when a positive value is required.

        Returns
        -------
        val : T
            Provided value type.
        """
        try:
            if value_type is str:
                entry_value = self._config[group][key]
            else:
                entry_value = self._config[group][key].lower()
            val = self._config_processor.process_config_value(value_type, entry_value)[0]
        except:
            if default is not None:
                val = default
            else:
                raise Exception(f'No {value_type.__name__} value specified for required keyword "{key}" in block "{group}".')

        if positive:
            if val <= 0:
                raise Exception(f'Value for "{key}" in block "{group}" must be positive, not {val}.')
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
            ini_value = self.config_get(str, group, key, "")
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