# -*- coding: utf-8 -*-
"""
Copyright (C) 2024 Stichting Deltares.

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
"""
Module for RiverConfigElementProcessor implementation

Classes:
    RiverConfigElementProcessor

"""
from typing import Callable, Optional, Tuple, Type, TypeVar
from dfastmi.io.Reach import Reach
T = TypeVar('T')  # Define a type variable


class RiverConfigElementProcessor:
    """
    Class is used to register processing functions to retrieve values from keys out of River Configuration files
    """
    _processors = {}
    """Contains the the processing functions to process the value string to the data type"""
    
    _parsers = {}
    """Contains the parser methods to be used in the processing functions to parse the value string to the data type"""

    def __init__(self):
        self._processors = {}
        self._parsers = {}

    def register_processor(self, element_type: Type[T], processor: Callable[[str, str, Reach], T], parser: Callable[[str], Tuple[T, ...]]):
        """Register processing functions and parser to parse the type of element to get from the river configuration."""
        self._processors[element_type] = processor
        self._parsers[element_type] = parser

    def process_river_element(self, element_type: Type[T], key: str, entry_value: str, reach: Reach, default: Optional[T] = None, expected_number_of_values: Optional[int] = None) -> T:
        """Call processing function and parser to parse the type of element to get from the river configuration."""
        processor = self._processors.get(element_type)
        if processor:
            parser = self._parsers.get(element_type)
            if parser:
                return processor(key, entry_value, reach, parser, default, expected_number_of_values)
            else:
                raise ValueError(f"No string parser registered for type {element_type}")
        else:
            raise ValueError(f"No processor registered for type {element_type}")