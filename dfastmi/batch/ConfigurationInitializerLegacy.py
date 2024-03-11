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
from typing import List

from configparser import ConfigParser
from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase

from dfastmi.io.ReachLegacy import ReachLegacy
from dfastmi.kernel.legacy import char_discharges, char_times
from dfastmi.kernel.typehints import BoolVector, QRuns


class ConfigurationInitializerLegacy(AConfigurationInitializerBase):
    """
    Determine discharges, times, etc. for version 1 analysis
    """

    def init(
        self,
        reach: ReachLegacy,
        config: ConfigParser
    ) -> None:
        """
        Determine discharges, times, etc. for version 1 analysis

        Arguments
        ---------
        reach : ReachLegacy
            The reach we want to get the levels from.
        config : configparser.ConfigParser
            Configuration of the analysis to be run.        

        Return
        ------
        discharges : Vector
            Array of discharges (Q); one for each forcing condition [m3/s].
        apply_q : BoolVector
            A list of flags indicating whether the corresponding entry in Q should be used.
        q_threshold : float
            River discharge at which the measure becomes active [m3/s].
        time_mi : Vector
            A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].
        tstag : float
            Fraction of year during which flow velocity is considered negligible [-].
        fractions_of_the_year : Vector
            A vector of values each representing the fraction of the year (T) during which the discharge is given by the corresponding entry in Q [-].
        rsigma : Vector
            A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
        celerity : Vector
            A vector of values each representing the bed celerity for the period given by the corresponding entry in Q [m/s].
        needs_tide : bool
            A bool stating if the calculation needs to make use of tide
        n_fields : int
            An int stating the number of fields
        """
        
        celerity_hg = reach.proprate_high
        celerity_lw = reach.proprate_low
        self._q_threshold = self._get_q_threshold_from_config(config)
        
        self._set_discharges(reach, config, reach.qstagnant, self.q_threshold, celerity_hg, celerity_lw, reach.normal_width)
        self._time_mi = tuple(0 if self.discharges[i] is None or self.discharges[i]<= reach.qstagnant else self.time_fractions_of_the_year[i] for i in range(len(self.time_fractions_of_the_year)))
        self._celerity = (celerity_lw, celerity_hg, celerity_hg)

    def _set_discharges(
        self,
        reach : ReachLegacy,
        config: ConfigParser,
        q_stagnant: float,
        q_threshold: float,
        celerity_hg: float,
        celerity_lw: float,
        nwidth: float,
    ) -> None :
        """
        Get the simulation discharges in batch mode (no user interaction).

        Arguments
        ---------
        reach : ReachLegacy
            The reach we want to get the discharges from.
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        q_stagnant : float
            Discharge below which the river flow is negligible [m3/s].
        celerity_hg : float
            Bed celerity during transitional and flood periods (from rivers configuration file) [m/s].
        celerity_lw : float
            Bed celerity during low flow period (from rivers configuration file) [m/s].
        nwidth : float
            Normal river width (from rivers configuration file) [m].        
        q_threshold : Optional[float]
            River discharge at which the measure becomes active [m3/s].
        
        Results
        -------
        three_characteristic_discharges : QRuns
            Tuple of (at most) three characteristic discharges [m3/s].
        apply_q : Tuple[bool, bool, bool]
            A list of 3 flags indicating whether each value should be used or not.
            The Q1 value can't be set to None because it's needed for char_times.
        tstag : float
            Fraction of year during which flow velocity is considered negligible [-].
        fractions_of_the_year : Vector
            A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
        rsigma : Vector
            A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
        """
        q_bankfull = self._get_q_bankfull_from_config(config, q_threshold, reach.qlevels)

        three_characteristic_discharges, self._apply_q = char_discharges(reach.qlevels, reach.dq, q_threshold, q_bankfull)

        self._tstag, self._time_fractions_of_the_year, self._rsigma = char_times(
            reach.qfit, q_stagnant, three_characteristic_discharges, celerity_hg, celerity_lw, nwidth
        )

        q_list = self._discharge_from_config(config, three_characteristic_discharges, self.apply_q)
        self._discharges = (q_list[0], q_list[1], q_list[2])

    def _discharge_from_config(self, config : ConfigParser, three_characteristic_discharges : QRuns, apply_q : BoolVector) -> List:
        """
        Tuple of (at most) three characteristic discharges [m3/s].
        
        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        three_characteristic_discharges : QRuns
            A tuple of 3 discharges for which simulations should be run (can later
            be adjusted by the user)
        apply_q : BoolVector
            A tuple of 3 flags indicating whether each value should be used or not.
            The Q1 value can't be set to None because it's needed for char_times.
        Results
        -------
        q_list : list 
            A list of discharges
        """
        q_list = list(three_characteristic_discharges)
        for iq in range(3):
            if apply_q[iq]:
                discharge = config.get(f"Q{iq + 1}", "Discharge", fallback="")
                if self._is_float_str(discharge):
                    q_list[iq] = float(discharge)
                else:
                    q_list[iq] = None
            else:
                q_list[iq] = None
        return q_list

    def _get_q_bankfull_from_config(self, config, q_threshold, q_levels) -> float:
        """
        Get the simulation discharge at which measure reaches bankfull 
        from configuration in batch mode (no user interaction).

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        q_threshold : Optional[float]
            River discharge at which the measure becomes active 
        q_levels : 
            Characteristic discharges used by algorithm [m3/s].
        Results
        -------
        q_bankfull : float
            River discharge at which the measure is bankfull [m3/s].
        """
        q_bankfull = 0.0
        if q_threshold is None or q_threshold < q_levels[1]:
            q_bankfull = config.get("General", "Qbankfull", fallback="0.0")
            if self._is_float_str(q_bankfull):
                q_bankfull = float(q_bankfull)
        return q_bankfull

    def _get_q_threshold_from_config(self, config):
        """
        Get the simulation discharge threshold from configuration in batch mode (no user interaction).

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        
        Results
        -------
        q_threshold : Optional[float]
            River discharge at which the measure becomes active [m3/s].
        """

        q_threshold = config.get("General", "Qthreshold", fallback="")
        if self._is_float_str(q_threshold):
            q_threshold = float(q_threshold)
        else:
            q_threshold = None
        return q_threshold

    def _is_float_str(self, string:str) -> bool:
        """
        Check if a string represents a (floating point) number.

        Arguments
        ---------
        string : str
            The string to be checked.

        Returns
        -------
        success : bool
            Boolean indicating whether the the string can be converted to a number or not.
        """
        try:
            float(string)
            return True
        except ValueError:
            return False
