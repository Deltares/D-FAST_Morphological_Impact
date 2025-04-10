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
import os
from configparser import ConfigParser
from pathlib import Path

from packaging.version import Version

from dfastmi.config.ConfigurationCheckerFactory import ConfigurationCheckerFactory
from dfastmi.io.RiversObject import RiversObject


class ConfigFileOperations:
    @staticmethod
    def write_config(filename: str, config: configparser.ConfigParser) -> None:
        """Pretty print a configParser object (configuration file) to file.

        This function ...
            aligns the equal signs for all keyword/value pairs.
            adds a two space indentation to all keyword lines.
            adds an empty line before the start of a new block.

        Arguments
        ---------
        filename : str
            Name of the configuration file to be written.
        config : configparser.ConfigParser
            The variable containing the configuration.
        """
        sections = config.sections()
        ml = 0
        for section in sections:
            options = config.options(section)
            if len(options) > 0:
                ml = max(ml, max([len(x) for x in options]))

        OPTIONLINE = "  {{:{}s}} = {{}}\n".format(ml)
        with Path(filename).open("w", encoding="utf-8") as configfile:
            first = True
            for section in sections:
                if first:
                    first = False
                else:
                    configfile.write("\n")
                configfile.write(f"[{section}]\n")
                options = config.options(section)
                for o in options:
                    configfile.write(OPTIONLINE.format(o, config[section][o]))

    @staticmethod
    def save_configuration_file(filename: str, config: ConfigParser) -> None:
        """
        Convert a configuration to relative paths and save to file.

        Arguments
        ---------
        filename : str
            The name of the configuration file to be saved.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis to be saved.

        Returns
        -------
        None
        """
        rootdir = Path(filename).parent
        config = ConfigFileOperations._config_to_relative_paths(rootdir, config)
        ConfigFileOperations.write_config(filename, config)

    @staticmethod
    def _config_to_relative_paths(
        rootdir: Path, config: configparser.ConfigParser
    ) -> configparser.ConfigParser:
        """
        Convert a configuration object to contain relative paths (for saving).

        Arguments
        ---------
        rootdir : Path
            The path to be used as base for the absolute paths.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with only absolute paths.

        Returns
        -------
        rconfig : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with as much as possible relative paths.
        """
        for key in ("RiverKM", "FigureDir", "OutputDir"):
            if key in config["General"]:
                ConfigFileOperations._update_to_relative_path(
                    rootdir, config, "General", key
                )
        for qstr in config.keys():
            if "Reference" in config[qstr]:
                ConfigFileOperations._update_to_relative_path(
                    rootdir, config, qstr, "Reference"
                )
            if "WithIntervention" in config[qstr]:
                ConfigFileOperations._update_to_relative_path(
                    rootdir, config, qstr, "WithIntervention"
                )
        return config

    @staticmethod
    def _update_to_relative_path(
        rootdir: Path, config: configparser.ConfigParser, section: str, key: str
    ):
        """
        Convert a configuration object to contain absolute paths (for editing).
        Arguments
        ---------
        rootdir : Path
            The path to be used as base for the absolute paths.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with absolute paths
            to be converted to relative paths.
        section : str
            Where in the configuration we need to update the absolute path
        key : str
            Where in the configuration we need to update the absolute path

        Returns
        -------
        aconfig : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with only relative paths.
        """
        absolute_path = config.get(section, key, fallback="")

        if len(absolute_path) == 0:
            absolute_path_converted_to_relative_path = ""
        else:
            try:
                absolute_path_converted_to_relative_path = str(
                    os.path.relpath(absolute_path, rootdir)
                )
            except ValueError:
                absolute_path_converted_to_relative_path = absolute_path

        config.set(section, key, absolute_path_converted_to_relative_path)

    @staticmethod
    def load_configuration_file(filename: str) -> configparser.ConfigParser:
        """
        Open a configuration file and return a configuration object with absolute paths.

        Arguments
        ---------
        filename : str
            The name of the file: all relative paths in the configuration will be assumed relative to this.

        Raises
        ------
        Exception
            If the configuration file does not include version information.
            If the version number in the configuration file is not equal to 1.0.

        Returns
        -------
        aconfig : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with only absolute paths.
        """
        config = configparser.ConfigParser()
        config.optionxform = str
        with Path(filename).open("r", encoding="utf-8") as configfile:
            config.read_file(configfile)

        config = ConfigFileOperations._config_case_check(config)
        file_version = config.get("General", "Version", fallback="")
        if len(file_version) == 0:
            raise LookupError("No version information in the file!")

        if not (
            Version(file_version) == Version("1")
            or Version(file_version) == Version("2")
            or Version(file_version) == Version("3")
        ):
            raise ValueError(f"Unsupported version number {file_version} in the file!")

        rootdir = os.path.dirname(filename)
        return ConfigFileOperations._config_to_absolute_paths(rootdir, config)

    @staticmethod
    def _config_case_check(
        config: configparser.ConfigParser,
    ) -> configparser.ConfigParser:
        config = ConfigFileOperations._config_case_check_section(config, "General")
        for key in [
            "Version",
            "CaseDescription",
            "Branch",
            "Reach",
            "Qthreshold",
            "Ucrit",
            "OutputDir",
            "Plotting",
            "SavePlots",
            "FigureDir",
            "ClosePlots",
            "RiverKM",
        ]:
            config = ConfigFileOperations._config_case_check_key(config, "General", key)

        return config

    @staticmethod
    def _config_case_check_section(
        config: configparser.ConfigParser, section: str
    ) -> configparser.ConfigParser:
        lower_section = section.lower()
        if not config.has_section(section):
            matching_sections = [
                s for s in config.sections() if s.lower() == lower_section
            ]
            if len(matching_sections) == 0:
                raise LookupError("No " + section + " block in the file!")
            elif len(matching_sections) > 1:
                raise LookupError("Multiple " + section + " blocks in the file!")
            else:
                config[section] = config[matching_sections[0]]
                config.remove_section(matching_sections[0])

        return config

    @staticmethod
    def _config_case_check_key(
        config: configparser.ConfigParser, section: str, key: str
    ) -> configparser.ConfigParser:
        sec = config[section]
        lower_key = key.lower()
        if not config.has_option(section, key):
            matching_keys = [k for k in sec.keys() if k.lower() == lower_key]
            if len(matching_keys) == 0:
                return config  # all keys considered optional at this level
            elif len(matching_keys) > 1:
                raise LookupError(
                    "Multiple keys " + key + " found in the block " + section + "!"
                )
            else:
                sec[key] = sec[matching_keys[0]]
                config.remove_option(section, matching_keys[0])

        return config

    @staticmethod
    def _config_to_absolute_paths(
        rootdir: str, config: configparser.ConfigParser
    ) -> configparser.ConfigParser:
        """
        Convert a configuration object to contain absolute paths (for editing).

        Arguments
        ---------
        rootdir : str
            The path to be used as base for the absolute paths.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with absolute or relative paths.

        Returns
        -------
        aconfig : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with only absolute paths.
        """
        for key in ("RiverKM", "FigureDir", "OutputDir"):
            if key in config["General"]:
                ConfigFileOperations._update_to_absolute_path(
                    rootdir, config, "General", key
                )
        for qstr in config.keys():
            if "Reference" in config[qstr]:
                ConfigFileOperations._update_to_absolute_path(
                    rootdir, config, qstr, "Reference"
                )
            if "WithIntervention" in config[qstr]:
                ConfigFileOperations._update_to_absolute_path(
                    rootdir, config, qstr, "WithIntervention"
                )
        return config

    @staticmethod
    def _update_to_absolute_path(
        rootdir: str, config: configparser.ConfigParser, section: str, key: str
    ):
        """
        Convert a configuration object to contain absolute paths (for editing).
        Arguments
        ---------
        rootdir : str
            The path to be used as base for the absolute paths.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with relative paths
            to be converted to absolute paths.
        section : str
            Where in the configuration we need to update the relative path
        key : str
            Where in the configuration we need to update the relative path

        Returns
        -------
        aconfig : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis with only absolute paths.
        """
        relative_path = config.get(section, key, fallback="")

        absolute_path = ConfigFileOperations._get_absolute_path_from_relative_path(
            rootdir, relative_path
        )

        config.set(section, key, absolute_path)

    @staticmethod
    def _get_absolute_path_from_relative_path(rootdir: str, relative_path: str) -> str:
        if len(relative_path) == 0:
            return relative_path

        absolute_path = str(Path(rootdir).joinpath(Path(relative_path)).resolve())
        return absolute_path


def check_configuration(rivers: RiversObject, config: ConfigParser) -> bool:
    """
    Check if an analysis configuration is valid.

    Arguments
    ---------
    rivers: RiversObject
        An object containing the river data.
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis.

    Returns
    -------
    success : bool
        Boolean indicating whether the D-FAST MI analysis configuration is valid.
    """
    cfg_version = config.get("General", "Version", fallback=None)

    try:
        configuration_version = Version(cfg_version)
        configuration_checker = ConfigurationCheckerFactory.generate(
            configuration_version
        )
        return configuration_checker.check_configuration(rivers, config)
    except (SystemExit, KeyboardInterrupt) as exception:
        raise exception
    except:
        return False
