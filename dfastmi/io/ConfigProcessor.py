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
Module for ConfigProcessor implementation

Classes:
    ConfigProcessor

"""

from typing import Callable, Type, TypeVar

T = TypeVar('T')  # Define a type variable

class ConfigProcessor:
    """
    Class is used to register processing functions to retrieve values from keys out of DFast MI Configuration files    
    """
    _processors  = {}
    """Contains the parser methods to be used to parse the value string to the data type"""

    def __init__(self):
        self._processors = {}

    def register_processor(self, element_type: Type[T], processor: Callable[[str], T],):
        """Register processing function to parse the type of element to get from the DFast MI Configuration."""
        self._processors[element_type] = processor

    def process_config_value(self, element_type: Type[T], config_value: str) -> T:
        """Call the processing function to parse the type of element to get from the DFast MI Configuration."""
        processor = self._processors.get(element_type)
        if processor:
            return processor(config_value)
        else:
            raise ValueError(f"No config value processor registered for type {element_type}")