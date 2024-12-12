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
Module for Reach implementation

Classes:
    Reach
"""
from typing import List, Tuple

from pydantic import model_validator

from dfastmi.io.AReach import AReach
from dfastmi.io.CelerObject import ICelerObject


class Reach(AReach):
    """
    Derived class with reach data information used with current (AKA v2) river configuration files.
    """

    hydro_q: List[float] = []
    hydro_t: List[float] = []
    auto_time: bool = False
    qfit: Tuple[float, float] = (0.0, 0.0)

    use_tide: bool = False
    tide_boundary_condition: Tuple[str, ...] = ()
    conditions: Tuple[str, ...] = ()

    celer_form: int = 0
    _celer_object: ICelerObject = None

    @property
    def celer_object(self):
        return self._celer_object

    @celer_object.setter
    def celer_object(self, value: ICelerObject):
        self._celer_object = value
        self._celer_object.parent_reach = self

    @model_validator(mode="after")
    def validate(self) -> "Reach":
        if not self.parent_branch:
            return self

        self._verify_consistency_hydro_q_and_hydro_t()

        self._verify_consistency_hydro_q_and_tide_bc()

        if self.celer_object:
            self.celer_object.model_validate(self.celer_object)

        if self.celer_form not in (1, 2):
            raise ValueError(
                f'Invalid value {self.celer_form} specified for "CelerForm" '
                f'for branch "{self.parent_branch.name}", reach "{self.name}";'
                f" only 1 and 2 are supported."
            )
        return self

    def _verify_consistency_hydro_q_and_tide_bc(self):
        """
        Verify consistent length of hydro discharge and tide boundary condition values for this branch on this reach.
        """
        if self.use_tide:
            hydro_q_length = len(self.hydro_q)
            tide_boundary_condition_length = len(self.tide_boundary_condition)
            if hydro_q_length != tide_boundary_condition_length:
                raise LookupError(
                    f'Length of "HydroQ" and "TideBC" for branch "{self.parent_branch.name}", '
                    f'reach "{self.name}" are not consistent: '
                    f"{hydro_q_length} and {tide_boundary_condition_length} "
                    f"values read respectively."
                )

    def _verify_consistency_hydro_q_and_hydro_t(self):
        """
        Verify consistent length of hydro_q and hydro_t for this branch on this reach.
        """
        if self.auto_time:
            self._check_qfit_on_branch_on_reach_with_auto_time()
        else:
            hydro_q_length = len(self.hydro_q)
            hydro_t_length = len(self.hydro_t)
            if hydro_q_length != hydro_t_length:
                raise LookupError(
                    f'Length of "HydroQ" and "HydroT" for branch "{self.parent_branch.name}", '
                    f'reach "{self.name}" are not consistent: '
                    f"{hydro_q_length} and {hydro_t_length} "
                    f"values read respectively."
                )

    def _check_qfit_on_branch_on_reach_with_auto_time(self):
        if self.qfit == (0.0, 0.0):
            raise ValueError(
                f'The parameter "QFit" must be specified for branch "{self.parent_branch.name}", '
                f'reach "{self.name}" since "AutoTime" is set to True.'
            )
