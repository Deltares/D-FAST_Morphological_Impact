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
from typing import List, Tuple

from dfastmi.kernel.typehints import Vector


class ICelerObject(ABC):
    "Interface or abstract base class to the CelerObject."
    @abstractmethod
    def verify(self, branch_name : str, reach_name : str):
        """
        Validate the Celerity object.

        """
        
    @abstractmethod
    def get_celerity(self, discharges : Vector) -> Vector:
        """
        Will create a vector of values each representing the bed celerity for the 
        period given by the corresponding entry in discharge (Q) [m/s] by the 
        celerity type (via a discharge or via legacy using properties).

        Arguments
        ---------
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].
        
        Return
        ------
        celerity : Vector
            A vector of values each representing the bed celerity for the 
            period given by the corresponding entry in Q [m/s].      
        """
        pass

class CelerDischarge(ICelerObject):
    """
        Series of discharge, bed celerity pairs
    """
    cdisch : Tuple[float,float] = (0.0, 0.0)
    
    def verify(self, branch_name : str, reach_name : str):
        if self.cdisch == (0.0, 0.0):
             raise ValueError(f'The parameter "CelerQ" must be specified for branch "{branch_name}", '
                              f'reach "{reach_name}" since "CelerForm" is set to 2.')
    def get_celerity(self, discharges : Vector) -> Vector:
        """
        Will create a vector of values each representing the bed celerity for the 
        period given by the corresponding entry in discharge (Q) [m/s] by the 
        celerity type (via a discharge or via legacy using properties).

        Arguments
        ---------
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].
        
        Return
        ------
        celerity : Vector
            A vector of values each representing the bed celerity for the 
            period given by the corresponding entry in Q [m/s].      
        """
        
        
        celerity = tuple(self.cdisch[0]*pow(discharge,self.cdisch[1]) for discharge in discharges)
        return celerity


class CelerProperties(ICelerObject):
    """
        Power-law relation between celerity and discharge
    """
    prop_q : List[float] = []
    prop_c : List[float] = []

    def validate(self):
        return super().validate()
    
    def get_celerity(self, discharges : Vector) -> Vector:
        """
        Will create a vector of values each representing the bed celerity for the 
        period given by the corresponding entry in discharge (Q) [m/s] by the 
        celerity type (via a discharge or via legacy using properties).

        Arguments
        ---------
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].
        
        Return
        ------
        celerity : Vector
            A vector of values each representing the bed celerity for the 
            period given by the corresponding entry in Q [m/s].      
        """
        
        
        celerity = tuple(self._get_celerity(discharge, self.prop_q, self.prop_c) for discharge in discharges)
        return celerity

    def _get_celerity(self, q: float, cel_q: Vector, cel_c: Vector) -> float:
        for i in range(len(cel_q)):
            if q < cel_q[i]:
                if i > 0:
                    c = cel_c[i - 1] + (cel_c[i] - cel_c[i - 1]) * (q - cel_q[i - 1]) / (cel_q[i] - cel_q[i - 1])
                else:
                    c = cel_c[0]
                break
        else:
            c = cel_c[-1]
        return c
