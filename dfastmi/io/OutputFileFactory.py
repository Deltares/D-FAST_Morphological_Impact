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

from pathlib import Path
from typing import Callable

from dfastmi.io.FouFile import FouFile
from dfastmi.io.MapFile import MapFile
from dfastmi.io.OutputFile import OutputFile


class OutputFileFactory:
    """
    Class is used to register and get creation of OutputFile Objects
    """

    _creators = {}
    """Contains the OutputFile Objects creators to be used"""

    @staticmethod
    def register_creator(
        file_name_suffix: str,
        creator: Callable[[bool], OutputFile],
    ):
        """Register creator function to create a OutputFile object."""
        if file_name_suffix not in OutputFileFactory._creators:
            OutputFileFactory._creators[file_name_suffix] = creator
    
    @staticmethod
    def unregister_creator(
        file_name_suffix: str
    ):
        """Unregister creator function to create a OutputFile object."""
        if file_name_suffix in OutputFileFactory._creators:
            del OutputFileFactory._creators[file_name_suffix]

    @staticmethod
    def generate(file: Path) -> OutputFile:
        """
        Call the Constructor function to generate OutputFile object.

        Arguments
        ---------
        file: Path
            File to use in OutputFile.

        Returns
        -------
        OutputFile : OutputFile
            OutputFile object based on the given file suffix, if no valid FileNameRetriever can be found default MapFile is returned.
        """
        file_name_suffix = str(file).lower()[-7:]
        constructor = OutputFileFactory._creators.get(file_name_suffix)
        if constructor:
            return constructor(file)
        else:
            return MapFile(file)


OutputFileFactory.register_creator("_fou.nc", FouFile)
OutputFileFactory.register_creator("_map.nc", MapFile)
