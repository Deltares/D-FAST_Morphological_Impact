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
"""
Module for concrete ObservableList implementation. 

Interfaces:


Classes:
    ObservableList

"""
from abc import abstractmethod
from typing import Iterator, List, TypeVar, Generic


T = TypeVar('T')

# Define an observer interface
class IObserver(Generic[T]):
    """
    An interface for observing changes in an ObservableList.
    """
    @abstractmethod
    def notify(self, element: T) -> None:
        """
        Method called when an element is added to the ObservableList.
        """        

class ObservableList(Generic[T]):
    """
    This class is a list object, but notify it's observers when an element is added
    """
    def __init__(self):
        self._list: List[T] = []
        self._observers : List[IObserver[T]] = []

    def __getitem__(self, index):
        return self._list[index]
    
    def __iter__(self) -> Iterator[T]:
        return iter(self._list)
    
    def append(self, element : T) -> None:
        """
        When an element is appended in the list we want to notify the observers 
        of the list so an action can be done from the observers to the element which is added.
        """
        self._list.append(element)
        self._notify_observers(element)

    def add_observer(self, observer: 'IObserver[T]') -> None:
        """
        Add an objects which will observer the list (currently on appending an element)
        """
        self._observers.append(observer)

    def _notify_observers(self, element: T) -> None:
        """
        Notify all observers about the added element.
        """
        for observer in self._observers:
            observer.notify(element)