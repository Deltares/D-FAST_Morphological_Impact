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
import math
from typing import List, Tuple

from configparser import ConfigParser

import numpy
from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.io.Reach import Reach

from dfastmi.kernel.core import relax_factors
from dfastmi.kernel.typehints import Vector


class ConfigurationInitializer(AConfigurationInitializerBase):
    """
    Determine discharges, times, etc. for version 2 analysis
    """
    def __init__(
        self,
        reach: Reach,
        config: ConfigParser
    ) -> None:
        """
        Determine discharges, times, etc. for version 2 analysis

        Arguments
        ---------
        reach : Reach
            The reach we want to get the levels from.
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        
        Return
        ------
        None
        """
        super().__init__(reach, config)

        self._set_q_threshold(config, reach.qstagnant)
        self._discharges = reach.hydro_q
        self._apply_q = (True,) * len(self.discharges)
        self._set_fraction_times(reach, self.q_threshold, self.discharges)

        # determine the bed celerity based on the input settings
        self._celerity = self.get_bed_celerity(reach, self.discharges)

        self._rsigma = relax_factors(self.discharges, self.time_fractions_of_the_year, reach.qstagnant, self.celerity, reach.normal_width)
        self._tstag = 0.0

        self._n_fields = self._get_tide(reach, config)
        self._needs_tide = reach.use_tide
        if self.needs_tide:
            self._tide_bc = reach.tide_boundary_condition
        self._set_slenght()

    def _get_tide(self, reach: Reach, config: ConfigParser) -> int:
        """
        When using tide retrieve from configuration else return default 1

        Arguments
        ---------
        reach : Reach
            The reach we want to get the levels from.
        config : ConfigParser
            Configuration of the analysis to be run.
        
        Return
        ------
        n_fields : int
            An int stating the number of fields
        """
        
        if reach.use_tide:
            try:
                n_fields = int(config.get("General", "NFields", fallback=""))
            except ValueError:
                n_fields = 1 # Or should I raise ValueError exception?
            if n_fields == 1:
                raise ValueError("Unexpected combination of tides and NFields = 1!")
        else:
            n_fields = 1
        return n_fields

    @staticmethod
    def get_bed_celerity(reach : Reach, discharges :Vector) -> Vector:
        """
        Will create a vector of values each representing the bed celerity for the 
        period given by the corresponding entry in discharge (Q) [m/s] by the 
        celerity type (via a discharge or via legacy using properties).

        Arguments
        ---------
        reach : Reach
            The reach we want to get the levels from.
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].
        
        Return
        ------
        celerity : Vector
            A vector of values each representing the bed celerity for the 
            period given by the corresponding entry in Q [m/s].      
        """
        
        celerity = ()
        if reach.celer_object :
            celerity = reach.celer_object.get_celerity(discharges)

            # set the celerity equal to 0 for discharges less or equal to qstagnant
            celerity = tuple({False:0.0, True:celerity[i]}[discharges[i]>reach.qstagnant] for i in range(len(discharges)))
            
            # check if all celerities are equal to 0. If so, the impact would be 0.
            all_zero = True
            for i, discharge in enumerate(discharges):
                if celerity[i] < 0.0:
                    raise ValueError(f"Invalid negative celerity {celerity[i]} m/s encountered for discharge {discharge} m3/s!")
                if celerity[i] > 0.0:
                    all_zero = False
            if all_zero:
                raise ValueError("The celerities can't all be equal to zero for a measure to have any impact!")

        return celerity

    def _set_fraction_times(self, reach : Reach, q_threshold : float, discharges : Vector) -> None:
        """
        Will set s vector of values each representing the fraction of the year during which 
        the discharge is given by the corresponding entry in Q [-].
        Also will set a vector of values each representing the fraction of the year during 
        which the discharge Q results in morphological impact [-].

        Arguments
        ---------
        reach : Reach
            The reach we want to get the levels from.
        q_threshold : float
            Threshold discharge above which the measure is active.
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].
        
        Return
        ------
        None
        """
        
        if reach.autotime:
            self._set_times(discharges, reach.qfit, reach.qstagnant, q_threshold)
        else:
            self._time_fractions_of_the_year = self.get_time_fractions_of_the_year(reach.hydro_t)
            self._time_mi = self.calculate_time_mi(q_threshold, discharges, self.time_fractions_of_the_year)

    @staticmethod
    def get_time_fractions_of_the_year(time_fractions_of_the_year : List[float]) -> Vector:
        """
        Calculate a vector of values each representing the fraction of the year (T) 
        during which the discharge is given by the corresponding entry in Q [-].
        
        Arguments
        ---------
        time_fractions_of_the_year : List[float]
            Series of values specifying the duration of each stage of the 'hydrograph'.
        
        Return
        ------
        time_fractions_of_the_year : Vector
            A vector of values each representing the fraction of the year (T) 
            during which the discharge is given by the corresponding entry in Q [-].
        """
        sum_of_time_fractions_of_the_year = sum(time_fractions_of_the_year)
        time_fractions_of_the_year = tuple(t / sum_of_time_fractions_of_the_year for t in time_fractions_of_the_year)
        return time_fractions_of_the_year

    @staticmethod
    def calculate_time_mi(q_threshold: float, discharges: Vector, time_fractions_of_the_year: Vector):
        """
        Calculates a vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].

        Arguments
        ---------
        reach : Reach
            The reach we want to get the levels from.
        q_threshold : float
            Threshold discharge above which the measure is active.
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].
        
        Return
        ------
        A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].
        """
        return tuple(0 if discharges[i]<q_threshold else time_fractions_of_the_year[i] for i in range(len(time_fractions_of_the_year)))

    def _set_q_threshold(self, config : ConfigParser, q_stagnant: float) -> None:
        """
        Sets the discharge threshold (q_threshhold) from the configuration.
        If not available or not a float use stagnant discharge value.
        
        Arguments
        ---------
        config : ConfigParser
            Configuration of the analysis to be run.        
        q_stagnant : float
            A discharge below which the river flow is negligible.
        
        Return
        ------
        None
        """
        if "Qthreshold" in config["General"]:
            try:
                q_threshold = float(config.get("General", "Qthreshold", fallback=""))
            except ValueError:
                q_threshold = q_stagnant # Or should I raise ValueError exception?
        else:
            q_threshold = q_stagnant
        self._q_threshold = q_threshold

    def _set_times(self, discharges: Vector, q_fit: Tuple[float, float], q_stagnant: float, q_threshold: float) -> None:
        """
        Get the representative time span for each discharge.

        Arguments
        ---------
        discharges : Vector
            a vector of discharges (Q) included in hydrograph [m3/s].
        q_fit : float
            A discharge and dicharge change determining the discharge exceedance curve [m3/s].
        q_stagnant : float
            A discharge below which the river flow is negligible.
        q_threshold : float
            Discharge below which the measure has no effect (due to measure design) [m3/s].

        Results
        -------
        time_fractions_of_the_year : Vector
            A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
        time_mi : Vector
            A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].
        """
        
        # make sure that the discharges are sorted low to high
        qvec = numpy.array(discharges)
        sorted_qvec = numpy.argsort(qvec)
        q = qvec[sorted_qvec]
        
        t = numpy.zeros(q.shape)
        tmi = numpy.zeros(q.shape)
        p_do = 1.0
        p_th = math.exp(min(0.0, q_fit[0] - max(q_stagnant, q_threshold))/q_fit[1])

        for i, discharge in enumerate(q):
            if discharge <= q_stagnant:
                if i < len(q) - 1 and q[i + 1] > q_stagnant:
                    q_up = q_stagnant
                    p_up = math.exp(min(0.0, q_fit[0] - q_up) / q_fit[1])
                else:
                    p_up = 1.0
            elif i < len(q) - 1:
                q_up = math.sqrt(discharge * q[i + 1])
                p_up = math.exp(min(0.0, q_fit[0] - q_up) / q_fit[1])
            else:
                p_up = 0.0
            
            t[i] = p_do - p_up
            
            if discharge <= q_threshold:
                tmi[i] = max(0.0, p_th - p_up)
            else:
                tmi[i] = min(p_th, p_do) - p_up
            
            p_do = p_up
        
        # correct in case the sorting of the discharges changed the order
        tvec = numpy.zeros(q.shape)
        tvec[sorted_qvec] = t
        self._time_fractions_of_the_year = tuple(ti for ti in tvec)

        tvec_mi = numpy.zeros(q.shape)
        tvec_mi[sorted_qvec] = tmi
        self._time_mi = tuple(ti for ti in tvec_mi)
