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


class SedimentationData:
    def __init__(
        self,
        sedarea,
        sedvol,
        sed_area_list,
        eroarea,
        erovol,
        ero_area_list,
        wght_estimate1i,
        wbini,
    ):
        self.sedarea = sedarea
        self.sedvol = sedvol
        self.sed_area_list = sed_area_list
        self.eroarea = eroarea
        self.erovol = erovol
        self.ero_area_list = ero_area_list
        self.wght_estimate1i = wght_estimate1i
        self.wbini = wbini
