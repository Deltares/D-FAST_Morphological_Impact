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
import os
from packaging import version

from dfastmi.io.FileUtils import FileUtils

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
        for s in sections:
            options = config.options(s)
            if len(options) > 0:
                ml = max(ml, max([len(x) for x in options]))

        OPTIONLINE = "  {{:{}s}} = {{}}\n".format(ml)
        with open(filename, "w") as configfile:
            first = True
            for s in sections:
                if first:
                    first = False
                else:
                    configfile.write("\n")
                configfile.write("[{}]\n".format(s))
                options = config.options(s)
                for o in options:
                    configfile.write(OPTIONLINE.format(o, config[s][o]))

    @staticmethod
    def save_configuration_file(filename: str, config):
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
        rootdir = os.path.dirname(filename)
        config = ConfigFileOperations._config_to_relative_paths(rootdir, config)
        ConfigFileOperations.write_config(filename, config)
    
    @staticmethod
    def _config_to_relative_paths(
        rootdir: str, config: configparser.ConfigParser
    ) -> configparser.ConfigParser:
        """
        Convert a configuration object to contain relative paths (for saving).

        Arguments
        ---------
        rootdir : str
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
                ConfigFileOperations._update_to_relative_path(rootdir, config, "General", key)
        for qstr in config.keys():
            if "Reference" in config[qstr]:
                ConfigFileOperations._update_to_relative_path(rootdir, config, qstr, "Reference")
            if "WithMeasure" in config[qstr]:
                ConfigFileOperations._update_to_relative_path(rootdir, config, qstr, "WithMeasure")
        return config
    
    @staticmethod
    def _update_to_relative_path(rootdir : str, config : configparser.ConfigParser, section : str, key : str):
        """
        Convert a configuration object to contain absolute paths (for editing).
        Arguments
        ---------
        rootdir : str
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
        absolute_path_converted_to_relative_path = FileUtils.relative_path(rootdir, absolute_path)
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
        with open(filename, "r") as configfile:
            config.read_file(configfile)

        file_version = config.get("General", "Version", fallback= "")
        if len(file_version) == 0 :
            raise LookupError("No version information in the file!")

        if not (version.parse(file_version) == version.parse("1") or version.parse(file_version) == version.parse("2")):
            raise ValueError(f"Unsupported version number {file_version} in the file!")

        rootdir = os.path.dirname(filename)
        return ConfigFileOperations._config_to_absolute_paths(rootdir, config)

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
                ConfigFileOperations._update_to_absolute_path(rootdir, config, "General", key)
        for qstr in config.keys():
            if "Reference" in config[qstr]:
                ConfigFileOperations._update_to_absolute_path(rootdir, config, qstr, "Reference")
            if "WithMeasure" in config[qstr]:
                ConfigFileOperations._update_to_absolute_path(rootdir, config, qstr, "WithMeasure")
        return config
    
    @staticmethod
    def _update_to_absolute_path(rootdir : str, config : configparser.ConfigParser, section : str, key : str):
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
        relative_path_converted_to_absolute_path = FileUtils.absolute_path(rootdir, relative_path)
        config.set(section, key, relative_path_converted_to_absolute_path)
