from typing import List
import PyQt5
from mock import patch
import pytest
from pytestqt.qtbot import QtBot
from unittest.mock import MagicMock
from dfastmi.gui.dialog_utils import FileExistValidator, FolderExistsValidator, ValidatingLineEdit, get_available_font, gui_text
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

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

def test_file_exist_validator_validate(file_exist_validator : FileExistValidator):
    """
    given : FileExistValidator instance.
    when  : Invoking the validate method with a file that exists and a file that does not exist.
    then  : The method should return Acceptable for the existing file and Invalid for the non-existing file.
    """
    # Test when file exists
    input_text = "./tests/files/read_riversv2_test.ini"
    pos = 0
    result, _, _ = file_exist_validator.validate(input_text, pos)
    assert result == PyQt5.QtGui.QValidator.Acceptable

    # Test when file does not exist
    input_text = "/path/to/non_existing_file.txt"
    result, _, _ = file_exist_validator.validate(input_text, pos)
    assert result == PyQt5.QtGui.QValidator.Invalid

def test_folder_exists_validator_validate(folder_exists_validator : FolderExistsValidator):
    """
    given : FolderExistsValidator instance.
    when  : Invoking the validate method with a folder that exists and a folder that does not exist.
    then  : The method should return Acceptable for the existing folder and Invalid for the non-existing folder.
    """
    # Test when folder exists
    input_str = "./tests"
    pos = 0
    result, _, _ = folder_exists_validator.validate(input_str, pos)
    assert result == PyQt5.QtGui.QValidator.Acceptable

    # Test when folder does not exist
    input_str = "/path/to/non_existing_folder"
    result, _, _ = folder_exists_validator.validate(input_str, pos)
    assert result == PyQt5.QtGui.QValidator.Invalid

def test_validating_line_edit_paint_event_setInvalid_True(validating_line_edit : ValidatingLineEdit, qtbot : QtBot):
    """
    given : ValidatingLineEdit instance.
    when  : Setting the widget as invalid and triggering a repaint.
    then  : The widget should indicate that it is in an invalid state.
    """
    # Test painting when invalid
    validating_line_edit.setInvalid(True)
    qtbot.addWidget(validating_line_edit)
    validating_line_edit.show()
    validating_line_edit.repaint()  # Trigger repaint
    
    assert validating_line_edit.invalid

def test_validating_line_edit_paint_event_setInvalid_False(validating_line_edit : ValidatingLineEdit, qtbot : QtBot):
    """
    given : ValidatingLineEdit instance.
    when  : Setting the widget as valid and triggering a repaint.
    then  : The widget should indicate that it is in a valid state.
    """
    # Test painting when valid
    validating_line_edit.setInvalid(False)
    qtbot.addWidget(validating_line_edit)
    validating_line_edit.show()
    validating_line_edit.repaint()  # Trigger repaint
    assert not validating_line_edit.invalid
    
def test_validating_line_edit_validate(validating_line_edit : ValidatingLineEdit, file_exist_validator : FileExistValidator, qtbot : QtBot):
    """
    given : ValidatingLineEdit instance and FileExistValidator instance.
    when  : Invoking the validate method with a valid and an invalid input.
    then  : The method should return Acceptable for valid input and Invalid for invalid input.
    """
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
    """
    given : No specific conditions.
    when  : Invoking the get_available_font function with different font scenarios.
    then  : The function should return the expected font based on availability and preferences.
    """
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
    """
    given : Preferred font is not available but fallback font is available.
    when  : Invoking the get_available_font function.
    then  : The function should return the fallback font.
    """
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
    """
    given : Neither preferred nor fallback font is available.
    when  : Invoking the get_available_font function.
    then  : The function should fall back to the current font.
    """
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
    """
    given : No specific conditions.
    when  : Invoking the gui_text function with different scenarios.
    then  : The function should return the expected text based on the provided keys and placeholders.
    """
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

