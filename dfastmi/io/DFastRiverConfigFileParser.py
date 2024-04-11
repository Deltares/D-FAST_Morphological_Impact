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
from configparser import ConfigParser
from typing import Tuple, Union

from dfastmi.io.DFastAnalysisConfigFileParser import DFastAnalysisConfigFileParser
from dfastmi.io.IReach import IReach


class DFastRiverConfigFileParser:
    """A parser class for parsing DFAST river config files.

    This parser utilizes a layered approach to extract configuration values, allowing
    for default values at the general, branch, and reach-specific levels.
    """

    _general_section: str = "General"

    def __init__(self, config_parser: ConfigParser):
        """Initializes a DFastRiverConfigFileParser with a ConfigParser instance.

        Args:
            config_parser (ConfigParser): A ConfigParser that has read a DFAST river config file.
        """
        self._parser = DFastAnalysisConfigFileParser(config_parser)

    def getint(self, key: str, reach: IReach, fallback: int = 0) -> int:
        """Attempts to retrieve an integer value from the configuration for a specific key and reach.

        The retrieval process looks up values in the following order: general section, branch section,
        and finally a specific reach in the branch section. This allows more specific configurations
        to override more general ones.

        Args:
            key (str): The configuration key.
            reach (IReach): The reach object to find the value for.
            fallback (int, optional): The fallback value if the key is not found. Defaults to 0.

        Returns:
            int: The retrieved integer value.
        """
        general_value = self._try_get_int_from_general_section(key, fallback)
        branch_value = self._try_get_int_from_branch_section(
            key, reach.parent_branch.name, general_value
        )
        reach_value = self._try_get_int_from_reach_section(
            key, reach.parent_branch.name, reach.config_key_index, branch_value
        )

        return reach_value

    def getfloat(self, key: str, reach: IReach, fallback: float = 0.0) -> float:
        """Attempts to retrieve a float value from the configuration for a specific key and reach.

        The retrieval process looks up values in the following order: general section, branch section,
        and finally a specific reach in the branch section. This allows more specific configurations
        to override more general ones.

        Args:
            key (str): The configuration key.
            reach (IReach): The reach object to find the value for.
            fallback (float, optional): The fallback value if the key is not found. Defaults to 0.0.

        Returns:
            float: The retrieved float value.
        """
        general_value = self._try_get_float_from_general_section(key, fallback)
        branch_value = self._try_get_float_from_branch_section(
            key, reach.parent_branch.name, general_value
        )
        reach_value = self._try_get_float_from_reach_section(
            key, reach.parent_branch.name, reach.config_key_index, branch_value
        )

        return reach_value

    def getboolean(self, key: str, reach: IReach, fallback: bool = False) -> bool:
        """Attempts to retrieve a boolean value from the configuration for a specific key and reach.

        The retrieval process looks up values in the following order: general section, branch section,
        and finally a specific reach in the branch section. This allows more specific configurations
        to override more general ones.

        Args:
            key (str): The configuration key.
            reach (IReach): The reach object to find the value for.
            fallback (bool, optional): The fallback value if the key is not found. Defaults to False.

        Returns:
            bool: The retrieved boolean value.
        """
        general_value = self._try_get_boolean_from_general_section(key, fallback)
        branch_value = self._try_get_boolean_from_branch_section(
            key, reach.parent_branch.name, general_value
        )
        reach_value = self._try_get_boolean_from_reach_section(
            key, reach.parent_branch.name, reach.config_key_index, branch_value
        )

        return reach_value

    def getstring(self, key: str, reach: IReach, fallback: str = "") -> str:
        """Attempts to retrieve a string value from the configuration for a specific key and reach.

        The retrieval process looks up values in the following order: general section, branch section,
        and finally a specific reach in the branch section. This allows more specific configurations
        to override more general ones.

        Args:
            key (str): The configuration key.
            reach (IReach): The reach object to find the value for.
            fallback (str, optional): The fallback value if the key is not found. Defaults to "".

        Returns:
            str: The retrieved string value.
        """
        general_value = self._try_get_string_from_general_section(key, fallback)
        branch_value = self._try_get_string_from_branch_section(
            key, reach.parent_branch.name, general_value
        )
        reach_value = self._try_get_string_from_reach_section(
            key, reach.parent_branch.name, reach.config_key_index, branch_value
        )

        return reach_value

    def getfloats(
        self,
        key: str,
        reach: IReach,
        fallback: Tuple[float, ...] = (),
        expected_number_of_values: Union[None, int] = None,
    ) -> Tuple[float, ...]:
        """Attempts to retrieve a tuple of floats from the configuration for a specific key and reach.

        The retrieval process looks up values in the following order: general section, branch section,
        and finally a specific reach in the branch section. This allows more specific configurations
        to override more general ones.

        Args:
            key (str): The configuration key.
            reach (IReach): The reach object to find the value for.
            fallback (Tuple[float, ...], optional): The fallback value if the key is not found. Defaults to ().
            expected_number_of_values (Union[None, int], optional): The expected length of the tuple. Defaults to None.

        Returns:
            Tuple[float, ...]: The retrieved tuple of floats.

        Raises:
            Exception: If the number of retrieved values does not match `expected_number_of_values`.
        """
        general_value = self._try_get_values_from_general_section(key, "")
        branch_value = self._try_get_values_from_branch_section(
            key, reach.parent_branch.name, general_value
        )
        reach_value = self._try_get_values_from_reach_section(
            key, reach.parent_branch.name, reach.config_key_index, branch_value
        )

        return_values = self._parse_floats(reach_value)
        if len(return_values) == 0 and fallback is not None:
            return_values = fallback

        if (
            expected_number_of_values is not None
            and len(return_values) != expected_number_of_values
        ):
            self._raise_exception_incorrect_value_entries(
                key,
                reach.name,
                reach.parent_branch.name,
                reach_value,
                expected_number_of_values,
            )

        return return_values

    def getstrings(
        self,
        key: str,
        reach: IReach,
        fallback: Tuple[str, ...] = (),
        expected_number_of_values: Union[None, int] = None,
    ) -> Tuple[str, ...]:
        """Attempts to retrieve a tuple of strings from the configuration for a specific key and reach.

        The retrieval process looks up values in the following order: general section, branch section,
        and finally a specific reach in the branch section. This allows more specific configurations
        to override more general ones.

        Args:
            key (str): The configuration key.
            reach (IReach): The reach object to find the value for.
            fallback (Tuple[str, ...], optional): The fallback value if the key is not found. Defaults to ().
            expected_number_of_values (Union[None, int], optional): The expected length of the tuple. Defaults to None.

        Returns:
            Tuple[str, ...]: The retrieved tuple of strings.

        Raises:
            Exception: If the number of retrieved values does not match `expected_number_of_values`.
        """
        general_value = self._try_get_values_from_general_section(key, "")
        branch_value = self._try_get_values_from_branch_section(
            key, reach.parent_branch.name, general_value
        )
        reach_value = self._try_get_values_from_reach_section(
            key, reach.parent_branch.name, reach.config_key_index, branch_value
        )

        return_values = self._parse_strings(reach_value)
        if len(return_values) == 0 and fallback is not None:
            return_values = fallback

        if (
            expected_number_of_values is not None
            and len(return_values) != expected_number_of_values
        ):
            self._raise_exception_incorrect_value_entries(
                key,
                reach.name,
                reach.parent_branch.name,
                reach_value,
                expected_number_of_values,
            )

        return return_values

    def _try_get_int_from_general_section(self, key: str, fallback: int) -> int:
        return self._parser.getint(self._general_section, key, fallback)

    def _try_get_int_from_branch_section(
        self, key: str, parent_branch: str, fallback: int
    ) -> int:
        return self._parser.getint(parent_branch, key, fallback)

    def _try_get_int_from_reach_section(
        self, key: str, branch_name: str, reach_index: int, fallback: int
    ) -> int:
        return self._parser.getint(branch_name, f"{key}{reach_index}", fallback)

    def _try_get_float_from_general_section(self, key: str, fallback: float) -> float:
        return self._parser.getfloat(self._general_section, key, fallback)

    def _try_get_float_from_branch_section(
        self, key: str, parent_branch: str, fallback: float
    ) -> float:
        return self._parser.getfloat(parent_branch, key, fallback)

    def _try_get_float_from_reach_section(
        self, key: str, branch_name: str, reach_index: int, fallback: float
    ) -> float:
        return self._parser.getfloat(branch_name, f"{key}{reach_index}", fallback)

    def _try_get_string_from_general_section(self, key: str, fallback: str) -> str:
        return self._parser.getstring(self._general_section, key, fallback)

    def _try_get_string_from_branch_section(
        self, key: str, parent_branch: str, fallback: str
    ) -> str:
        return self._parser.getstring(parent_branch, key, fallback)

    def _try_get_string_from_reach_section(
        self, key: str, branch_name: str, reach_index: int, fallback: str
    ) -> str:
        return self._parser.getstring(branch_name, f"{key}{reach_index}", fallback)

    def _try_get_boolean_from_general_section(self, key: str, fallback: bool) -> bool:
        return self._parser.getboolean(self._general_section, key, fallback)

    def _try_get_boolean_from_branch_section(
        self, key: str, parent_branch: str, fallback: bool
    ) -> bool:
        return self._parser.getboolean(parent_branch, key, fallback)

    def _try_get_boolean_from_reach_section(
        self, key: str, branch_name: str, reach_index: int, fallback: bool
    ) -> bool:
        return self._parser.getboolean(branch_name, f"{key}{reach_index}", fallback)

    def _try_get_values_from_general_section(self, key: str, fallback: str) -> str:
        return self._parser.getstring(self._general_section, key, fallback)

    def _try_get_values_from_branch_section(
        self, key: str, name: str, fallback: str
    ) -> str:
        return self._parser.getstring(name, key, fallback)

    def _try_get_values_from_reach_section(
        self, key: str, branch_name: str, reach_index: int, fallback: str
    ) -> str:
        return self._parser.getstring(branch_name, f"{key}{reach_index}", fallback)

    @staticmethod
    def _parse_floats(floats_as_string: str) -> Tuple[float, ...]:
        return tuple(float(x) for x in floats_as_string.split())

    @staticmethod
    def _parse_strings(string_values) -> Tuple[str, ...]:
        return tuple(x for x in string_values.split())

    def _raise_exception_incorrect_value_entries(
        self, key, reach_name, branch_name, entry_value, expected_number_of_values
    ):
        raise Exception(
            f'Reading {key} for reach {reach_name} on {branch_name} returns "{entry_value}". Expecting {expected_number_of_values} values.'
        )
