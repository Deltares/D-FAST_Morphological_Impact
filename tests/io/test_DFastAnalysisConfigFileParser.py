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
    @pytest.mark.parametrize("truthy_value", ['1', 'yes', 'true', 'on', 'y', 't'])
    def test_boolean_values_that_parse_to_true(self, truthy_value: str):
        # setup
        section = "randomSection"
        key = "randomKey"
        config_parser = ConfigParser()
        config_parser[section] = {key: truthy_value}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getboolean(section, key)

        # assert
        assert result is True

    @pytest.mark.parametrize("falsy_value", ['0', 'no', 'false', 'off', 'n', 'f'])
    def test_boolean_values_that_parse_to_false(self, falsy_value):
        # setup
        section = "randomSection"
        key = "randomKey"
        config_parser = ConfigParser()
        config_parser[section] = {key: falsy_value}

        parser = DFastAnalysisConfigFileParser(config_parser)

        # call
        result = parser.getboolean(section, key)

        # assert
        assert result is False
