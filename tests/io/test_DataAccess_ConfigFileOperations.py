import configparser
import sys
from contextlib import contextmanager
from io import StringIO

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


class Test_data_access_write_config():
    def test_write_config_and_read_back(self):
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
        ConfigFileOperations.write_config(filename, config)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['[G 1]',
                         '  k 1     = V 1',
                         '',
                         '[Group 2]',
                         '  k1      = 1.0 0.1 0.0 0.01',
                         '  k2      = 2.0 0.2 0.02 0.0',
                         '',
                         '[Group 3]',
                         '  longkey = 3']
        assert all_lines == all_lines_ref