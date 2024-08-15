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


from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import netCDF4 as nc
import numpy as np
import numpy.ma as ma

FACE_LOCATION = "face"


class OutputFile(ABC):
    """BaseClass of the 'output' data for the provided dflowfm netcdf output file."""

    def __init__(self, file: Path):
        """Initializes a new instance of the 'FouFile' class for the provided fou file.

        Arguments
        ---------
            fou_file : Path
                The path to the map file.
        """
        self._file = file
        self._mesh2d_name = None
        self._face_dimension_name = None

    @abstractmethod
    def x_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the x-velocity at faces.

        Arguments
        ---------
        discharges : Vector
            A vector of discharges (Q) included in hydrograph [m3/s].

        Return
        ------
        celerity : Vector
            A vector of values each representing the bed celerity for the
            period given by the corresponding entry in Q [m/s].
        """
        pass

    @abstractmethod
    def y_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the y-velocity at faces.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.
        """
        pass

    @abstractmethod
    def water_depth(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the y-velocity at faces.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.
        """
        pass

    @property
    def node_x_coordinates(self) -> np.ndarray:
        """Get the x-coordinates of the nodes.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of nodes.
        """
        return self._get_node_coordinate_data(["projection_x_coordinate", "longitude"])

    @property
    def node_y_coordinates(self) -> np.ndarray:
        """Get the y-coordinates of the nodes.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of nodes.
        """
        return self._get_node_coordinate_data(["projection_y_coordinate", "latitude"])

    @property
    def face_node_connectivity(self) -> ma.masked_array:
        """Get the face-node connectivity from the 2d mesh.

        Returns
        -------
        ma.masked_array
            Array with shape (N,M) where N is the number of faces and M the maximum number of nodes per face.
            If not all the faces have the same number of nodes, a boolean mask is provided with shape (N,M)
            where each True value indicates a fill value.
        """
        with nc.Dataset(self._file) as dataset:
            mesh2d = dataset.variables[self.mesh2d_name]
            var_name = mesh2d.getncattr("face_node_connectivity")
            var = dataset.variables[var_name]
            data = var[...] - self._get_start_index(var)

        return data
    
    def _get_node_coordinate_data(self, standard_names: List[str]) -> np.ndarray:
        with nc.Dataset(self._file) as dataset:
            mesh2d = dataset.variables[self.mesh2d_name]

            coord_var_names = mesh2d.getncattr("node_coordinates").split()
            for coord_var_name in coord_var_names:
                standard_name = dataset.variables[coord_var_name].standard_name
                if standard_name in standard_names:
                    var = dataset.variables[coord_var_name]
                    break

            data = var[...]

        return data

    def read_face_variable(
        self,
        varname: str,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """
        Read the last time step of any quantity defined at faces from a D-Flow FM map-file.

        Arguments
        ---------
        varname : str
            Name of the netCDF variable to be read.
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.

        Raises
        ------
        ValueError
            If the data file doesn't include a 2D mesh.
            If it cannot uniquely identify the variable to be read.

        Returns
        -------
        numpy.ndarray
            1D data of the requested variable. If the variable is time-dependent,
            the time_index_from_last is used.
        """
        with nc.Dataset(self._file) as dataset:
            var = self._get_face_var_by_name(varname, dataset)
            data = self._get_var_data(var, time_index_from_last)

        return data

    def _get_var_data(self, var: nc.Variable, time_index_from_last: Optional[int]):
        if var.get_dims()[0].isunlimited():
            # assume that time dimension is unlimited and is the first dimension
            # slice to obtain last time step or earlier as requested
            if time_index_from_last is None:
                time_index_from_last = 0
            return var[-1 - time_index_from_last, :]

        if time_index_from_last is not None:
            raise ValueError(
                'Trying to access time-independent variable "{}" with time offset {}.'.format(
                    var.name, -1 - time_index_from_last
                )
            )

        return var[...]

    def _get_face_var_by_name(self, varname: str, dataset: nc.Dataset) -> nc.Variable:
        variables = self._get_face_vars_by_standard_name(dataset, varname)
        if len(variables) == 0:
            variables = self._get_face_vars_by_long_name(dataset, varname)
        if len(variables) != 1:
            raise ValueError(
                'Expected one variable for "{}", but obtained {}.'.format(
                    varname, len(variables)
                )
            )
        return variables[0]

    def _get_face_vars_by_standard_name(
        self, dataset: nc.Dataset, standard_name: str
    ) -> List[nc.Variable]:
        return dataset.get_variables_by_attributes(
            standard_name=standard_name, mesh=self.mesh2d_name, location=FACE_LOCATION
        )

    def _get_face_vars_by_long_name(
        self, dataset: nc.Dataset, long_name: str
    ) -> List[nc.Variable]:
        return dataset.get_variables_by_attributes(
            long_name=long_name, mesh=self.mesh2d_name, location=FACE_LOCATION
        )

    @property
    def mesh2d_name(self) -> str:
        """Get the name of the mesh2d variable.

        Returns
        -------
        str
            String containing the name of the mesh2d variable.
        """
        if not self._mesh2d_name:
            with nc.Dataset(self._file) as dataset:
                mesh2d = self._get_mesh2d_variable(dataset)
                self._mesh2d_name = mesh2d.name

        return self._mesh2d_name

    def _get_mesh2d_variable(self, dataset: nc.Dataset) -> nc.Variable:
        mesh2d = dataset.get_variables_by_attributes(
            cf_role="mesh_topology", topology_dimension=2
        )
        if len(mesh2d) != 1:
            raise ValueError(
                "Currently only one 2D mesh supported ... this file contains {} 2D meshes.".format(
                    len(mesh2d)
                )
            )

        return mesh2d[0]
