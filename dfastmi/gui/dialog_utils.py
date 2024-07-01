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
"""
This module provides validators and utilities for PySide6 GUI applications.
It also includes functions for handling fonts and querying text strings for GUI elements.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import PySide6.QtCore
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QPainter,
    QPaintEvent,
    QValidator,
)
from PySide6.QtWidgets import QLineEdit

from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper


class FileExistValidator(QValidator):
    """A validator class to check if a file exists at the provided path."""

    def validate(self, input_text: str, pos: int):
        """
        Validate the input text as a file path.

        Parameters
        ----------
        input_text : str
            The input text to be validated.
        pos : int
            The position of the text cursor.

        Returns
        -------
        Tuple[int, str, int]
            A tuple containing the validation state, the input text, and the cursor position.
        """
        if Path(input_text).is_file():
            return (QValidator.Acceptable, input_text, pos)
        return (QValidator.Invalid, input_text, pos)


class FolderExistsValidator(QValidator):
    """A validator class to check if a folder exists at the provided path."""

    def validate(self, input_str: str, pos: int):
        """
        Validate the input string as a folder path.

        Parameters
        ----------
        input_str : str
            The input string to be validated.
        pos : int
            The position of the text cursor.

        Returns
        -------
        Tuple[int, str, int]
            A tuple containing the validation state, the input string, and the cursor position.
        """
        if len(input_str) > 0 and Path(input_str).is_dir():
            return (QValidator.Acceptable, input_str, pos)
        return (QValidator.Invalid, input_str, pos)


class ValidatingLineEdit(QLineEdit):
    """A custom QLineEdit widget with validation support."""

    def __init__(self, validator: QValidator = FileExistValidator(), parent=None):
        """
        Initialize the ValidatingLineEdit with the given validator.

        Parameters
        ----------
        validator : QValidator, optional
            The validator object to be used for input validation (default is FileExistValidator()).
        parent : QWidget, optional
            The parent widget (default is None).
        """
        super().__init__(parent)
        self.validator = validator
        self.invalid = True

    def setInvalid(self, invalid: bool):
        """
        Set the validation state of the widget.

        Parameters
        ----------
        invalid : bool
            The validation state to be set.
        """
        self.invalid = invalid
        self.update()

    def paintEvent(self, event: QPaintEvent):
        """
        Handle the paint event to visually indicate the validation state.

        Parameters
        ----------
        event : QPaintEvent
            The paint event object.
        """
        super().paintEvent(event)
        if self.isEnabled() and self.invalid:
            self.paint_box(PySide6.QtCore.Qt.red)

    def paint_box(self, colour: QColor):
        """
        Draw a colored border around the widget.

        Parameters
        ----------
        colour : QColor
            The color of the border to be drawn.
        """
        painter = QPainter(self)
        painter.setPen(colour)
        painter.setBrush(PySide6.QtCore.Qt.NoBrush)
        painter.drawRect(
            PySide6.QtCore.QRect(0, 0, self.width() - 1, self.height() - 1)
        )
        painter.end()  # Ensure to end the painter

    def validate(self, input_str: str, pos: int):
        """
        Validate the input string based on the provided validator.

        Parameters
        ----------
        input_str : str
            The input string to be validated.
        pos : int
            The position of the text cursor.

        Returns
        -------
        Tuple[int, str, int]
            A tuple containing the validation state, the validated input string, and the cursor position.
        """
        state, _, _ = self.validator.validate(input_str, pos)
        if state == QValidator.Acceptable:
            return state, input_str, pos
        else:
            return state, input_str[:pos], pos


def get_available_font(
    currrent_font: QFont,
    preferred_font: str,
    fallback_font: str,
    font_database: QFontDatabase,
):
    """
    Get an available font based on preference and availability.

    Parameters
    ----------
    currrent_font : QFont
        The current font to be used as a reference.
    preferred_font : str
        The preferred font name.
    fallback_font : str
        The fallback font name.
    font_database : QFontDatabase
        The font database object.

    Returns
    -------
    QFont
        A QFont object representing the selected font.
    """
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


def gui_text(
    key: str,
    prefix: str = "gui_",
    placeholder_dictionary: Optional[Dict[str, Any]] = None,
):
    """
    Query the global dictionary of texts for a single string in the GUI.

    This routine concatenates the prefix and the key to query the global
    dictionary of texts. It selects the first line of the text obtained and
    expands any placeholders in the string using the optional dictionary
    provided.

    Parameters
    ----------
    key : str
        The key string used to query the dictionary (extended with prefix).
    prefix : str, optional
        The prefix used in combination with the key (default "gui_").
    placeholder_dictionary : Dict[str, Any], optional
        A dictionary used for placeholder expansions (default None).

    Returns
    -------
    str
        The first line of the text in the dictionary expanded with the provided keys.
    """
    if placeholder_dictionary is None:
        placeholder_dictionary = (
            {}
        )  # If dict is None, initialize it as an empty dictionary

    cstr = ApplicationSettingsHelper.get_text(prefix + key)
    try:
        application_setting = cstr[0].format(**placeholder_dictionary)
    except KeyError:
        application_setting = cstr[0]
    return application_setting
