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
import PyQt5.QtCore
from PyQt5 import QtWidgets
import PyQt5.QtGui

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


def get_available_font(currrent_font : PyQt5.QtGui.QFont, preferred_font, fallback_font):
    # Check if the preferred font is available
    available_fonts = PyQt5.QtGui.QFontDatabase().families()

    if preferred_font in available_fonts:
        return PyQt5.QtGui.QFont(preferred_font, currrent_font.pointSize())
    else:
        # Check if the fallback font is available
        if fallback_font in available_fonts:
            return PyQt5.QtGui.QFont(fallback_font, currrent_font.pointSize())
        else:
            # If neither font is available, return the default font
            return currrent_font