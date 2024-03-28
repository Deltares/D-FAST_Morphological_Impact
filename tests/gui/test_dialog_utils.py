import sys
from typing import List
import PyQt5
from mock import patch
import pytest
from PyQt5.QtWidgets import QApplication
from unittest.mock import MagicMock
from dfastmi.gui.dialog_utils import FileExistValidator, FolderExistsValidator, ValidatingLineEdit, get_available_font, gui_text
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
#from your_module_name import FileExistValidator, FolderExistsValidator, ValidatingLineEdit, get_available_font, gui_text

@pytest.fixture
def mock_application_settings_helper():
    return MagicMock(spec=ApplicationSettingsHelper)

@pytest.fixture
def file_exist_validator():
    return FileExistValidator()

@pytest.fixture
def folder_exists_validator():
    return FolderExistsValidator()

@pytest.fixture
def validating_line_edit():
    return ValidatingLineEdit()

def test_file_exist_validator_validate(file_exist_validator):
    # Test when file exists
    input_text = "./tests/files/read_riversv2_test.ini"
    pos = 0
    result, _, _ = file_exist_validator.validate(input_text, pos)
    assert result == PyQt5.QtGui.QValidator.Acceptable

    # Test when file does not exist
    input_text = "/path/to/non_existing_file.txt"
    result, _, _ = file_exist_validator.validate(input_text, pos)
    assert result == PyQt5.QtGui.QValidator.Invalid

def test_folder_exists_validator_validate(folder_exists_validator):
    # Test when folder exists
    input_str = "./tests"
    pos = 0
    result, _, _ = folder_exists_validator.validate(input_str, pos)
    assert result == PyQt5.QtGui.QValidator.Acceptable

    # Test when folder does not exist
    input_str = "/path/to/non_existing_folder"
    result, _, _ = folder_exists_validator.validate(input_str, pos)
    assert result == PyQt5.QtGui.QValidator.Invalid

def test_validating_line_edit_paint_event_setInvalid_True(validating_line_edit, qtbot):
    # Test painting when invalid
    validating_line_edit.setInvalid(True)
    qtbot.addWidget(validating_line_edit)
    validating_line_edit.show()
    validating_line_edit.repaint()  # Trigger repaint
    
    assert validating_line_edit.invalid

def test_validating_line_edit_paint_event_setInvalid_False(validating_line_edit, qtbot):
    # Test painting when valid
    validating_line_edit.setInvalid(False)
    qtbot.addWidget(validating_line_edit)
    validating_line_edit.show()
    validating_line_edit.repaint()  # Trigger repaint
    assert not validating_line_edit.invalid
    
def test_validating_line_edit_validate(validating_line_edit, file_exist_validator, qtbot):
    # Test when input is valid
    input_str = "./tests/files/read_riversv2_test.ini"
    pos = 0
    result, _, _ = validating_line_edit.validate(input_str, pos)
    assert result == PyQt5.QtGui.QValidator.Acceptable

    # Test when input is invalid
    input_str = "/path/to/non_existing_file.txt"
    result, _, _ = validating_line_edit.validate(input_str, pos)
    assert result == PyQt5.QtGui.QValidator.Invalid

def test_get_available_font():
    # Mock current font
    current_font = MagicMock()
    current_font.pointSize.return_value = 12  # Assuming point size of 12

    # Test when preferred font is available
    preferred_font = "Helvetica"
    fallback_font = "Tahoma"
    result_font = get_available_font(current_font, preferred_font, fallback_font, QFontDatabaseWrapper())
    assert result_font.family() == preferred_font
    assert result_font.pointSize() == 12  # Point size should remain unchanged        

def test_get_available_font_preferred_font_is_not_available_but_fallback_font_is():
    # Mock current font
    current_font = MagicMock()
    current_font.pointSize.return_value = 12  # Assuming point size of 12

    # Test when preferred font is not available but fallback font is
    preferred_font = "Arial"
    fallback_font = "Tahoma"
    result_font = get_available_font(current_font, preferred_font, fallback_font,QFontDatabaseWrapper())
    assert result_font.family() == fallback_font
    assert result_font.pointSize() == 12  # Point size should remain unchanged

def test_get_available_font_neither_preferred_nor_fallback_font_is_available():
    # Mock current font
    current_font = MagicMock()
    current_font.pointSize.return_value = 12  # Assuming point size of 12

    # Test when neither preferred nor fallback font is available
    preferred_font = "Georgia"
    fallback_font = "Times New Roman"
    result_font = get_available_font(current_font, preferred_font, fallback_font, QFontDatabaseWrapper())
    assert result_font.family() == current_font.family()  # Should fall back to the current font
    assert result_font.pointSize() == 12  # Point size should remain unchanged

class QFontDatabaseWrapper:
    def families(self) -> List[str]:
        return ["Helvetica", "Tahoma", "Verdana"]
    
def test_gui_text():
    # Mock the return value of ApplicationSettingsHelper.get_text
     with patch("dfastmi.io.ApplicationSettingsHelper.ApplicationSettingsHelper.get_text") as mock_application_settings_helper_get_text:
        mock_application_settings_helper_get_text.return_value = ["Hello, {name}!"]

        # Test with placeholder dictionary
        placeholder_dictionary = {"name": "World"}
        result = gui_text("greeting", "hello_", placeholder_dictionary)
        assert result == "Hello, World!"

        # Test without placeholder dictionary
        result = gui_text("greeting", "hello_")
        assert result == "Hello, {name}!"

