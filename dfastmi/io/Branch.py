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
from dfastmi.io.IReach import IReach
from dfastmi.io.ObservableList import ObservableList, IObserver
from dfastmi.io.AReach import AReach


class Branch(IBranch, IObserver[AReach]):
    """Class for storing branch information"""
    _name : str
    _qlocation : str
    _reaches: ObservableList[AReach]  # Specify the type parameter AReach for ObservableList


    def __init__(self, branch_name : str = "Branch"):
        """
        Create Branch based on name. 
        Initialize the reaches

        Args:
            branch_name(str) : name of the branch, can only be set in the constructor
        """

        self._name = branch_name
        self._reaches: ObservableList[AReach] = ObservableList[AReach]()
        self._reaches.add_observer(self)

    def get_reach(self, reach_name : str) -> IReach:
        """
        Return the reach from the read reaches list

        Arguments
        ---------
        reach_name : str
            The name of the reach in the branch of the river configuration 
        """
        for reach in self._reaches:
            if reach.name == reach_name:
                return reach
        return None  # Return None if the reach with the given name is not found


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
    def reaches(self) -> ObservableList[AReach]:
        """The reaches in this branch"""
        return self._reaches

    def notify(self, reach:AReach) -> None:
        """When a reach is added to the reaches list we want to set the parent branch in the reach element"""
        reach.parent_branch = self
