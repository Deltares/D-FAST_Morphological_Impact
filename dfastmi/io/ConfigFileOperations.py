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
