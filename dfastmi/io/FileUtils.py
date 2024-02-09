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
import os
import pathlib

class FileUtils:
    @staticmethod
    def absolute_path(rootdir: str, file: str) -> str:
        """
        Convert a relative path to an absolute path.

        Arguments
        ---------
        rootdir : str
            Any relative paths should be given relative to this location.
        file : str
            A relative or absolute location.

        Returns
        -------
        afile : str
            An absolute location.
        """
        if file == "":
            return file
        else:
            try:
                return os.path.normpath(os.path.join(rootdir, file))
            except:
                return file

    @staticmethod
    def relative_path(rootdir: str, file: str) -> str:
        """
        Convert an absolute path to a relative path.

        Arguments
        ---------
        rootdir : str
            Any relative paths will be given relative to this location.
        file : str
            An absolute location.

        Returns
        -------
        rfile : str
            An absolute or relative location (relative only if it's on the same drive as rootdir).
        """
        if file == "":
            return file
        else:
            try:
                rfile = os.path.relpath(file, rootdir)
                return rfile
            except:
                return file

    @staticmethod
    def get_progloc() -> str:
        """
        Get the location of the program.

        Arguments
        ---------
        None
        """
        progloc = str(pathlib.Path(__file__).parent.parent.absolute())
        return progloc