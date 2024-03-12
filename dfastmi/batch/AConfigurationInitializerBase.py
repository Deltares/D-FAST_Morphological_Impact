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
from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Tuple
from dfastmi.io.IReach import IReach
from dfastmi.kernel.core import estimate_sedimentation_length

from dfastmi.kernel.typehints import BoolVector, Vector


class AConfigurationInitializerBase(ABC):
    """
    DTO with discharges, times, etc. for analysis
    """
    
    def __init__(self, reach : IReach, config: ConfigParser):
        """
        Initialize the DTO with defaults and then initialize
        """
        self._discharges : Vector = ()
        self._rsigma : Vector = ()
        self._time_fractions_of_the_year : Vector = ()
        self._time_mi : Vector = ()
        self._apply_q : Vector = ()
        self._celerity : Vector = ()
        self._tide_bc : Tuple[str, ...] = ()
        self._q_threshold : float = 0.0
        self._tstag : float = 0.0
        self._ucrit : float = 0.0
        self._n_fields : int = 1
        self._slength : float = 0.0
        self._needs_tide : bool = False
        self._set_ucrit(reach, config)
        self.init(reach, config)
        self._set_slenght()

    @property
    def discharges(self) -> Vector:
        """Array of discharges (Q); one for each forcing condition [m3/s]."""
        return self._discharges

    @property
    def rsigma(self) -> Vector:
        """A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-]."""
        return self._rsigma

    @property
    def q_threshold(self) -> float:
        """River discharge at which the measure becomes active [m3/s]."""
        return self._q_threshold

    @property
    def tstag(self) -> float:
        """Fraction of year during which flow velocity is considered negligible [-]."""
        return self._tstag
    
    @property
    def ucrit(self) -> float:
        """Critical flow velocity [m/s]."""
        return self._ucrit
    
    @property
    def slength(self) -> float:
        """The expected yearly impacted sedimentation length [m]."""
        return self._slength
    
    @property
    def time_fractions_of_the_year(self) -> Vector:
        """A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-]."""
        return self._time_fractions_of_the_year
    
    @property
    def time_mi(self) -> Vector:
        """A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-]."""
        return self._time_mi
    
    @property
    def celerity(self) -> Vector:
        """A vector of values each representing the bed celerity for the period given by the corresponding entry in Q [m/s]."""
        return self._celerity
    
    @property
    def tide_bc(self) -> Tuple[str, ...]:
        """Array of tidal boundary condition; one per forcing condition."""
        return self._tide_bc
    
    @property
    def apply_q(self) -> BoolVector:
        """A list of flags indicating whether the corresponding entry in Q should be used."""
        return self._apply_q
    
    @property
    def needs_tide(self) -> bool:
        """Specifies whether the tidal boundary is needed."""
        return self._needs_tide
    
    @property    
    def n_fields(self) -> int:
        """An int stating the number of fields."""
        return self._n_fields
    
    @abstractmethod
    def init(self,
        reach: IReach,
        config: ConfigParser) -> None:
        """
        Will initialize the config for this reach
        """

    def _set_ucrit(self, reach : IReach, config: ConfigParser) -> None:
        """
        Set critical flow velocity [m/s] based on dfast mi configuration 
        and river default configuration or use min default.

        Arguments
        ---------
        reach : IReach
            Reach which we want to do the initialization on.
        config : ConfigParser        
            The variable containing the configuration.
        
        Return
        ------
        None
        """

        try:
            ucrit = float(config.get("General", "Ucrit", fallback=""))
        except ValueError:
            ucrit = reach.ucritical
        ucrit_min = 0.01
        ucrit = max(ucrit_min, ucrit)
        self._ucrit = ucrit
    
    def _set_slenght(self) -> None:
        """
        Should only be called AFTER(!) init. 
        Set the expected yearly impacted sedimentation length 
        depending on time_mi and celerity.

        Arguments
        ---------
        None

        Return
        ------
        None
        """
        self._slength = estimate_sedimentation_length(self.time_mi, self.celerity)
