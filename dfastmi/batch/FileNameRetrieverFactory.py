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

from typing import Callable

from packaging.version import Version

from dfastmi.batch.AFileNameRetriever import AFileNameRetriever
from dfastmi.batch.FileNameRetriever import FileNameRetriever
from dfastmi.batch.FileNameRetrieverLegacy import FileNameRetrieverLegacy
from dfastmi.batch.FileNameRetrieverUnsupported import FileNameRetrieverUnsupported


class FileNameRetrieverFactory:
    """
    Class is used to register and get creation of AFileNameRetriever Objects
    """

    _creators = {}
    """Contains the AFileNameRetriever Objects creators to be used"""

    @staticmethod
    def register_creator(
        file_name_retriever_version: Version,
        creator: Callable[[bool], AFileNameRetriever],
    ):
        """Register creator function to create a AFileNameRetriever object."""
        if file_name_retriever_version not in FileNameRetrieverFactory._creators:
            FileNameRetrieverFactory._creators[file_name_retriever_version] = creator

    @staticmethod
    def generate(
        file_name_retriever_version: Version, needs_tide: bool
    ) -> AFileNameRetriever:
        """
        Call the Constructor function to generate AFileNameRetriever object.

        Arguments
        ---------
        file_name_retriever_version: version
            Version to retrieve the FileNameRetriever for.
        needs_tide : bool
            Specifies whether the tidal boundary is needed.

        Returns
        -------
        FileNameRetriever : AFileNameRetriever
            AFileNameRetriever object based on the given version, if no valid FileNameRetriever can be found FileNameRetrieverUnsupported is returned.
        """
        constructor = FileNameRetrieverFactory._creators.get(
            file_name_retriever_version
        )
        if constructor:
            return constructor(needs_tide)
        else:
            return FileNameRetrieverUnsupported()


FileNameRetrieverFactory.register_creator(
    Version("1.0"), lambda needs_tide: FileNameRetrieverLegacy()
)

FileNameRetrieverFactory.register_creator(Version("2.0"), FileNameRetriever)
FileNameRetrieverFactory.register_creator(Version("3.0"), FileNameRetriever)
