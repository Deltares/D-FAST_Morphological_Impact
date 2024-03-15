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
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class AFileNameRetriever(ABC):
    """
    Abstract file name retriever.
    """

    @abstractmethod
    def get_file_names(
        self, config: Optional[configparser.ConfigParser] = None
    ) -> Dict[Any, Tuple[str, str]]:
        """
        Abstract method to get the filenames.

        Arguments
        ---------
        config : Optional[configparser.ConfigParser]
            The variable containing the configuration (may be None for imode = 0).

        Returns
        -------
        filenames : Dict[Any, Tuple[str,str]]
            Dictionary of string tuples representing the D-Flow FM file names for
            each reference/with measure pair.
        """

    def _cfg_get(self, config: configparser.ConfigParser, chap: str, key: str) -> str:
        """
        Get a single entry from the analysis configuration structure.
        Raise KeyError message when it fails.

        Arguments
        ---------
        config : Optional[configparser.ConfigParser]
            The variable containing the configuration (may be None for imode = 0).
        chap : str
            The name of the chapter in which to search for the key.
        key : str
            The name of the key for which to return the value.

        Raises
        ------
        KeyError
            If the key in the chapter doesn't exist.

        Returns
        -------
        value : str
            The value specified for the key in the chapter.
        """
        value = config.get(chap, key, fallback=None)
        if value is None:
            raise KeyError(
                f'Keyword "{key}" is not specified in group "{chap}" of analysis configuration file.'
            )
        return value
