# -*- coding: utf-8 -*-
"""
Copyright © 2024 Stichting Deltares.

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
from configparser import ConfigParser

import pytest

from dfastmi.io.DFastAnalysisConfigFileParser import DFastAnalysisConfigFileParser


class TestDFastAnalysisConfigFileParser:
    section = "random section"
    key = "random key"

    @pytest.mark.parametrize("truthy_value", ["1", "yes", "true", "on", "y", "t"])
    def test_boolean_values_that_parse_to_true(self, truthy_value: str):
        # setup
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: truthy_value}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getboolean(self.section, self.key)

        # assert
        assert result is True

    @pytest.mark.parametrize("falsy_value", ["0", "no", "false", "off", "n", "f"])
    def test_boolean_values_that_parse_to_false(self, falsy_value):
        # setup
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: falsy_value}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getboolean(self.section, self.key)

        # assert
        assert result is False

    def test_getint_valid_int_value_returns_expected_int_value(self):
        # setup
        value = 123
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getint(self.section, self.key)

        # assert
        assert isinstance(result, int)
        assert result == value

    def test_getint_unknown_section_without_fallback_returns_default_fallback_value(
        self,
    ):
        # setup
        value = 123
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        section_that_does_not_exist = "This section does not exist"
        result = parser.getint(section_that_does_not_exist, self.key)

        # assert
        assert isinstance(result, int)
        default_fallback = 0
        assert result == default_fallback

    def test_getint_unknown_section_with_fallback_returns_fallback_value(self):
        # setup
        value = 123
        fallback = 456
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        section_that_does_not_exist = "This section does not exist"
        result = parser.getint(section_that_does_not_exist, self.key, fallback)

        # assert
        assert isinstance(result, int)
        assert result == fallback

    def test_getint_unknown_key_without_fallback_returns_default_fallback_value(self):
        # setup
        value = 123
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        key_that_does_not_exist = "This key does not exist"
        result = parser.getint(self.section, key_that_does_not_exist)

        # assert
        assert isinstance(result, int)
        default_fallback = 0
        assert result == default_fallback

    def test_getint_unknown_key_with_fallback_returns_fallback_value(self):
        # setup
        value = 123
        fallback = 456
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        key_that_does_not_exist = "This key does not exist"
        result = parser.getint(self.section, key_that_does_not_exist, fallback)

        # assert
        assert isinstance(result, int)
        assert result == fallback

    @pytest.mark.parametrize("non_int_value", ["", "  ", "not an int"])
    def test_getint_value_not_an_int_raises_error(self, non_int_value: str):
        # setup
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: non_int_value}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call / assert
        with pytest.raises(ValueError):
            _ = parser.getint(self.section, self.key)

    def test_getfloat_valid_float_value_returns_expected_float_value(self):
        # setup
        value = 123.456
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getfloat(self.section, self.key)

        # assert
        assert isinstance(result, float)
        assert result == value

    def test_getfloat_unknown_section_without_fallback_returns_default_fallback_value(
        self,
    ):
        # setup
        value = 123.456
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        section_that_does_not_exist = "This section does not exist"
        result = parser.getfloat(section_that_does_not_exist, self.key)

        # assert
        assert isinstance(result, float)
        default_fallback = 0.0
        assert result == default_fallback

    def test_getfloat_unknown_section_with_fallback_returns_fallback_value(self):
        # setup
        value = 123.456
        fallback = 456.789
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        section_that_does_not_exist = "This section does not exist"
        result = parser.getfloat(section_that_does_not_exist, self.key, fallback)

        # assert
        assert isinstance(result, float)
        assert result == fallback

    def test_getfloat_unknown_key_without_fallback_returns_default_fallback_value(self):
        # setup
        value = 123.456
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        key_that_does_not_exist = "This key does not exist"
        result = parser.getfloat(self.section, key_that_does_not_exist)

        # assert
        assert isinstance(result, float)
        default_fallback = 0.0
        assert result == default_fallback

    def test_getfloat_unknown_key_with_fallback_returns_fallback_value(self):
        # setup
        value = 123.456
        fallback = 456.789
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        key_that_does_not_exist = "This key does not exist"
        result = parser.getfloat(self.section, key_that_does_not_exist, fallback)

        # assert
        assert isinstance(result, float)
        assert result == fallback

    @pytest.mark.parametrize("non_float_value", ["", "  ", "not a float"])
    def test_getfloat_value_not_a_float_raises_error(self, non_float_value: str):
        # setup
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: non_float_value}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call / assert
        with pytest.raises(ValueError):
            _ = parser.getfloat(self.section, self.key)

    def test_getstring_returns_expected_string_value(self):
        # setup
        value = "randomString"
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getstring(self.section, self.key)

        # assert
        assert isinstance(result, str)
        assert result == value

    def test_getstring_unknown_section_without_fallback_returns_default_fallback_value(
        self,
    ):
        # setup
        value = "randomString"
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        section_that_does_not_exist = "This section does not exist"
        result = parser.getstring(section_that_does_not_exist, self.key)

        # assert
        assert isinstance(result, str)
        default_fallback = ""
        assert result == default_fallback

    def test_getstring_unknown_section_with_fallback_returns_fallback_value(self):
        # setup
        value = "randomString"
        fallback = "Super awesome fallback value"
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        section_that_does_not_exist = "This section does not exist"
        result = parser.getstring(section_that_does_not_exist, self.key, fallback)

        # assert
        assert isinstance(result, str)
        assert result == fallback

    def test_getstring_unknown_key_without_fallback_returns_default_fallback_value(
        self,
    ):
        # setup
        value = "randomString"
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        key_that_does_not_exist = "This key does not exist"
        result = parser.getstring(self.section, key_that_does_not_exist)

        # assert
        assert isinstance(result, str)
        default_fallback = ""
        assert result == default_fallback

    def test_getstring_unknown_key_with_fallback_returns_fallback_value(self):
        # setup
        value = "randomString"
        fallback = "Super awesome fallback value"
        config_parser = ConfigParser()
        config_parser[self.section] = {self.key: str(value)}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        key_that_does_not_exist = "This key does not exist"
        result = parser.getstring(self.section, key_that_does_not_exist, fallback)

        # assert
        assert isinstance(result, str)
        assert result == fallback


class Test_config_get_range:
    def given_simple_valid_range_string_key_value_when_config_get_range_then_return_expected_tuple_range_value(
        self,
    ):
        """
        Setup a simple config with a valid range string key value
        which can be parsed correctly will return the expected tuple range
        """
        config = ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "[0.0:10.0]"
        config[myGroup][myKey] = myVal
        config_data = DFastAnalysisConfigFileParser(config)
        assert config_data.get_range(myGroup, myKey, (0.0, 0.0)) == (0.0, 10.0)

    def given_simple_valid_range_string_key_value_with_decending_range_when_config_get_range_then_return_expected_tuple_range_value(
        self,
    ):
        """
        Setup a simple config with a valid range string key value
        but with decending range
        which can be parsed correctly will return the expected tuple range
        """
        config = ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "[10.0:0.0]"
        config[myGroup][myKey] = myVal
        config_data = DFastAnalysisConfigFileParser(config)
        assert config_data.get_range(myGroup, myKey, (0.0, 0.0)) == (0.0, 10.0)

    def given_simple_valid_range_string_key_with_invalid_value_when_config_get_range_then_throw_exception(
        self,
    ):
        """
        Setup a simple config with an invalid range string key value
        will throw an range exception
        """
        config = ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0.0-10.0"
        config[myGroup][
            myKey
        ] = myVal  # even on not setting this value we expect the exception
        config_data = DFastAnalysisConfigFileParser(config)
        with pytest.raises(ValueError) as cm:
            config_data.get_range(myGroup, myKey, None)
        assert str(
            cm.value
        ) == 'Invalid range specification "{}" for required keyword "{}" in block "{}".'.format(
            myVal, myKey, myGroup
        )

    def given_simple_valid_range_string_key_with_invalid_value_but_with_default_value_when_config_get_range_then_return_default(
        self,
    ):
        """
        Setup a simple config with a valid string key with no value set
        which can't be parsed correctly because range string value is invalid
        but because default is provided we expect the default value to be returned
        """
        config = ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        config_data = DFastAnalysisConfigFileParser(config)
        assert config_data.get_range(myGroup, myKey, "YES") == "YES"

    def given_simple_valid_but_uncommon_range_string_key_value_when_config_get_range_then_return_expected_tuple_range_value(
        self,
    ):
        """
        Setup a simple config with a valid range string key value
        but in uncommon format
        which can be parsed correctly will return the expected tuple range
        """
        config = ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "0.0:10.0"
        config[myGroup][myKey] = myVal
        config_data = DFastAnalysisConfigFileParser(config)
        assert config_data.get_range(myGroup, myKey, (0.0, 0.0)) == (0.0, 10.0)

    def given_simple_valid_but_uncommon_range_in_decending_order_string_key_value_when_config_get_range_then_return_expected_tuple_range_value(
        self,
    ):
        """
        Setup a simple config with a valid range string key value
        but in uncommon format and in decending order
        which can be parsed correctly will return the expected tuple range
        """
        config = ConfigParser()
        myGroup = "GROUP"
        config.add_section(myGroup)
        myKey = "KEY"
        myVal = "10.0:0.0"
        config[myGroup][myKey] = myVal
        config_data = DFastAnalysisConfigFileParser(config)
        assert config_data.get_range(myGroup, myKey, (0.0, 0.0)) == (0.0, 10.0)
