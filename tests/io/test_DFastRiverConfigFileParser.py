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
        default_fallback = 0
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
    def _get_config_content() -> str:
        return """
        [General]
        general_int_key = 123   
        int_key_in_general_and_branch_section = 123
        int_key_in_general_and_branch_and_reach = 123
        
        general_float_key = 123.123   
        float_key_in_general_and_branch_section = 123.123
        float_key_in_general_and_branch_and_reach = 123.123
        
        [Branch1]
        int_key_in_general_and_branch_section = 456
        int_key_in_general_and_branch_and_reach = 456
        float_key_in_general_and_branch_section = 456.456
        float_key_in_general_and_branch_and_reach = 456.456
        
        int_key_in_general_and_branch_and_reach1 = 789
        float_key_in_general_and_branch_and_reach1 = 789.789
        """
