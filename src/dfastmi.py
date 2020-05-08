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

import logging
import argparse
from pathlib import Path
import dfastmi_kernel


def parse_arguments():
    parser = argparse.ArgumentParser(description="D-FAST Morphological Change.")
    parser.add_argument(
        "-i",
        "--inputfile",
        default="",
        required=True,
        help="name of configuration file",
        dest="input_file",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default="INFO",
        required=False,
        help="set verbosity level of run-time diagnostics (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        dest="verbosity",
    )
    args = parser.parse_args()

    verbosity = args.__dict__["verbosity"].upper()
    verbosity_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if not verbosity in verbosity_levels:
        raise SystemExit('Unknown verbosity level "' + verbosity + '"')

    input_file = args.__dict__["input_file"]
    input_path = Path(input_file).resolve()
    if not input_path.is_file():
        raise SystemExit('Configuration File "' + input_file + '" does not exist!')

    return verbosity, input_file


if __name__ == "__main__":
    verbosity, input_file = parse_arguments()
    logging.basicConfig(level=verbosity, format="%(message)s")
    dfastmi_kernel.main_program(input_file)
