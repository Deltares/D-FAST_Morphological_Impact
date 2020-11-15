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

from typing import Optional, Tuple

import argparse
import sys
import os
import numpy
import dfastmi.cli
import dfastmi.gui
import dfastmi.io
import pathlib


def parse_arguments() -> Tuple[bool, str, str, Optional[str]]:
    """
    Parse the command line arguments.

    Arguments
    ---------
    None

    Raises
    ------
    Exception
        If invalid language is specified.

    Returns
    -------
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    language : str
        Language identifier ("NL" or "UK").
    runmode : str
        Specification of the run mode ("BATCH", "CLI" or "GUI")
    config_name : Optional[str]
        Name of the configuration file (optional).
    """
    parser = argparse.ArgumentParser(description="D-FAST Morphological Impact.")
    parser.add_argument(
        "--language", help="display language 'NL' or 'UK' (UK is default)"
    )
    parser.set_defaults(language="UK")
    parser.add_argument(
        "--mode", help="run mode 'BATCH', 'CLI' or 'GUI' (GUI is default)"
    )
    parser.set_defaults(mode="GUI")
    parser.add_argument(
        "--config", help="name of configuration file (required for BATCH mode)"
    )
    parser.set_defaults(config=None)
    parser.add_argument(
        "--reduced_output",
        help="write reduced M/N range (structured model only)",
        action="store_true",
    )
    parser.set_defaults(reduced_output=False)
    args = parser.parse_args()

    reduced_output = args.__dict__["reduced_output"]
    language = args.__dict__["language"].upper()
    runmode = args.__dict__["mode"].upper()
    config = args.__dict__["config"]
    if language not in ["NL", "UK"]:
        raise Exception(
            'Incorrect language "{}" specified. Should read "NL" or "UK".'.format(
                language
            )
        )
    return reduced_output, language, runmode, config


if __name__ == "__main__":
    reduced_output, language, runmode, config = parse_arguments()

    progloc = str(pathlib.Path(__file__).parent.absolute())
    try:
        dfastmi.io.load_program_texts(
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
        rivers = dfastmi.io.read_rivers(progloc + os.path.sep + "rivers.ini")
        if runmode == "BATCH":
            if config is None:
                dfastmi.cli.log_text("missing_config")
            else:
                dfastmi.batch.batch_mode(config, rivers, reduced_output)
        elif runmode == "CLI":
            if not config is None:
                dfastmi.cli.log_text("ignoring_config")
            dfastmi.cli.interactive_mode(sys.stdin, rivers, reduced_output)
        elif runmode == "GUI":
            dfastmi.gui.main(rivers, config)
        else:
            raise Exception(
                'Invalid run mode "{}" specified. Should read "BATCH", "CLI" or "GUI".'.format(
                    runmode
                )
            )
