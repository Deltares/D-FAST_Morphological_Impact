import configparser
import os
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import mock
import pytest

from dfastmi.config.ConfigFileOperations import ConfigFileOperations


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_write_config:
    def test_write_config_check_written(self):
        """
        Testing write_config.
        """
        filename = "test.cfg"
        config = configparser.ConfigParser()
        config.add_section("G 1")
        config["G 1"]["K 1"] = "V 1"
        config.add_section("Group 2")
        config["Group 2"]["K1"] = "1.0 0.1 0.0 0.01"
        config["Group 2"]["K2"] = "2.0 0.2 0.02 0.0"
        config.add_section("Group 3")
        config["Group 3"]["LongKey"] = "3"

        with mock.patch.object(Path, "open") as mock_file:
            ConfigFileOperations.write_config(filename, config)
            mock_file.assert_called_once_with("w", encoding="utf-8")
            mock_file.return_value.__enter__().write.assert_called()
            mock_file.return_value.__enter__().write.assert_any_call("[G 1]\n")
            mock_file.return_value.__enter__().write.assert_any_call(
                "  k 1     = V 1\n"
            )
            mock_file.return_value.__enter__().write.assert_any_call("\n")
            mock_file.return_value.__enter__().write.assert_any_call("[Group 2]\n")
            mock_file.return_value.__enter__().write.assert_any_call(
                "  k1      = 1.0 0.1 0.0 0.01\n"
            )
            mock_file.return_value.__enter__().write.assert_any_call(
                "  k2      = 2.0 0.2 0.02 0.0\n"
            )
            mock_file.return_value.__enter__().write.assert_any_call("[Group 3]\n")
            mock_file.return_value.__enter__().write.assert_any_call("  longkey = 3\n")

    @pytest.mark.parametrize(
        "absolute_path, expected_relative_path",
        [
            pytest.param(Path(r"D:\DHYDRO\file1.txt"), r"..\..\DHYDRO\file1.txt"),
            pytest.param(Path(r"D:\DFAST\file2.txt"), r"..\file2.txt"),
            pytest.param(Path(r"D:\DFAST\root\file3.txt"), r"file3.txt"),
            pytest.param(Path(r"D:\DFAST\root\output\file4.txt"), r"output\file4.txt"),
        ],
    )
    def test_absolute_path_in_config_is_updated_to_relative_path_correctly(
        self, absolute_path: Path, expected_relative_path: str
    ):
        rootdir = Path(r"D:\DFAST\root")

        config = configparser.ConfigParser()
        section = "randomSection"
        key = "randomKey"
        config[section] = {key: absolute_path}

        ConfigFileOperations._update_to_relative_path(rootdir, config, section, key)

        relative_path = config[section][key]

        assert relative_path == expected_relative_path

    def test_no_absolute_path_when_converting_to_relative_path_uses_root_dir_instead(
        self,
    ):
        rootdir = Path(r"D:\DFAST\root")

        config = configparser.ConfigParser()
        section = "randomSection"
        key = "randomKey"
        config[section] = {key: ""}

        ConfigFileOperations._update_to_relative_path(rootdir, config, section, key)

        relative_path = config[section][key]

        assert relative_path == ""
