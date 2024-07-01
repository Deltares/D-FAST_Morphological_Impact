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
from typing import Any, Dict, List, Optional, TextIO


class ApplicationSettingsHelper:
    """
    Load texts from configuration file, and store globally for access.
    """

    PROGTEXTS: Dict[str, List[str]]

    @staticmethod
    def load_program_texts(filename: str) -> None:
        """
        Load texts from configuration file, and store globally for access.

        This routine reads the text file "filename", and detects the keywords
        indicated by lines starting with [ and ending with ]. The content is
        placed in a global dictionary PROGTEXTS which may be queried using the
        routine "get_text". These routines are used to implement multi-
        language support.

        Parameters
        ----------
        filename : str
            The name of the file to be read and parsed.
        """
        text: List[str]
        dict: Dict[str, List[str]]

        all_lines = open(filename, "r", encoding="UTF-8").read().splitlines()
        dict = {}
        text = []
        key = None
        for line in all_lines:
            rline = line.strip()
            if rline.startswith("[") and rline.endswith("]"):
                if not key is None:
                    dict[key] = text
                key = rline[1:-1]
                text = []
            else:
                text.append(line)
        if key in dict.keys():
            raise Exception('Duplicate entry for "{}" in "{}".'.format(key, filename))
        if not key is None:
            dict[key] = text
        ApplicationSettingsHelper.PROGTEXTS = dict

    @staticmethod
    def get_text(key: str) -> List[str]:
        """
        Query the global dictionary of texts via a string key.

        Query the global dictionary PROGTEXTS by means of a string key and return
        the list of strings contained in the dictionary. If the dictionary doesn't
        include the key, a default string is returned.

        Parameters
        ----------
        key : str
            The key string used to query the dictionary.

        Returns
        -------
        text : List[str]
            The list of strings returned contain the text stored in the dictionary
            for the key. If the key isn't available in the dictionary, the routine
            returns the default string "No message found for <key>"
        """

        try:
            application_setting = ApplicationSettingsHelper.PROGTEXTS[key]
        except (KeyError,TypeError):
            application_setting = ["No message found for " + key]
        except:
            application_setting = ["Still no message found for " + key]
        return application_setting

    @staticmethod
    def log_text(
        key: str,
        file: Optional[TextIO] = None,
        dict: Dict[str, Any] = {},
        repeat: int = 1,
    ) -> None:
        """
        Write a text to standard out or file.

        Arguments
        ---------
        key : str
            The key for the text to show to the user.
        file : Optional[TextIO]
            The file to write to (None for writing to standard out).
        dict : Dict[str, Any]
            A dictionary used for placeholder expansions (default empty).
        repeat : int
            The number of times that the same text should be repeated (default 1).

        Returns
        -------
        None
        """
        the_text = ApplicationSettingsHelper.get_text(key)
        for r in range(repeat):
            for line in the_text:
                expanded_line = line.format(**dict)
                if file is None:
                    print(expanded_line)
                else:
                    file.write(expanded_line + "\n")

    @staticmethod
    def get_filename(key: str) -> str:
        """
        Query the global dictionary of texts for a file name.

        The file name entries in the global dictionary have a prefix "filename_"
        which will be added to the key by this routine.

        Arguments
        ---------
        key : str
            The key string used to query the dictionary.

        Results
        -------
        filename : str
            File name.
        """
        filename = ApplicationSettingsHelper.get_text("filename_" + key)[0]
        return filename
