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
from pathlib import Path
from typing import Any, Dict, Optional
import PyQt5.QtCore
from PyQt5 import QtWidgets
from PyQt5.QtGui import QFontDatabase, QFont

from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

class FileExistValidator(PyQt5.QtGui.QValidator):
    def validate(self, input_text, pos):
        if Path(input_text).is_file():
            return (PyQt5.QtGui.QValidator.Acceptable, input_text, pos)
        else:
            return (PyQt5.QtGui.QValidator.Invalid, input_text, pos)


class FolderExistsValidator(PyQt5.QtGui.QValidator):
    def validate(self, input_str, pos):
        if Path(input_str).is_dir():
            return (PyQt5.QtGui.QValidator.Acceptable, input_str, pos)
        else:
            return (PyQt5.QtGui.QValidator.Invalid, input_str, pos)


class ValidatingLineEdit(QtWidgets.QLineEdit):
    def __init__(self, validator:PyQt5.QtGui.QValidator=FileExistValidator(), parent=None):
        super().__init__(parent)
        self.validator = validator
        #self.setValidator(self.validator)
        self.invalid = True

    def setInvalid(self, invalid):
         self.invalid = invalid
         self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isEnabled():
            if self.invalid:
                painter = PyQt5.QtGui.QPainter(self)
                painter.setPen(PyQt5.QtCore.Qt.red)
                painter.setBrush(PyQt5.QtCore.Qt.NoBrush)
                painter.drawRect(PyQt5.QtCore.QRect(0, 0, self.width() - 1, self.height() - 1))
                painter.end()  # Ensure to end the painter
            else:
                painter = PyQt5.QtGui.QPainter(self)
                painter.setPen(PyQt5.QtCore.Qt.green)
                painter.setBrush(PyQt5.QtCore.Qt.NoBrush)
                painter.drawRect(PyQt5.QtCore.QRect(0, 0, self.width() - 1, self.height() - 1))
                painter.end()  # Ensure to end the painter

    def validate(self, input_str, pos):
        state, _, _ = self.validator.validate(input_str, pos)
        if state == PyQt5.QtGui.QValidator.Acceptable:
            return state, input_str, pos
        else:
            return state, input_str[:pos], pos


def get_available_font(currrent_font : QFont, preferred_font, fallback_font, font_database):
    # Check if the preferred font is available
    available_fonts = font_database.families()

    if preferred_font in available_fonts:
        return QFont(preferred_font, currrent_font.pointSize())
    else:
        # Check if the fallback font is available
        if fallback_font in available_fonts:
            return QFont(fallback_font, currrent_font.pointSize())
        else:
            # If neither font is available, return the default font
            return currrent_font

def gui_text(key: str, prefix: str = "gui_", placeholder_dictionary: Optional[Dict[str, Any]] = None):
        """
        Query the global dictionary of texts for a single string in the GUI.

        This routine concatenates the prefix and the key to query the global
        dictionary of texts. It selects the first line of the text obtained and
        expands and placeholders in the string using the optional dictionary
        provided.

        Arguments
        ---------
        key : str
            The key string used to query the dictionary (extended with prefix).
        prefix : str
            The prefix used in combination with the key (default "gui_").
        dict : Dict[str, Any]
            A dictionary used for placeholder expansions (default empty).

        Returns
        -------
            The first line of the text in the dictionary expanded with the keys.
        """
        if placeholder_dictionary is None:
            placeholder_dictionary = {}  # If dict is None, initialize it as an empty dictionary

        cstr = ApplicationSettingsHelper.get_text(prefix + key)
        try:
            application_setting = cstr[0].format(**placeholder_dictionary)
        except KeyError:
            application_setting = cstr[0]
        return application_setting