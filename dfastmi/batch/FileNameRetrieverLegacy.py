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

from typing import Any, Dict, Optional, Tuple
import configparser
from dfastmi.batch.AFileNameRetriever import AFileNameRetriever

class FileNameRetrieverLegacy(AFileNameRetriever):
    """
    File name retriever for version 1 (Legacy).
    """

    def get_file_names(self, config : Optional[configparser.ConfigParser] = None) -> Dict[Any, Tuple[str,str]]:
        """
        Extract the list of six file names from the configuration.
        This routine is valid for version 1 configuration files.

        Arguments
        ---------
        config : Optional[configparser.ConfigParser]
            The variable containing the configuration (may be None for imode = 0).

        Returns
        -------
        filenames : Dict[Any, Tuple[str,str]]
            Dictionary of string tuples representing the D-Flow FM file names for
            each reference/with measure pair. The keys of the dictionary vary. They
            can be the discharge index, discharge value or a tuple of forcing
            conditions, such as a Discharge and Tide forcing tuple.
        """
        filenames: Dict[Any, Tuple[str,str]]
        filenames = {}
        for i in range(3):
            qstr = f"Q{i+1}"
            if qstr in config:
                reference = self._cfg_get(config, qstr, "Reference")
                measure = self._cfg_get(config, qstr, "WithMeasure")
                filenames[i] = (reference, measure)

        return filenames