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
Module for ICelerObject interface and CelerObject implementations

Interfaces:
    ICelerObject

Classes:
    CelerDischarge
    CelerProperties

"""
from abc import ABC, abstractmethod
from typing import List


class ICelerObject(ABC):
    "Interface or abstract base class to the CelerObject."
    @abstractmethod
    def validate(self):
        pass
    


class CelerDischarge(ICelerObject):
    cdisch = tuple[float,float]
    
    def validate(self):
        if self.cdisch == (0.0, 0.0):            
            # raise Exception(
            #             'The parameter "CelerQ" must be specified for branch "{}", reach "{}" since "CelerForm" is set to 2.'.format(
            #                 branch,
            #                 reach,
            #             )
            #         )
            return
    


class CelerProperties(ICelerObject):
    prop_q : List[float]
    prop_c : List[float]

    def validate(self):
        return super().validate()