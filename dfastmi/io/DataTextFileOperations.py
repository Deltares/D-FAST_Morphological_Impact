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

from typing import Tuple

import fiona
import numpy
import shapely
import shapely.geometry
from dfastio.xyc.models import XYCModel

fiona.supported_drivers["kml"] = "rw"  # enable KML support which is disabled by default
fiona.supported_drivers["KML"] = "rw"  # enable KML support which is disabled by default
fiona.supported_drivers["libkml"] = (
    "rw"  # enable KML support which is disabled by default
)
fiona.supported_drivers["LIBKML"] = (
    "rw"  # enable KML support which is disabled by default
)


class DataTextFileOperations:
    @staticmethod
    def read_waqua_xyz(filename: str, cols: Tuple[int, ...] = (2,)) -> numpy.ndarray:
        """
        Read data columns from a SIMONA XYZ file.

        Arguments
        ---------
        filename : str
            Name of file to be read.
        cols : Tuple[int]
            List of column numbers for which to return the data.

        Returns
        -------
        data : numpy.ndarray
            Data read from the file.
        """
        data = numpy.genfromtxt(filename, delimiter=",", skip_header=1, usecols=cols)
        return data

    @staticmethod
    def write_simona_box(
        filename: str, rdata: numpy.ndarray, firstm: int, firstn: int
    ) -> None:
        """
        Write a SIMONA BOX file.

        Arguments
        ---------
        filename : str
            Name of the file to be written.
        rdata : numpy.ndarray
            Two-dimensional NumPy array containing the data to be written.
        firstm : int
            Firt M index to be written.
        firstn : int
            First N index to be written.
        """
        # open the data file
        boxfile = open(filename, "w")

        # get shape and prepare block header; data will be written in blocks of 10
        # N-lines
        shp = numpy.shape(rdata)
        mmax = shp[0]
        nmax = shp[1]
        boxheader = "      BOX MNMN=({m1:4d},{n1:5d},{m2:5d},{n2:5d}), VARIABLE_VAL=\n"
        nstep = 10

        # Loop over all N-blocks and write data to file
        for j in range(firstn, nmax, nstep):
            k = min(nmax, j + nstep)
            boxfile.write(boxheader.format(m1=firstm + 1, n1=j + 1, m2=mmax, n2=k))
            nvalues = (mmax - firstm) * (k - j)
            boxdata = ("   " + "{:12.3f}" * (k - j) + "\n") * (mmax - firstm)
            values = tuple(rdata[firstm:mmax, j:k].reshape(nvalues))
            boxfile.write(boxdata.format(*values))

        # close the file
        boxfile.close()

    @staticmethod
    def get_xykm(
        kmfile: str,
    ) -> shapely.geometry.linestring.LineString:
        """

        Arguments
        ---------
        kmfile : str
            Name of chainage file.

        Returns
        -------
        xykm : shapely.geometry.linestring.LineString

        """
        # get the chainage file
        xykm = XYCModel.read(kmfile, num_columns=3)

        # make sure that chainage is increasing with node index
        if xykm.coords[0][2] > xykm.coords[1][2]:
            xykm = shapely.geometry.asLineString(xykm.coords[::-1])

        return xykm
