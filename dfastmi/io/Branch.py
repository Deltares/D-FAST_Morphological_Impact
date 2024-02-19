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
Module for concrete Branch implementation

Classes:
    Branch

"""
from dfastmi.io.IBranch import IBranch
from dfastmi.io.ObservableList import ObservableList
from dfastmi.io.Reach import Reach


class Branch(IBranch):
    """Class for storing branch information"""
    _name : str
    _qlocation : str
    _reaches : ObservableList

    def __init__(self, branch_name : str = "Branch"):
        """
        Create Branch based on name. 
        Initialize the reaches

        Args:
            info (dict[str, Any]):
        """

        self._name = branch_name
        self._reaches = ObservableList()
        self._reaches.add_observer(self)

    @property
    def name(self) -> str:
        """Name of the branch"""
        return self._name
    
    @property
    def qlocation(self) -> str:
        """Location name in the branch where we have the discharge"""
        return self._qlocation
    
    @qlocation.setter
    def qlocation(self, value):
        self._qlocation = value

    @property
    def reaches(self) -> ObservableList:
        """The reaches in this branch"""
        return self._reaches

    def notify(self, reach:Reach):
        """When a reach is added to the reaches list we want to set the parent branch in the reach element"""
        print(f"reach '{reach.name}' with (config_key) index '{reach.config_key_index}' was appended to the reaches list of branch {self.name}.")
        reach.parent_branch = self
