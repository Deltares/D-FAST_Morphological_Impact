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

# ------------------------------------------------------------------------------
# Needed for Nuitka compilation
# ------------------------------------------------------------------------------
import os
import pathlib
from typing import Optional, Tuple

is_nuitka = "__compiled__" in globals()
if is_nuitka:
    root = str(pathlib.Path(__file__).parent)
    os.environ["GDAL_DATA"] = root + os.sep + "gdal"
    os.environ["PROJ_LIB"] = root + os.sep + "proj"
    os.environ["MATPLOTLIBDATA"] = root + os.sep + "matplotlib" + os.sep + "mpl-data"
    os.environ["TCL_LIBRARY"] = root + os.sep + "lib" + os.sep + "tcl8.6"
    proj_lib_dirs = os.environ.get("PROJ_LIB", "")
    import pyproj.datadir

    pyproj.datadir.set_data_dir(root + os.sep + "proj")
    import pyproj

import argparse

import _ctypes
import cftime
import fiona.enums
import fiona.ogrext
import fiona.schema
import netCDF4.utils
import pandas._libs.tslibs.base
import shapely._geos
import six

import dfastmi.cmd

# ------------------------------------------------------------------------------


def parse_arguments() -> Tuple[str, str, Optional[str], str, bool]:
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
    language : str
        Language identifier ("NL" or "UK").
    runmode : str
        Specification of the run mode ("BATCH", "CLI" or "GUI")
    config_name : Optional[str]
        Name of the analysis configuration file (optional).
    rivers_file : str
        Name of rivers configuration file.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    """
    parser = argparse.ArgumentParser(description="D-FAST Morphological Impact.")

    parser.add_argument(
        "--language",
        choices=["UK", "NL"],
        default="UK",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--mode",
        choices=["CLI", "BATCH", "GUI"],
        default="GUI",
        help="run mode 'BATCH' or 'GUI' (%(default)s is default)",
    )

    parser.add_argument(
        "--config",
        default="dfastmi.cfg",
        help="name of analysis configuration file ('%(default)s' is default)",
    )

    parser.add_argument(
        "--rivers",
        default="unspecified",
        help="name of rivers configuration file ('Dutch_rivers_v2.ini' is default)",
    )

    parser.add_argument(
        "--reduced_output",
        help=argparse.SUPPRESS,
        action="store_true",
    )
    parser.set_defaults(reduced_output=False)
    args = parser.parse_args()

    language = args.__dict__["language"].upper()
    runmode = args.__dict__["mode"].upper()
    config = args.__dict__["config"]
    rivers_file = args.__dict__["rivers"]
    reduced_output = args.__dict__["reduced_output"]
    if rivers_file == "unspecified":
        if runmode == "CLI":
            rivers_file = "Dutch_rivers_v1.ini"
        else:
            rivers_file = "Dutch_rivers_v2.ini"

    if language not in ["NL", "UK"]:
        raise LookupError(
            f'Incorrect language "{language}" specified. Should read "NL" or "UK".'
        )
    return language, runmode, config, rivers_file, reduced_output


if __name__ == "__main__":
    language, runmode, config, rivers_file, reduced_output = parse_arguments()
    dfastmi.cmd.run(language, runmode, config, rivers_file, reduced_output)
