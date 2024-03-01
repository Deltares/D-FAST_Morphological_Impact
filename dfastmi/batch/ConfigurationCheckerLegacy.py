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
from typing import Callable, Optional, Tuple
from dfastmi.batch.AConfigurationChecker import AConfigurationCheckerBase
import dfastmi.kernel.core
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Reach import ReachLegacy
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.core import BoolVector, QRuns, Vector

WAQUA_EXPORT = "WAQUA export"
DFLOWFM_MAP = "D-Flow FM map"

class ConfigurationCheckerLegacy(AConfigurationCheckerBase):
    """
        Check if a version 1 / legacy analysis configuration is valid.
    """
    _validators = {}
    """Contains the configuration validator be used depending on mode"""

    def __init__(self):
        self._register_validator(WAQUA_EXPORT, self._check_configuration_cond_waqua)
        self._register_validator(DFLOWFM_MAP, self._check_configuration_cond_fm)

    def _register_validator(self, mode: str, validator: Callable[[configparser.ConfigParser,  int], bool]):
        """Register creator function to create a AConfigurationChecker object."""
        if mode not in self._validators:
            self._validators[mode] = validator
        #else:
            #print(f"Validator {mode} already exists in the dictionary.")

    def _validate(self, mode: str, config: configparser.ConfigParser, i : int ) -> bool:
        """
        Call the Validator function to valdite a ConfigurationCheckerLegacy object.

        Arguments
        ---------
        mode: str
            The mode in the configuration to validate for.

        Returns
        -------
        bool
            calls the existing / registered validator and validates the provided configuration.
        """
        validate_method = self._validators.get(mode)
        if validate_method:
            return validate_method(config, i)
        else:
            return False

    def check_configuration(self, rivers: RiversObject, config: configparser.ConfigParser) -> bool:
        """
        Check if a version 1 analysis configuration is valid.

        Arguments
        ---------
        rivers: RiversObject
            A dictionary containing the river data.
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        try:
            reach = self._get_reach(rivers, config)
        except LookupError:
            return False

        nwidth = reach.normal_width
        [_, apply_q, _, _, _, _, _, _] = self._get_levels(reach, config, nwidth)

        mode_str = config.get("General", "Mode", fallback=DFLOWFM_MAP)
        for i in range(3):
            if not apply_q[i]:
                continue

            if not self._validate(mode_str, config, i) :
                return False

        return True

    def _get_levels(
        self,
        reach: ReachLegacy,
        config: configparser.ConfigParser,
        nwidth: float
    ) -> Tuple[Vector, BoolVector, float, Vector, float, Vector, Vector, Vector]:
        """
        Determine discharges, times, etc. for version 1 analysis

        Arguments
        ---------
        rivers : RiversObject
            A dictionary containing the river data.
        ibranch : int
            Number of selected branch.
        ireach : int
            Number of selected reach.
        config : configparser.ConfigParser
            Configuration of the analysis to be run.
        nwidth : float
            Normal river width (from rivers configuration file) [m].

        Return
        ------
        Q : Vector
            Array of discharges; one for each forcing condition [m3/s].
        apply_q : BoolVector
            A list of flags indicating whether the corresponding entry in Q should be used.
        q_threshold : float
            River discharge at which the measure becomes active [m3/s].
        time_mi : Vector
            A vector of values each representing the fraction of the year during which the discharge Q results in morphological impact [-].
        tstag : float
            Fraction of year during which flow velocity is considered negligible [-].
        T : Vector
            A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
        rsigma : Vector
            A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
        celerity : Vector
            A vector of values each representing the bed celerity for the period given by the corresponding entry in Q [m/s].
        """
        q_stagnant = reach.qstagnant
        celerity_hg = reach.proprate_high
        celerity_lw = reach.proprate_low

        (
            all_q,
            q_threshold,
            q_bankfull,
            q_fit,
            Q1,
            apply_q1,
            tstag,
            T,
            rsigma,
        ) = self._batch_get_discharges(
            reach, config, q_stagnant, celerity_hg, celerity_lw, nwidth
        )
        Q = Q1
        apply_q = apply_q1
        time_mi = tuple(0 if Q[i] is None or Q[i]<=q_stagnant else T[i] for i in range(len(T)))
        celerity = (celerity_lw, celerity_hg, celerity_hg)

        return (Q, apply_q, q_threshold, time_mi, tstag, T, rsigma, celerity)

    def _batch_get_discharges(
        self,
        reach : ReachLegacy,
        config: configparser.ConfigParser,
        q_stagnant: float,
        celerity_hg: float,
        celerity_lw: float,
        nwidth: float,
    ) -> Tuple[
        bool,
        Optional[float],
        float,
        Tuple[float, float],
        QRuns,
        Tuple[bool, bool, bool],
        float,
        Vector,
        Vector,
    ]:
        """
        Get the simulation discharges in batch mode (no user interaction).

        Arguments
        ---------
        rivers : RiversObject
            A dictionary containing the river data.
        ibranch : int
            Number of selected branch.
        ireach : int
            Number of selected reach.
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

        Results
        -------
        all_q : bool
            Flag indicating whether simulation data for all discharges is available.
        q_threshold : Optional[float]
            River discharge at which the measure becomes active [m3/s].
        q_bankfull : float
            River discharge at which the measure is bankfull [m3/s].
        q_fit : Tuple[float, float]
            A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file) [m3/s].
        Q : QRuns
            Tuple of (at most) three characteristic discharges [m3/s].
        apply_q : Tuple[bool, bool, bool]
            A list of 3 flags indicating whether each value should be used or not.
            The Q1 value can't be set to None because it's needed for char_times.
        tstag : float
            Fraction of year during which flow velocity is considered negligible [-].
        T : Vector
            A vector of values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q [-].
        rsigma : Vector
            A vector of values each representing the relaxation factor for the period given by the corresponding entry in Q [-].
        """
        q_threshold: Optional[float]

        stages = ApplicationSettingsHelper.get_text("stage_descriptions")

        q_fit = reach.qfit
        q_levels = reach.qlevels
        dq = reach.dq

        q_min = reach.qmin
        q_threshold = self._get_q_threshold_from_config(config)
        q_bankfull = self._get_q_bankfull_from_config(config, q_threshold, q_levels)

        Q, apply_q = dfastmi.kernel.core.char_discharges(q_levels, dq, q_threshold, q_bankfull)

        tstag, T, rsigma = dfastmi.kernel.core.char_times(
            q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
        )

        q_list = list(Q)
        for iq in range(3):
            if apply_q[iq]:
                discharge = config.get(f"Q{iq + 1}", "Discharge", fallback="")
                if self._is_float_str(discharge):
                    q_list[iq] = float(discharge)
                else:
                    q_list[iq] = None                
            else:
                q_list[iq] = None
        Q = (q_list[0], q_list[1], q_list[2])

        all_q = True
        return (
            all_q,
            q_threshold,
            q_bankfull,
            q_fit,
            Q,
            apply_q,
            tstag,
            T,
            rsigma,
        )

    def _get_q_bankfull_from_config(self, config, q_threshold, q_levels):
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
        if q_threshold is None or q_threshold < q_levels[1]:
            q_bankfull = config.get("General", "Qbankfull", fallback="")
            if self._is_float_str(q_bankfull):
                q_bankfull = float(q_bankfull)
            else:
                q_bankfull = 0
        else:
            q_bankfull = 0
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

    def _check_configuration_cond_waqua(
            self,
            config: configparser.ConfigParser,
            i : int) -> bool:
        """
        Check validity of one condition of a version 1 analysis configuration using WAQUA results.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.
        i : int
            Flow condition to be checked.            

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        cond = "Q" + str(i+1) 
        # condition block to be checked.
        # condition block must be specified since it must contain the Reference and WithMeasure file names
        if cond not in config.sections():
            return False
        
        # condition block may not be specified since it doesn't contain any required keys
        if config.has_section(cond) and cond in config.sections() and "Discharge" in config[cond]:
            # if discharge is specified, it must be a number
            discharge_value = config.get(cond, "Discharge", fallback="")
            if not self._is_float_str(discharge_value):
                return False
        return True
    
    def _check_configuration_cond_fm(
            self,
            config: configparser.ConfigParser,
            i : int) -> bool:
        """
        Check validity of one condition of a version 1 analysis configuration using D-Flow FM results.

        Arguments
        ---------
        config : configparser.ConfigParser
            Configuration for the D-FAST Morphological Impact analysis.
        i : int
            Flow condition to be checked.            

        Returns
        -------
        success : bool
            Boolean indicating whether the D-FAST MI analysis configuration is valid.
        """
        cond = "Q" + str(i+1) 
        # condition block to be checked.
        # condition block must be specified since it must contain the Reference and WithMeasure file names
        if cond not in config.sections():
            return False

        if "Discharge" in config[cond]:
            # if discharge is specified, it must be a number
            discharge_value = config.get(cond, "Discharge", fallback="")
            if not self._is_float_str(discharge_value):
                return False

        if "Reference" not in config[cond]:
            return False

        if "WithMeasure" not in config[cond]:
            return False

        return True