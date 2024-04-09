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
    def test_getint_key_only_in_general_section_returns_value_from_general_section(self):
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

    @staticmethod
    def _get_reach():
        parent_branch = Branch()
        reach = Reach()
        reach.parent_branch = parent_branch

        return reach

    @staticmethod
    def _get_config_parser():
        config_content = TestDFastRiverConfigFileParser._get_config_content()
        config_parser = ConfigParser()
        config_parser.read_string(config_content)

        return config_parser

    @staticmethod
    def _get_config_content():
        return """
        [General]
        general_int_key = 123       
        """