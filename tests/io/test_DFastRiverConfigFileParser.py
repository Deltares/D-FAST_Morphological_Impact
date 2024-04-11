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
from typing import Any
import pytest

from dfastmi.io.Branch import Branch
from dfastmi.io.DFastRiverConfigFileParser import DFastRiverConfigFileParser
from dfastmi.io.Reach import Reach


class TestDFastRiverConfigFileParser:
    def test_getint_key_only_in_general_section_returns_value_from_general_section(
        self,
    ):
        # setup
        reach = self._get_reach()
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getint("general_int_key", reach)

        # assert
        assert isinstance(value, int)
        expected_value = 123
        assert value == expected_value

    def test_getint_key_both_in_general_section_and_in_branch_section_returns_value_from_branch_section(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getint("int_key_in_general_and_branch_section", reach)

        # assert
        assert isinstance(value, int)
        expected_value = 456
        assert value == expected_value

    def test_getint_key_in_general_section_and_in_branch_section_and_in_reach_returns_value_from_reach(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getint("int_key_in_general_and_branch_and_reach", reach)

        # assert
        assert isinstance(value, int)
        expected_value = 789
        assert value == expected_value

    def test_getint_key_not_found_and_no_fallback_given_returns_default_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getint("This key does not exist", reach)

        # assert
        assert isinstance(value, int)
        default_fallback = 0
        assert value == default_fallback

    def test_getint_key_not_found_and_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = 123456
        value = parser.getint("This key does not exist", reach, fallback)

        # assert
        assert isinstance(value, int)
        assert value == fallback

    def test_getfloat_key_only_in_general_section_returns_value_from_general_section(
        self,
    ):
        # setup
        reach = self._get_reach()
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloat("general_float_key", reach)

        # assert
        assert isinstance(value, float)
        expected_value = 123.123
        assert value == expected_value

    def test_getfloat_key_both_in_general_section_and_in_branch_section_returns_value_from_branch_section(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloat("float_key_in_general_and_branch_section", reach)

        # assert
        assert isinstance(value, float)
        expected_value = 456.456
        assert value == expected_value

    def test_getfloat_key_in_general_section_and_in_branch_section_and_in_reach_returns_value_from_reach(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloat("float_key_in_general_and_branch_and_reach", reach)

        # assert
        assert isinstance(value, float)
        expected_value = 789.789
        assert value == expected_value

    def test_getfloat_key_not_found_and_no_fallback_given_returns_default_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloat("This key does not exist", reach)

        # assert
        assert isinstance(value, float)
        default_fallback = 0.0
        assert value == default_fallback

    def test_getfloat_key_not_found_and_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = 123456.123456
        value = parser.getfloat("This key does not exist", reach, fallback)

        # assert
        assert isinstance(value, float)
        assert value == fallback

    def test_getboolean_key_only_in_general_section_returns_value_from_general_section(
        self,
    ):
        # setup
        reach = self._get_reach()
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getboolean("general_bool_key", reach)

        # assert
        assert isinstance(value, bool)
        expected_value = True
        assert value == expected_value

    def test_getboolean_key_both_in_general_section_and_in_branch_section_returns_value_from_branch_section(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getboolean("bool_key_in_general_and_branch_section", reach)

        # assert
        assert isinstance(value, bool)
        expected_value = True
        assert value == expected_value

    def test_getboolean_key_in_general_section_and_in_branch_section_and_in_reach_returns_value_from_reach(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getboolean("bool_key_in_general_and_branch_and_reach", reach)

        # assert
        assert isinstance(value, bool)
        expected_value = True
        assert value == expected_value

    def test_getboolean_key_not_found_and_no_fallback_given_returns_default_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getboolean("This key does not exist", reach)

        # assert
        assert isinstance(value, bool)
        default_fallback = False
        assert value == default_fallback

    def test_getboolean_key_not_found_and_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = True
        value = parser.getboolean("This key does not exist", reach, fallback)

        # assert
        assert isinstance(value, bool)
        assert value == fallback

    def test_getstring_key_only_in_general_section_returns_value_from_general_section(
        self,
    ):
        # setup
        reach = self._get_reach()
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstring("general_str_key", reach)

        # assert
        assert isinstance(value, str)
        expected_value = "abc"
        assert value == expected_value

    def test_getstring_key_both_in_general_section_and_in_branch_section_returns_value_from_branch_section(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstring("str_key_in_general_and_branch_section", reach)

        # assert
        assert isinstance(value, str)
        expected_value = "def"
        assert value == expected_value

    def test_getstring_key_in_general_section_and_in_branch_section_and_in_reach_returns_value_from_reach(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstring("str_key_in_general_and_branch_and_reach", reach)

        # assert
        assert isinstance(value, str)
        expected_value = "ghi"
        assert value == expected_value

    def test_getstring_key_not_found_and_no_fallback_given_returns_default_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstring("This key does not exist", reach)

        # assert
        assert isinstance(value, str)
        default_fallback = ""
        assert value == default_fallback

    def test_getstring_key_not_found_and_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = "abcdef"
        value = parser.getstring("This key does not exist", reach, fallback)

        # assert
        assert isinstance(value, str)
        assert value == fallback

    def test_getfloats_key_only_in_general_section_returns_value_from_general_section(
        self,
    ):
        # setup
        reach = self._get_reach()
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloats("general_floats_key", reach)

        # assert
        assert self._is_tuple_of_floats(value)
        expected_value = (123, 123)
        assert value == expected_value

    def test_getfloats_key_both_in_general_section_and_in_branch_section_returns_value_from_branch_section(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloats("floats_key_in_general_and_branch_section", reach)

        # assert
        assert self._is_tuple_of_floats(value)
        expected_value = (456, 456)
        assert value == expected_value

    def test_getfloats_key_in_general_section_and_in_branch_section_and_in_reach_returns_value_from_reach(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloats("floats_key_in_general_and_branch_and_reach", reach)

        # assert
        assert self._is_tuple_of_floats(value)
        expected_value = (789, 789)
        assert value == expected_value

    def test_getfloats_key_not_found_and_no_fallback_given_returns_default_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getfloats("This key does not exist", reach)

        # assert
        assert self._is_tuple_of_floats(value)
        default_fallback = ()
        assert value == default_fallback

    def test_getfloats_key_not_found_and_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = (123.456, 123.456)
        value = parser.getfloats("This key does not exist", reach, fallback)

        # assert
        assert self._is_tuple_of_floats(value)
        assert value == fallback

    def test_getfloats_number_of_values_parsed_not_equal_to_expected_number_of_values_raises_exception(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        with pytest.raises(Exception) as e:
            _ = parser.getfloats("floats_key_in_general_and_branch_and_reach", reach, expected_number_of_values=99)

        expected_message = "Reading floats_key_in_general_and_branch_and_reach for reach randomReach on Branch1 returns \"789 789\". Expecting 99 values."
        assert str(e.value) == expected_message

    def test_getfloats_empty_value_but_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = (123.123, 123.123, 123.123)
        value = parser.getfloats("floats_key_empty", reach, fallback)

        # assert
        assert self._is_tuple_of_floats(value)
        assert value == fallback

    def test_getstrings_key_only_in_general_section_returns_value_from_general_section(
        self,
    ):
        # setup
        reach = self._get_reach()
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstrings("general_strings_key", reach)

        # assert
        assert self._is_tuple_of_strings(value)
        expected_value = ("abc", "abc")
        assert value == expected_value

    def test_getstrings_key_both_in_general_section_and_in_branch_section_returns_value_from_branch_section(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstrings("strings_key_in_general_and_branch_section", reach)

        # assert
        assert self._is_tuple_of_strings(value)
        expected_value = ("def", "def")
        assert value == expected_value

    def test_getstrings_key_in_general_section_and_in_branch_section_and_in_reach_returns_value_from_reach(
        self,
    ):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstrings("strings_key_in_general_and_branch_and_reach", reach)

        # assert
        assert self._is_tuple_of_strings(value)
        expected_value = ("ghi", "ghi")
        assert value == expected_value

    def test_getstrings_key_not_found_and_no_fallback_given_returns_default_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        value = parser.getstrings("This key does not exist", reach)

        # assert
        assert self._is_tuple_of_strings(value)
        default_fallback = ()
        assert value == default_fallback

    def test_getstrings_key_not_found_and_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = ("abcdef", "abcdef")
        value = parser.getstrings("This key does not exist", reach, fallback)

        # assert
        assert self._is_tuple_of_strings(value)
        assert value == fallback

    def test_getstrings_number_of_values_parsed_not_equal_to_expected_number_of_values_raises_exception(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        with pytest.raises(Exception) as e:
            _ = parser.getstrings("strings_key_in_general_and_branch_and_reach", reach, expected_number_of_values=99)

        expected_message = "Reading strings_key_in_general_and_branch_and_reach for reach randomReach on Branch1 returns \"ghi ghi\". Expecting 99 values."
        assert str(e.value) == expected_message

    def test_getstrings_empty_value_but_fallback_given_returns_fallback(self):
        # setup
        reach = self._get_reach(1, "Branch1")
        config = self._get_config_parser()
        parser = DFastRiverConfigFileParser(config)

        # call
        fallback = ("abc", "abc", "abc")
        value = parser.getstrings("strings_key_empty", reach, fallback)

        # assert
        assert self._is_tuple_of_strings(value)
        assert value == fallback


    @staticmethod
    def _get_reach(
        reach_index: int = 1, branch_name: str = "randomBranchName"
    ) -> Reach:
        parent_branch = Branch(branch_name)
        reach = Reach("randomReach", reach_index)
        reach.parent_branch = parent_branch

        return reach

    @staticmethod
    def _get_config_parser() -> ConfigParser:
        config_content = TestDFastRiverConfigFileParser._get_config_content()
        config_parser = ConfigParser()
        config_parser.read_string(config_content)

        return config_parser

    @staticmethod
    def _is_tuple_of_floats(value: Any) -> bool:
        return isinstance(value, tuple) and all(isinstance(item, float) for item in value)

    @staticmethod
    def _is_tuple_of_strings(value: Any) -> bool:
        return isinstance(value, tuple) and all(isinstance(item, str) for item in value)
    @staticmethod
    def _get_config_content() -> str:
        return """
        [General]
        general_int_key = 123   
        int_key_in_general_and_branch_section = 123
        int_key_in_general_and_branch_and_reach = 123
        
        general_float_key = 123.123   
        float_key_in_general_and_branch_section = 123.123
        float_key_in_general_and_branch_and_reach = 123.123
        
        general_bool_key = True
        bool_key_in_general_and_branch_section = False
        bool_key_in_general_and_branch_and_reach = True
        
        general_str_key = abc
        str_key_in_general_and_branch_section = abc
        str_key_in_general_and_branch_and_reach = abc
        
        general_floats_key = 123 123
        floats_key_in_general_and_branch_section = 123 123
        floats_key_in_general_and_branch_and_reach = 123 123
        floats_key_empty = 
        
        general_strings_key = abc abc
        strings_key_in_general_and_branch_section = abc abc
        strings_key_in_general_and_branch_and_reach = abc abc
        strings_key_empty = 
        
        [Branch1]
        int_key_in_general_and_branch_section = 456
        int_key_in_general_and_branch_and_reach = 456
        float_key_in_general_and_branch_section = 456.456
        float_key_in_general_and_branch_and_reach = 456.456
        bool_key_in_general_and_branch_section = True
        bool_key_in_general_and_branch_and_reach = False
        str_key_in_general_and_branch_section = def
        str_key_in_general_and_branch_and_reach = def
        floats_key_in_general_and_branch_section = 456 456
        floats_key_in_general_and_branch_and_reach = 456 456
        strings_key_in_general_and_branch_section = def def
        strings_key_in_general_and_branch_and_reach = def def
        
        int_key_in_general_and_branch_and_reach1 = 789
        float_key_in_general_and_branch_and_reach1 = 789.789
        bool_key_in_general_and_branch_and_reach1 = True
        str_key_in_general_and_branch_and_reach1 = ghi
        floats_key_in_general_and_branch_and_reach1 = 789 789
        strings_key_in_general_and_branch_and_reach1 = ghi ghi
        """


