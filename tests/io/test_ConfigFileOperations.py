import configparser

import sys
from contextlib import contextmanager
from io import StringIO

import mock

from dfastmi.io.ConfigFileOperations import ConfigFileOperations

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_write_config():
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

        with mock.patch("builtins.open") as mock_file:
            ConfigFileOperations.write_config(filename, config)
            mock_file.assert_called_once_with(filename, 'w')
            mock_file.return_value.__enter__().write.assert_called()
            mock_file.return_value.__enter__().write.assert_any_call('[G 1]\n')
            mock_file.return_value.__enter__().write.assert_any_call('  k 1     = V 1\n')
            mock_file.return_value.__enter__().write.assert_any_call('\n')
            mock_file.return_value.__enter__().write.assert_any_call('[Group 2]\n')
            mock_file.return_value.__enter__().write.assert_any_call('  k1      = 1.0 0.1 0.0 0.01\n')
            mock_file.return_value.__enter__().write.assert_any_call('  k2      = 2.0 0.2 0.02 0.0\n')
            mock_file.return_value.__enter__().write.assert_any_call('[Group 3]\n')
            mock_file.return_value.__enter__().write.assert_any_call('  longkey = 3\n')