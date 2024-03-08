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
import configparser
import math
from typing import Tuple

import numpy
from dfastmi.batch.AConfigurationChecker import AConfigurationCheckerBase
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.Reach import Reach

from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

from dfastmi.batch.AConfigurationChecker import AConfigurationCheckerBase
from dfastmi.io.Reach import Reach
from dfastmi.kernel.core import get_celerity, relax_factors
from dfastmi.kernel.typehints import BoolVector, Vector
class ConfigurationChecker(AConfigurationCheckerBase):
    """
        Check if a version 2 analysis configuration is valid.
    """
    def check_configuration(self,
                            rivers: RiversObject,
                            config: configparser.ConfigParser) -> bool:
        """
        Check if a version 2 analysis configuration is valid.

        Arguments
        ---------
        rivers: RiversObject
            An object containing the river data.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        try:
            reach = self._get_reach(rivers, config, Reach)
        except LookupError:
            return False
        except ValueError:
            return False

        hydro_q = reach.hydro_q
        q_stagnant = reach.qstagnant
        if config.has_section("General") and config.has_option("General", "Qthreshold") :
            try:
                q_threshold = config.getfloat("General", "Qthreshold")
            except ValueError:
                q_threshold_str = config.get("General", "Qthreshold", fallback="")
                ApplicationSettingsHelper.log_text(f"Please this configuration has in the General section an option for Qthreshold"
                                                   f"but is not float but : {q_threshold_str}!" 
                                                   f"Using q_stagnant as q_threshold : {q_stagnant}")
                q_threshold = q_stagnant
        else:
            q_threshold = q_stagnant        
        n_cond = len(hydro_q)

        return_value = False
        for i in range(n_cond):
            if hydro_q[i] > q_threshold : 
                success = self._check_configuration_cond(config, hydro_q[i])
                if success and not return_value:
                    return_value = True
        return return_value
    
    def get_levels(
        self,
        reach: Reach,
        config: configparser.ConfigParser,
        nwidth: float
    ) -> Tuple[Vector, BoolVector, float, Vector, float, Vector, Vector, Vector, bool, int, Tuple[str, ...]]:
        """
        Determine discharges, times, etc. for version 2 analysis

        Arguments
        ---------
        reach : ReachLegacy
            The reach we want to get the levels from.
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        nwidth : float
            Normal river width (from rivers configuration file) [m].

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
        
        q_stagnant = reach.qstagnant
        q_threshold = self._get_q_threshold(config, q_stagnant)

        discharges = reach.hydro_q
        apply_q = (True,) * len(discharges)
        T, time_mi = self._get_fraction_times(reach, q_threshold, discharges)
        
        # determine the bed celerity based on the input settings
        celerity = self._get_bed_celerity(reach, discharges)

        rsigma = relax_factors(discharges, T, q_stagnant, celerity, nwidth)
        tstag = 0
        
        n_fields = self._get_tide(reach, config)
        return (discharges, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity, reach.use_tide, n_fields, reach.tide_bc if reach.use_tide else ())

    def _get_tide(self, reach: Reach, config: configparser.ConfigParser):
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

    def _get_bed_celerity(self, reach, discharges):
        cform = reach.celer_form
        if cform == 1:
            prop_q = reach.celer_object.prop_q
            prop_c = reach.celer_object.prop_c
            celerity = tuple(get_celerity(q, prop_q, prop_c) for q in discharges)
        elif cform == 2:
            cdisch = reach.celer_object.cdisch
            celerity = tuple(cdisch[0]*pow(q,cdisch[1]) for q in discharges)
         
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

    def _get_fraction_times(self, reach:Reach, q_threshold, discharges):
        if reach.autotime:            
            time_fractions_of_the_year, time_mi = self._get_times(discharges, reach.qfit, reach.qstagnant, q_threshold)
        else:
            time_fractions_of_the_year = reach.hydro_t
            sum_of_time_fractions_of_the_year = sum(time_fractions_of_the_year)
            time_fractions_of_the_year = tuple(t / sum_of_time_fractions_of_the_year for t in time_fractions_of_the_year)
            time_mi = tuple(0 if discharges[i]<q_threshold else time_fractions_of_the_year[i] for i in range(len(time_fractions_of_the_year)))
        return time_fractions_of_the_year,time_mi

    def _get_q_threshold(self, config, q_stagnant):
        if "Qthreshold" in config["General"]:
            try:
                q_threshold = float(config.get("General", "Qthreshold", fallback=""))
            except ValueError:
                q_threshold = q_stagnant # Or should I raise ValueError exception?
        else:
            q_threshold = q_stagnant
        return q_threshold

    def _get_times(self, discharges: Vector, q_fit: Tuple[float, float], q_stagnant: float, q_threshold: float) -> Tuple[Vector, Vector]:
        """
        Get the representative time span for each discharge.

        Arguments
        ---------
        discharges : Vector
            a vector of discharges (Q) included in hydrograph [m3/s].
        q_fit : float
            A discharge and dicharge change determining the discharge exceedance curve [m3/s].
        q_stagnant : float
            Discharge below which flow conditions are stagnant [m3/s].
        q_threshold : float
            Discharge below which the measure has no effect (due to measure design) [m3/s].

        Results
        -------
        T : Vector
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
        for i in range(len(q)):
            if q[i] <= q_stagnant:
                # if the current discharge is in the stagnant regime
                if i < len(q)-1 and q[i+1] > q_stagnant:
                    # if the next discharge is not in the stagnant regime, then the stagnant discharge is the boundary between the two regimes
                    # this will associate the whole stagnant period with this discharge since p_do = 1
                    q_up = q_stagnant
                    p_up = math.exp(min(0.0, q_fit[0] - q_up)/q_fit[1])
                else:
                    # if the next discharge is also in the stagnant regime, keep p_up = p_do = 1
                    # this will associate zero time with this discharge
                    p_up = 1.0
            elif i < len(q)-1:
                # if the current discharge is above the stagnant regime and more (higher) discharges follow, select the geometric midpoint as transition
                q_up = math.sqrt(q[i] * q[i+1])
                p_up = math.exp(min(0.0, q_fit[0] - q_up)/q_fit[1])
            else:
                # if there are no higher discharges, associate this discharge with the whole remaining range until "infinite discharge"
                # q_up = inf
                p_up = 0.0
            t[i] = p_do - p_up
            
            if q[i] <= q_threshold:
                # if the measure is inactive for the current discharge, this discharge range may still be associated with impact at the high discharge end
                tmi[i] = max(0.0, p_th - p_up)
            else:
                # if the measure is active for the current discharge, the impact of this discharge range may be reduced at the low discharge end
                tmi[i] = min(p_th, p_do) - p_up
            p_do = p_up
        
        # correct in case the sorting of the discharges changed the order
        tvec = numpy.zeros(q.shape)
        tvec[sorted_qvec] = t
        T = tuple(ti for ti in tvec)

        tvec_mi = numpy.zeros(q.shape)
        tvec_mi[sorted_qvec] = tmi
        time_mi = tuple(ti for ti in tvec_mi)

        return T, time_mi

    def _check_configuration_cond(self, 
                                 config: configparser.ConfigParser,
                                 discharge: float) -> bool:
        """
        Check if a version 2 analysis condition configuration is valid for a discharge.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.
        
        discharge : float
            Discharge (q) [m3/s]

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration condition is valid for this discharge.
        
        """
        return_value = True
        has_condition_section_for_this_discharge = False
        condition_sections = [section for section in config.sections() if section[0] == "C"]
        if len(condition_sections) == 0:
            ApplicationSettingsHelper.log_text("No condition sections found in conditions configurations file!")
            return False

        for condition in condition_sections:
            if config.has_option(condition, "Discharge"):
                try:
                    discharge_cond = config.getfloat(condition, "Discharge")
                except ValueError:
                    discharge_cond_str = config.get(condition, "Discharge", fallback="")
                    ApplicationSettingsHelper.log_text(f"Please this is a condition ({condition}), "
                        f"but discharge in condition cfg file is not float but has value : {discharge_cond_str}!")
                    continue

                if abs(discharge - discharge_cond) <= 0.001:
                    has_condition_section_for_this_discharge = True
                    
                    # we found the correct condition
                    return_value = self._check_key_with_file_value_and_set_return_value_if_needed(config, return_value, condition, "Reference")
                    return_value = self._check_key_with_file_value_and_set_return_value_if_needed(config, return_value, condition, "WithMeasure")
            else:
                ApplicationSettingsHelper.log_text(f"Please this is a condition : {condition}, but 'Discharge' key is not set!")
                if return_value:
                    return_value = False

        return return_value and has_condition_section_for_this_discharge

    def _check_key_with_file_value_and_set_return_value_if_needed(self,
               config : configparser.ConfigParser,
               return_value : bool,
               condition : str,
               key : str) -> bool:
        """
        Check if key exist as option in the section of this condition.
        If exist check if file which is the key value is representing exist.        
        """
        if not self._check_key_with_file_value(config, condition, key) and return_value:
            return_value = False
        return return_value
