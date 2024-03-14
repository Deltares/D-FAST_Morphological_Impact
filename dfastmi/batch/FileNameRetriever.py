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

import configparser
from typing import Any, Dict, Optional, Tuple

from dfastmi.batch.AFileNameRetriever import AFileNameRetriever


class FileNameRetriever(AFileNameRetriever):
    """
    File name retriever for version 2.
    """

    def __init__(self, needs_tide: bool):
        """
        Constructor of the FileNameRetriever.

        Arguments
        ---------
        needs_tide : bool
            Specifies whether the tidal boundary is needed.
        """
        self.needs_tide = needs_tide

    def get_file_names(
        self, config: Optional[configparser.ConfigParser] = None
    ) -> Dict[Any, Tuple[str, str]]:
        """
        Extract the list of 2N file names from the configuration.
        This routine is valid for version 2 configuration files.

        Arguments
        ---------
        config : Optional[configparser.ConfigParser]
            The variable containing the configuration (may be None for if 0).

        Returns
        -------
        filenames : Dict[Any, Tuple[str,str]]
            Dictionary of string tuples representing the D-Flow FM file names for
            each reference/with measure pair. The keys of the dictionary vary. They
            can be the discharge index, discharge value or a tuple of forcing
            conditions, such as a Discharge and Tide forcing tuple.
        """
        filenames: Dict[Any, Tuple[str, str]]
        key: Union[Tuple[float, int], float]
        filenames = {}
        i = 0
        while True:
            i = i + 1
            CSTR = f"C{i}"
            if CSTR in config:
                q_string = self._cfg_get(config, CSTR, "Discharge")

                try:
                    Q = float(q_string)
                except ValueError as exc:
                    raise TypeError(
                        f"{q_string} from Discharge could now be handled as a float."
                    ) from exc

                reference = self._cfg_get(config, CSTR, "Reference")
                measure = self._cfg_get(config, CSTR, "WithMeasure")
                if self.needs_tide:
                    T = self._cfg_get(config, CSTR, "TideBC")
                    key = (Q, T)
                else:
                    key = Q
                filenames[key] = (reference, measure)
            else:
                break

        return filenames
