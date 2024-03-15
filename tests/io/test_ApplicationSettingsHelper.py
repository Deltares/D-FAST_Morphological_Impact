import sys
from contextlib import contextmanager
from io import StringIO

import mock
import pytest

from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_load_program_texts:
    """
    Unit testing load_program_texts with mocking.
    """

    def test_load_program_texts_in_global_PROGTEXT(self):
        """
        Read simple key with value
        """
        with mock.patch(
            "builtins.open", mock.mock_open(read_data="[header]\r\ncontent\r\n")
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")
            assert ApplicationSettingsHelper.PROGTEXTS["header"] == ["content"]

    def test_load_program_texts_multiline_in_global_PROGTEXT(self):
        """
        Read simple key with multiline value
        """
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[header]\r\ncontent\r\ncontent2\r\n"),
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")
            assert ApplicationSettingsHelper.PROGTEXTS["header"] == [
                "content",
                "content2",
            ]

    def test_load_program_texts_line_header_with_no_value_in_global_PROGTEXT(self):
        """
        Read simple key without value and another with value
        """
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[header]\r\n[otherheader]\r\ncontent\r\n"),
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")
            assert ApplicationSettingsHelper.PROGTEXTS["header"] == []
            assert ApplicationSettingsHelper.PROGTEXTS["otherheader"] == ["content"]

    def test_load_program_texts_double_header_throws_exception(self):
        """
        Read simple duplicate keys with value raises exception
        """
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[header]\r\n[header]\r\ncontent\r\n"),
        ) as mock_file:
            with pytest.raises(Exception) as cm:
                ApplicationSettingsHelper.load_program_texts("")
            assert str(cm.value) == 'Duplicate entry for "header" in "".'


class Test_log_text:
    @pytest.fixture
    def setup_data(self):
        ApplicationSettingsHelper.PROGTEXTS = {}

    def test_log_text_no_key_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key)
        outstr = out.getvalue().splitlines()
        strref = "No message found for " + key
        assert outstr[0] == strref

    def test_log_text_with_key_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[confirm]\r\nConfirm key found\r\n"),
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key)
        outstr = out.getvalue().splitlines()
        strref = "Confirm key found"
        assert outstr[0] == strref

    def test_log_text_with_key_and_variable_id_in_global_PROGTEXT(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        dict = {"value": "ABC"}
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[confirm]\r\nConfirm key found with {value}\r\n"),
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key, dict=dict)
        outstr = out.getvalue().splitlines()
        strref = "Confirm key found with ABC"
        assert outstr[0] == strref

    def test_log_text_two_times_with_key_and_variable_id_in_global_PROGTEXT(
        self, setup_data
    ):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        dict = {"value": "ABC"}
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[confirm]\r\nConfirm key found with {value}\r\n"),
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key, dict=dict, repeat=2)
        outstr = out.getvalue().splitlines()
        strref = "Confirm key found with ABC"
        assert outstr[0] == strref
        assert outstr[1] == strref

    def test_log_text_with_key_and_variable_id_in_global_PROGTEXT_write_in_file(
        self, setup_data
    ):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        dict = {"value": "ABC"}
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data="[confirm]\r\nConfirm key found with {value}\r\n"),
        ) as mock_file:
            ApplicationSettingsHelper.load_program_texts("")

        with mock.patch("builtins.open") as mock_file:
            ApplicationSettingsHelper.log_text(key, dict=dict, file=mock_file)
            assert mock_file.write.called
            mock_file.write.assert_called_once_with("Confirm key found with ABC\n")


class Test_get_filename:
    def test_get_filename_get_filename_from_uk_keys(self):
        """
        Testing get_filename wrapper for get_text.
        """
        ApplicationSettingsHelper.PROGTEXTS = {"filename_report.out": ["report.txt"]}
        file = ApplicationSettingsHelper.get_filename("report.out")
        assert file == "report.txt"


class Test_get_text:
    def test_get_text_from_empty_global_PROGTEXTS_results_in_no_message_found(self):
        """
        Testing get_text: key not found.
        """
        ApplicationSettingsHelper.PROGTEXTS = {}
        assert ApplicationSettingsHelper.get_text("@") == ["No message found for @"]

    def test_get_text_from_empty_key_in_global_PROGTEXTS_results_in_specified_value(
        self,
    ):
        """
        Testing get_text: empty line key.
        """
        ApplicationSettingsHelper.PROGTEXTS = {"": ""}
        assert ApplicationSettingsHelper.get_text("") == ""

    def test_get_text_from_custom_key_in_global_PROGTEXTS_results_in_specified_value(
        self,
    ):
        """
        Testing get_text: "confirm" key.
        """
        ApplicationSettingsHelper.PROGTEXTS = {"confirm": 'Confirm using "y" ...'}
        confirmText = ApplicationSettingsHelper.get_text("confirm")
        assert confirmText == 'Confirm using "y" ...'
