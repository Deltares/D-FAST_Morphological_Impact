"""
Tests for DFastMIConfig class
"""

import configparser
import sys
from contextlib import contextmanager
from io import StringIO
from typing import Tuple

import pytest
from mock import Mock

from dfastmi.io.AReach import AReach
from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser
from dfastmi.io.IBranch import IBranch
from dfastmi.io.IReach import IReach


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_DFastMIConfigParser:
    """
    Class will validate the functionality the DFastMConfigParser
    """

    _reach: IReach
    _config: configparser.ConfigParser
    _my_group: str
    _my_key: str
    _my_val: str
    _river_data: DFastMIConfigParser

    @pytest.fixture
    def setup_data(self):
        """Setup a reach with a branch to be used in the tests"""
        reach = Mock(AReach)
        reach.name = "Reach1"
        self._reach = reach
        branch = Mock(IBranch)
        branch.name = "Branch1"
        self._reach.parent_branch = branch
        self._config = configparser.ConfigParser()
        self._my_group = "General"
        self._config.add_section(self._my_group)
        self._my_key = "KEY"
        self._my_val = "YES"
        self._config[self._my_group][self._my_key] = self._my_val
        self._river_data = DFastMIConfigParser(self._config)

    def given_simple_river_config_when_read_key_with_custom_unknown_type_then_exception_thrown(
        self, setup_data
    ):
        """
        When we want to read a configuration value from a river configuration file but have not registered a type
        or actually have an exception while parsing the value string to the type we want we throw an exception.
        """
        self._river_data._processor.register_processor(
            Test_DFastMIConfigParser,
            self._river_data._process_entry_value,
            lambda x: 1 / 0,
        )
        with pytest.raises(Exception) as cm:
            self._river_data.read_key(
                Test_DFastMIConfigParser, self._my_key, self._reach
            )
        assert (
            str(cm.value)
            == f'Reading {self._my_key} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "{self._my_val}". Expecting 1 values.'
        )

    def given_simple_river_config_when_read_key_with_custom_unknown_tuple_type_then_return_empty_tuple(
        self, setup_data
    ):
        """
        When we want to read a configuration tuple value from a river configuration file but have not registered a type
        or actually have an exception while parsing the value string to the tuple type we want we return an empty tuple.
        """
        self._river_data._processor.register_processor(
            Test_DFastMIConfigParser,
            self._river_data._process_tuple_entry_value,
            lambda x: 1 / 0,
        )
        assert (
            self._river_data.read_key(
                Test_DFastMIConfigParser, self._my_key, self._reach
            )
            == ()
        )


class Test_read_key:
    """
    Class will validate the functionality of reading key values from a river configuration file
    """

    _reach: IReach

    @pytest.fixture
    def setup_data(self):
        """setup the reach with a simple branch to be used in the test methods"""
        reach = Mock(AReach)
        reach.name = "Reach1"
        self._reach = reach
        branch = Mock(IBranch)
        branch.name = "Branch1"
        self._reach.parent_branch = branch
        self._config = configparser.ConfigParser()
        self._my_group = "General"
        self._config.add_section(self._my_group)

    def given_simple_valid_bool_key_value_when_read_key_with_type_bool_then_return_expected_value(
        self, setup_data
    ):
        """
        Setup a simple config with a valid bool key value
        which can be parsed correctly will return the expected boolean
        """
        myKey = "KEY"
        myVal = "YES"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert river_data.read_key(bool, myKey, self._reach, False)

    def given_simple_invalid_bool_key_value_because_value_not_set_when_read_key_with_type_bool_then_throw_exception(
        self, setup_data
    ):
        """
        Setup a simple config with a valid bool key but invalid value
        which can't be parsed correctly will throw an exception
        """
        myKey = "KEY"
        myVal = ""
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)

        with pytest.raises(Exception) as cm:
            river_data.read_key(bool, myKey, self._reach)
        assert (
            str(cm.value)
            == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "". Expecting 1 values.'
        )

    def given_simple_invalid_bool_key_value_because_value_not_available_when_read_key_with_type_bool_then_throw_exception(
        self, setup_data
    ):
        """
        Setup a simple config with a valid bool key but value not written
        which can't be parsed correctly will throw an exception
        """
        myKey = "KEY"
        river_data = DFastMIConfigParser(self._config)
        with pytest.raises(Exception) as cm:
            river_data.read_key(bool, myKey, self._reach)
        assert (
            str(cm.value)
            == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "". Expecting 1 values.'
        )

    def given_simple_valid_int_key_value_when_read_key_with_type_int_then_return_expected_value(
        self, setup_data
    ):
        """
        Setup a simple config with a valid int key value
        which can be parsed correctly will return the expected int
        """
        myKey = "KEY"
        myVal = "801"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert (
            river_data.read_key(
                int,
                myKey,
                self._reach,
            )
            == 801
        )

    def given_simple_invalid_int_key_value_with_a_default_value_but_no_int_value_set_when_read_key_with_type_int_then_return_expected_default_value(
        self, setup_data
    ):
        """
        Setup a simple invalid int key value with a default value
        but no int value set which can't be parsed correctly will return the expected default
        """
        myKey = "KEY"
        myVal = ""
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert river_data.read_key(int, myKey, self._reach, 802) == 802

    def given_simple_valid_float_key_value_when_read_key_with_type_float_then_return_expected_value(
        self, setup_data
    ):
        """
        Setup a simple config with a valid float key value
        which can be parsed correctly will return the expected float
        """
        myKey = "KEY"
        myVal = "8.01"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert river_data.read_key(float, myKey, self._reach) == 8.01

    def given_simple_valid_tulple_float_key_value_and_expected_number_of_float_of_2_values_when_read_key_with_type_tuple_float_then_return_expected_value(
        self, setup_data
    ):
        """
        Setup a simple config with a valid tuple float key values and expected number of values of 2
        which can be parsed correctly will return the expected tuple float key values
        """
        myKey = "KEY"
        myVal = "8.01 8.02"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        read_data = river_data.read_key(
            Tuple[float, ...], myKey, self._reach, expected_number_of_values=2
        )
        assert len(read_data) == 2
        assert read_data == (8.01, 8.02)

    def given_simple_valid_tulple_float_key_value_and_expected_number_of_float_of_4_values_when_read_key_with_type_tuple_float_then_return_expected_value(
        self, setup_data
    ):
        """
        Setup a simple config with a valid tuple float key values and expected number of values of 4
        which can be parsed correctly will return the expected tuple float key values
        """
        myKey = "KEY"
        myVal = "8.01 8.02 2.14 5.88"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert river_data.read_key(
            Tuple[float, ...], myKey, self._reach, expected_number_of_values=4
        ) == (8.01, 8.02, 2.14, 5.88)

    def given_simple_valid_tulple_float_key_values_when_read_key_with_type_tuple_float_then_return_expected_values(
        self, setup_data
    ):
        """
        Setup a simple config with a valid tuple float key values
        which can be parsed correctly will return the expected tuple float key values
        """
        myKey = "KEY"
        myVal = "8.01 8.02 2.14 5.88 76 27"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert river_data.read_key(Tuple[float, ...], myKey, self._reach) == (
            8.01,
            8.02,
            2.14,
            5.88,
            76,
            27,
        )

    def given_simple_valid_tulple_float_key_with_invalid_values_because_not_set_but_with_default_when_read_key_with_type_tuple_float_then_return_expected_default_values(
        self, setup_data
    ):
        """
        Setup a simple config with invalid tuple float key values because not set but with a default
        which can be parsed correctly will return the expected default tuple float key values
        """
        myKey = "KEY"
        myVal = ""
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        assert river_data.read_key(
            Tuple[float, ...], myKey, self._reach, (80.1, 80.2), 2
        ) == (80.1, 80.2)

    def given_simple_valid_tulple_float_key_with_invalid_number_of_expected_values_when_read_key_with_type_tuple_float_then_throw_exception(
        self, setup_data
    ):
        """
        Setup a simple config with valid tuple float key values but expecting a certain number of values
        which can be parsed correctly but will throw an exception because wrong number of expected values.
        """
        myKey = "KEY"
        myVal = "8.01 8.02 2.14 5.88 76 27"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        with pytest.raises(Exception) as cm:
            river_data.read_key(
                Tuple[float, ...], myKey, self._reach, expected_number_of_values=4
            )
        assert (
            str(cm.value)
            == f'Reading {myKey} for reach {self._reach.name} on {self._reach.parent_branch.name} returns "{myVal}". Expecting 4 values.'
        )

    def given_simple_valid_tulple_str_key_value_and_expected_number_of_str_of_3_values_when_read_key_with_type_tuple_str_then_return_expected_value(
        self, setup_data
    ):
        """
        Setup a simple config with a valid tuple str key values and expected number of values of 3
        which can be parsed correctly will return the expected tuple str key values
        """
        myKey = "KEY"
        myVal = "8.01 8.02 8.03"
        self._config[self._my_group][myKey] = myVal
        river_data = DFastMIConfigParser(self._config)
        read_data = river_data.read_key(
            Tuple[str, ...], myKey, self._reach, expected_number_of_values=3
        )
        assert len(read_data) == 3
        assert read_data == ("8.01", "8.02", "8.03")


class Test_config_get:
    """
    Class will validate the functionality of reading key values from a DFast application configuration file.
    This is a simplified but very similar functionality of the read_key functionality in the class.
    This functionality only reads from the configuration file, it is not using the data type object reach and branch
    """

    def given_simple_valid_bool_key_value_when_config_get_with_type_bool_then_return_expected_value(
        self,
    ):
        """
        Setup a simple config with a valid bool key value
        which can be parsed correctly will return the expected boolean
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)

        assert config_data.config_get(bool, myGroup, myKey)

    def given_simple_valid_bool_key_value_with_no_value_set_when_config_get_with_type_bool_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid bool key with no value set
        which can be parsed correctly but will throw no bool specified in configuration exception
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(bool, myGroup, myKey)
        assert str(
            cm.value
        ) == 'No bool value specified for required keyword "{}" in block "{}".'.format(
            myKey, myGroup
        )

    def given_simple_valid_bool_key_value_with_no_value_set_but_default_is_given_when_config_get_with_type_bool_then_return_expected_default(
        self,
    ):
        """
        Setup a simple config with a valid bool key with no value set
        which can be parsed correctly but no value will be available
        but because default is provided we expect the default value to be returned
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(bool, myGroup, myKey, default=True)

    def given_simple_valid_int_key_value_when_config_get_with_type_int_then_return_expected_value(
        self,
    ):
        """
        Setup a simple config with a valid int key value
        which can be parsed correctly will return the expected integer
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "1"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(int, myGroup, myKey) == 1

    def given_simple_valid_int_key_value_with_no_value_set_when_config_get_with_type_int_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid int key with no value set
        which can be parsed correctly but will throw no int specified in configuration exception
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(int, myGroup, myKey)
        assert (
            str(cm.value)
            == f'No {int.__name__} value specified for required keyword "{myKey}" in block "{myGroup}".'
        )

    def given_simple_valid_int_key_value_but_is_negative_while_only_positive_values_are_expected_when_config_get_with_type_int_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid int key value and this integer value is negative
        which can be parsed correctly but we expect only positive values an exception is thrown
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "-1"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(int, myGroup, myKey, positive=True)
        assert (
            str(cm.value)
            == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {myVal}.'
        )

    def given_simple_valid_int_key_value_but_is_0_while_only_positive_values_are_expected_when_config_get_with_type_int_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid int key value and this integer value is 0
        which can be parsed correctly but we expect only positive values an exception is thrown
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(int, myGroup, myKey, positive=True)
        assert (
            str(cm.value)
            == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {myVal}.'
        )

    def given_simple_valid_int_key_value_with_no_value_set_but_default_is_given_when_config_get_with_type_int_then_return_expected_default(
        self,
    ):
        """
        Setup a simple config with a valid int key with no value set
        which can be parsed correctly but no value will be available
        but because default is provided we expect the default value to be returned
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(int, myGroup, myKey, default=1) == 1

    def given_simple_valid_float_key_value_when_config_get_with_type_float_then_return_expected_value(
        self,
    ):
        """
        Setup a simple config with a valid bool key value
        which can be parsed correctly will return the expected boolean
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "8.01"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(float, myGroup, myKey) == 8.01

    def given_simple_valid_float_key_value_with_no_value_set_when_config_get_with_type_float_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid float key with no value set
        which can be parsed correctly but will throw no float specified in configuration exception
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(float, myGroup, myKey)
        assert (
            str(cm.value)
            == f'No {float.__name__} value specified for required keyword "{myKey}" in block "{myGroup}".'
        )

    def given_simple_valid_float_key_value_but_is_negative_while_only_positive_values_are_expected_when_config_get_with_type_float_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid float key value and this floating point value is negative
        which can be parsed correctly but we expect only positive values an exception is thrown
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "-0.5"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(float, myGroup, myKey, positive=True)
        assert (
            str(cm.value)
            == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {myVal}.'
        )

    def given_simple_valid_float_key_value_but_is_0_while_only_positive_values_are_expected_when_config_get_with_type_float_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid int key value and this integer value is 0
        which can be parsed correctly but we expect only positive values an exception is thrown
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)

        with pytest.raises(Exception) as cm:
            config_data.config_get(float, myGroup, myKey, positive=True)
        assert (
            str(cm.value)
            == f'Value for "{myKey}" in block "{myGroup}" must be positive, not {float(myVal)}.'
        )

    def given_simple_valid_float_key_value_with_no_value_set_but_default_is_given_when_config_get_with_type_float_then_return_expected_default(
        self,
    ):
        """
        Setup a simple config with a valid float key with no value set
        which can be parsed correctly but no value will be available
        but because default is provided we expect the default value to be returned
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(float, myGroup, myKey, default=0.5) == 0.5

    def given_simple_valid_string_key_value_when_config_get_with_type_string_then_return_expected_value(
        self,
    ):
        """
        Setup a simple config with a valid string key value
        which can be parsed correctly will return the expected string
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "YES"
        config[myGroup][myKey] = myVal
        config_data = DFastMIConfigParser(config)
        assert config_data.config_get(str, myGroup, myKey) == "YES"

    def given_simple_valid_string_key_value_with_no_value_set_when_config_get_with_type_string_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with a valid float key with no value set
        which can be parsed correctly but will throw no float specified in configuration exception
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        with pytest.raises(Exception) as cm:
            config_data.config_get(str, myGroup, myKey)
        assert (
            str(cm.value)
            == f'No {str.__name__} value specified for required keyword "{myKey}" in block "{myGroup}".'
        )

    def given_simple_valid_string_key_value_with_no_value_set_but_default_is_given_when_config_get_with_type_string_then_return_expected_default(
        self,
    ):
        """
        Setup a simple config with a valid string key with no value set
        which can be parsed correctly but no value will be available
        but because default is provided we expect the default value to be returned
        """
        config = configparser.ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastMIConfigParser(config)
        assert (
            config_data.config_get(str, myGroup, myKey, default="YES sir") == "YES sir"
        )
