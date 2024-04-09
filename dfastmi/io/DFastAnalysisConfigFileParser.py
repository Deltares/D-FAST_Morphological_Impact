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
from typing import Tuple


class DFastAnalysisConfigFileParser:
    """A parser class for parsing DFAST analysis config files."""

    def __init__(self, config_parser: ConfigParser):
        """Initializes the DFastAnalysisConfigFileParser with a ConfigParser instance.

        Args:
            config_parser (ConfigParser): A ConfigParser that has read a DFAST analysis file.
        """
        self._config_parser = config_parser
        self._configure_booleans()

    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Retrieves an integer value from the configuration.

        Args:
            section (str): The configuration section name.
            key (str): The configuration key within the specified section.
            fallback (int, optional): The fallback value if the key is not found. Defaults to 0.

        Returns:
            int: The integer value of the configuration key.

        Raises:
            Exception: When the given section or key does not exist.
        """
        return self._config_parser.getint(section, key, fallback=fallback)

    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Retrieves a float value from the configuration.

        Args:
            section (str): The configuration section name.
            key (str): The configuration key within the specified section.
            fallback (float, optional): The fallback value if the key is not found. Defaults to 0.0.

        Returns:
            float: The float value of the configuration key.

        Raises:
            Exception: When the given section or key does not exist.
        """
        return self._config_parser.getfloat(section, key, fallback=fallback)

    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Retrieves a boolean value from the configuration.

        Args:
            section (str): The configuration section name.
            key (str): The configuration key within the specified section.
            fallback (bool, optional): The fallback value if the key is not found. Defaults to False.

        Returns:
            bool: The boolean value of the configuration key.

        Raises:
            Exception: When the given section or key does not exist.
        """
        return self._config_parser.getboolean(section, key, fallback=fallback)

    def getstring(self, section: str, key: str, fallback: str = "") -> str:
        """Retrieves a string value from the configuration.

        Args:
            section (str): The configuration section name.
            key (str): The configuration key within the specified section.
            fallback (str, optional): The fallback value if the key is not found. Defaults to an empty string.

        Returns:
            str: The string value of the configuration key.
        """
        return self._config_parser.get(section, key, fallback=fallback)

    def get_range(
        self, section: str, key: str, fallback: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Retrieves a range (tuple of two floats) from the configuration.

        The range is specified in the configuration file in the format "[x:y]", where
        x and y are floats. This method parses that format and returns a tuple of two floats.

        Args:
            section (str): The configuration section name.
            key (str): The configuration key within the specified section.
            fallback (Tuple[float, float]): The fallback value if the key is not found or parsing fails.

        Returns:
            Tuple[float, float]: The range specified by the configuration key as a tuple of two floats.

        Raises:
            Exception: If parsing fails and no fallback is provided.
        """
        try:
            ini_value = self.getstring(section, key, "")
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
            if fallback is not None:
                val = fallback
            else:
                raise Exception(
                    f'Invalid range specification "{ini_value}" for required keyword "{key}" in block "{section}".'
                )

        return val

    def _configure_booleans(self):
        self._config_parser.BOOLEAN_STATES = {
            "1": True,
            "yes": True,
            "true": True,
            "on": True,
            "t": True,
            "y": True,
            "0": False,
            "no": False,
            "false": False,
            "off": False,
            "f": False,
            "n": False,
        }
