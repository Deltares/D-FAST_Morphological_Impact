# -*- coding: utf-8 -*-
"""
Copyright (C) 2020 Stichting Deltares.

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
import pathlib
import sys
import os
from dfastmi.batch.DFastUtils import get_progloc
import dfastmi.cli
import dfastmi.gui
import dfastmi.batch.core

from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.FileUtils import FileUtils
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper


def run(
    language: str = "UK",
    runmode: str = "GUI",
    configfile: str = "dfastmi.cfg",
    rivers_file: str = "Dutch_rivers_v2.ini",
    reduced_output: bool = False,
) -> None:
    """
    Main routine initializing the language file and starting the chosen run mode.
    
    Arguments
    ---------
    language: str
        Display language 'NL' or 'UK' ('UK' is default)
    runmode: str
        Run mode 'BATCH', 'CLI' or 'GUI' ('GUI' is default)
    configfile: str
        Configuration file ('dfastmi.cfg' is default)
    rivers_file : str
        Name of rivers configuration file ('Dutch_rivers_v2.ini' is default).
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only (False is default).
    """

    progloc = get_progloc()
    try:
        ApplicationSettingsHelper.load_program_texts(
            progloc + os.path.sep + "messages." + language + ".ini"
        )
    except:
        if language == "NL":
            print(
                "Het taalbestand 'messages."
                + language
                + ".ini' kan niet worden geladen."
            )
        else:
            print("Unable to load language file 'messages." + language + ".ini'")
    else:
        abs_rivers_file = str(pathlib.Path(progloc).absolute().joinpath(rivers_file))
        rivers = RiversObject(abs_rivers_file)
        if runmode == "BATCH":
            dfastmi.batch.core.batch_mode(configfile, rivers, reduced_output)
        elif runmode == "CLI":
            if configfile != "dfastmi.cfg":
                ApplicationSettingsHelper.log_text("ignoring_config")
            dfastmi.cli.interactive_mode(sys.stdin, rivers, reduced_output)
        elif runmode == "GUI":
            dfastmi.gui.main(rivers, configfile)
        else:
            raise Exception(
                'Invalid run mode "{}" specified. Should read "BATCH", "CLI" or "GUI".'.format(
                    runmode
                )
            )
