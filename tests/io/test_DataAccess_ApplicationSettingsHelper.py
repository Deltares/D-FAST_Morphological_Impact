import os


import sys
from contextlib import contextmanager
from io import StringIO

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

class Test_data_access_load_program_texts():
    def test_load_program_texts_load_default_uk_messages_file(self):
        """
        Testing load_program_texts.
        """
        print("current work directory: ", os.getcwd())
        assert ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini") == None

class Test_data_access_log_text():
    @pytest.fixture
    def setup_data(self):
        """
        Foreach test load the uk messages
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")

    def test_log_text_check_content_messages_uk(self, setup_data):
        """
        Testing standard output of a single text without expansion.
        """
        key = "confirm"
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key)
        outstr = out.getvalue().splitlines()
        strref = ['Confirm using "y" ...', '']
        assert outstr == strref

    def test_log_text_empty_keys(self, setup_data):
        """
        Testing standard output of a repeated text without expansion.
        """
        key = ""
        nr = 3
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key, repeat=nr)
        outstr = out.getvalue().splitlines()
        strref = ['', '', '']
        assert outstr == strref

    def test_log_text_replace_variable_id_with_provided_value_in_dictionary(self, setup_data):
        """
        Testing standard output of a text with expansion.
        """
        key = "reach"
        dict = {"reach": "ABC"}
        with captured_output() as (out, err):
            ApplicationSettingsHelper.log_text(key, dict=dict)
        outstr = out.getvalue().splitlines()
        strref = ['The measure is located on reach ABC']
        assert outstr == strref

    def test_log_text_replace_variable_id_with_provided_value_in_dictionary_and_write_in_file(self, setup_data):
        """
        Testing file output of a text with expansion.
        """
        key = "reach"
        dict = {"reach": "ABC"}
        filename = "test.log"
        with open(filename, "w") as f:
            ApplicationSettingsHelper.log_text(key, dict=dict, file=f)
        all_lines = open(filename, "r").read().splitlines()
        strref = ['The measure is located on reach ABC']
        assert all_lines == strref

class Test_data_access_get_text():
    @pytest.fixture
    def setup_data(self):
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")

    def test_get_text_messages_uk_loaded_key_not_found(self):
        """
        Testing get_text: key not found.
        """
        assert ApplicationSettingsHelper.get_text("@") == ["No message found for @"]

    def test_get_text_messages_uk_loaded_key_empty(self, setup_data: None):
        """
        Testing get_text: empty line key.
        """
        assert ApplicationSettingsHelper.get_text("") == [""]

    def test_get_text_messages_uk_loaded_key_confirm_returns_value(self, setup_data: None):
        """
        Testing get_text: "confirm" key.
        """
        confirmText = ApplicationSettingsHelper.get_text("confirm")
        assert confirmText == ['Confirm using "y" ...','']