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

from pathlib import Path
from typing import List

import numpy


class XyzFileWriter:
    """
    Class used to write data to a xyz file.
    """

    @staticmethod
    def write_xyz_file(
        wbin_labels: list[str],
        kmid: numpy.ndarray,
        binvol: List[numpy.ndarray],
        xyz_file_location: Path,
    ) -> None:
        """
        Writes the given data to the given file location.

        Arguments
        ---------
        wbin_labels: list[str]
            Array of length N containing the index of the target width bin [-].
        kmid: numpy.ndarray
            Array of length N containing the location of points expressed as chainage.
        binvol : List[numpy.ndarray]
            List of arrays containing the total volume per streamwise bin [m3]. List length corresponds to number of width bins.
        xyz_file_location : Path
            Location to write the xyz file to.
        """
        if xyz_file_location:
            # write a table of chainage and volume per width bin to file
            binvol2 = numpy.stack(binvol)
            with open(xyz_file_location, "w") as file:
                vol_str = " ".join('"{}"'.format(str) for str in wbin_labels)
                file.write('"chainage" ' + vol_str + "\n")
                for i in range(binvol2.shape[1]):
                    vol_str = " ".join("{:8.2f}".format(j) for j in binvol2[:, i])
                    file.write("{:8.2f} ".format(kmid[i]) + vol_str + "\n")
