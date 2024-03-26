import PyQt5.QtCore
from PyQt5 import QtWidgets
import PyQt5.QtGui


import os


class FileExistValidator(PyQt5.QtGui.QValidator):
    def validate(self, input_text, pos):
        if os.path.isfile(input_text):
            return (PyQt5.QtGui.QValidator.Acceptable, input_text, pos)
        else:
            return (PyQt5.QtGui.QValidator.Invalid, input_text, pos)


class FolderExistsValidator(PyQt5.QtGui.QValidator):
    def validate(self, input_str, pos):
        if os.path.isdir(input_str):
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