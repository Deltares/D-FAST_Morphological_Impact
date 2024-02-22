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

from typing import Optional, Union, Dict, Any, Tuple
import configparser
from abc import ABC, abstractmethod
from packaging import version

class IFileNameRetriever(ABC):
    """
    Abstract file name retriever.
    """
    
    @abstractmethod
    def get_file_names(self, config : Optional[configparser.ConfigParser] = None) -> Dict[Any, Tuple[str,str]]:
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
        Raise clear exception message when it fails.

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
        Exception
            If the key in the chapter doesn't exist.

        Returns
        -------
        value : str
            The value specified for the key in the chapter.
        """
        try:
            return config[chap][key]
        except:
            raise Exception('Keyword "{}" is not specified in group "{}" of analysis configuration file.'.format(key,chap,))

def get_filename_retriever(imode : int, config : configparser.ConfigParser, need_tides : bool) -> IFileNameRetriever:
    """
    Retrieves the expected file name retriever based on the given values.
    
        Arguments
    ---------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).

    config : Optional[configparser.ConfigParser]
        The variable containing the configuration (may be None for imode = 0).
        
    needs_tide : bool
        Specifies whether the tidal boundary is needed.

    Returns
    -------
    filenames : IFileNameRetriever
        returns the IFileNameRetriever which should be used.
    """
    if imode == 0 or config is None:
        return FileNameRetrieverUnsupported()
    
    if version.parse(config["General"]["Version"]) == version.parse("1"):
        return FileNameRetrieverV1()
    
    return FileNameRetrieverV2(need_tides)

class FileNameRetrieverUnsupported(IFileNameRetriever):
    """
    File name retriever for unsupported file name retrieving, e.g. for imode = 0.
    """
    
    def get_file_names(self, config : Optional[configparser.ConfigParser] = None) -> Dict[Any, Tuple[str,str]]:
        """
        Get file names for unsupported file name retriever.

        Arguments
        ---------
        config : Optional[configparser.ConfigParser]
            The variable containing the configuration (may be None for imode = 0).

        Returns
        -------
        filenames : Dict[Any, Tuple[str,str]]
            Returns and empty Dict.
        """
        return {}
        
class FileNameRetrieverV1(IFileNameRetriever):
    """
    File name retriever for version 1.
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
            qstr = "Q{}".format(i + 1)
            if qstr in config:
                reference = self._cfg_get(config, qstr, "Reference")
                measure = self._cfg_get(config, qstr, "WithMeasure")
                filenames[i] = (reference, measure)

        return filenames
    
class FileNameRetrieverV2(IFileNameRetriever):
    """
    File name retriever for version 2.
    """
    
    def __init__(self, needs_tide: bool):
        """
        Constructor of the FileNameRetrieverV2.

        Arguments
        ---------
        needs_tide : bool
            Specifies whether the tidal boundary is needed.
        """
        self.needs_tide = needs_tide
    
    def get_file_names(self, config : Optional[configparser.ConfigParser] = None) -> Dict[Any, Tuple[str,str]]:
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
        filenames: Dict[Any, Tuple[str,str]]
        key: Union[Tuple[float, int], float]
        filenames = {}
        i = 0
        while True:
            i = i + 1
            CSTR = "C{}".format(i)
            if CSTR in config:
                Q = float(self._cfg_get(config, CSTR, "Discharge"))
                reference = self._cfg_get(config, CSTR, "Reference")
                measure = self._cfg_get(config, CSTR, "WithMeasure")
                if self.needs_tide:
                    T = self._cfg_get(config, CSTR, "TideBC")
                    key = (Q,T)
                else:
                    key = Q
                filenames[key] = (reference, measure)
            else:
                break

        return filenames