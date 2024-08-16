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
from typing import List, Optional

import netCDF4 as nc
import numpy as np

from dfastmi.io.OutputFile import OutputFile


class MapFile(OutputFile):
    """D-HYDRO FM Map 'output' data for the provided dflowfm netcdf output file."""

    def __init__(self, map_file: Path):
        # Call the base class constructor using super()
        super().__init__(map_file)
        self._face_dimension_name = None

    def x_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the x-velocity at faces.
        Arguments
        ---------
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        """
        u0 = self.read_face_variable(
            "sea_water_x_velocity", time_index_from_last=time_index_from_last
        )
        return u0

    def y_velocity(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the y-velocity at faces.

        Arguments
        ---------
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        """
        v0 = self.read_face_variable(
            "sea_water_y_velocity", time_index_from_last=time_index_from_last
        )
        return v0

    def water_depth(
        self,
        time_index_from_last: Optional[int] = None,
    ) -> np.ndarray:
        """Get the y-velocity at faces.
        Arguments
        ---------
        time_index_from_last : Optional[int]
            Time step offset index from the last time step written.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of faces.
        """
        h0 = self.read_face_variable(
            "sea_floor_depth_below_sea_surface",
            time_index_from_last=time_index_from_last,
        )
        return h0

    @property
    def face_dimension_name(self) -> str:
        """Get the name of the face dimension.

        Returns
        -------
        str
            String containing the name of the face dimension.
        """
        if not self._face_dimension_name:
            with nc.Dataset(self._file) as dataset:
                mesh2d = dataset.variables[self.mesh2d_name]
                facenodeconnect_varname = mesh2d.face_node_connectivity
                fnc = dataset.get_variables_by_attributes(name=facenodeconnect_varname)[
                    0
                ]
                self._face_dimension_name = fnc.dimensions[0]

        return self._face_dimension_name

    def _copy_var(
        self, source_dataset: nc.Dataset, var_name: str, target_dataset: nc.Dataset
    ) -> None:
        """
        Copy a single variable from one netCDF file to another.

        Copy a single netCDF variable including all attributes from source file to
        destination file. Create dimensions as necessary.

        Arguments
        ---------
        source_dataset : netCDF4.Dataset
            Dataset object representing the source file.
        var_name : str
            Name of the netCDF variable to be copied from source to destination.
        target_dataset : netCDF4.Dataset
            Dataset object representing the destination file.
        """
        variable = source_dataset.variables[var_name]
        self._copy_var_dimensions(variable, source_dataset, target_dataset)
        self._copy_var_data(variable, target_dataset)

    def _copy_var_dimensions(
        self,
        variable: nc.Variable,
        source_dataset: nc.Dataset,
        target_dataset: nc.Dataset,
    ):
        for dim_name in variable.dimensions:
            dimension = source_dataset.dimensions[dim_name]
            if dim_name not in target_dataset.dimensions.keys():
                target_dataset.createDimension(
                    dim_name, (len(dimension) if not dimension.isunlimited() else None)
                )

    def _copy_var_data(self, variable: nc.Variable, target_dataset: nc.Dataset):
        variable_copy = target_dataset.createVariable(
            variable.name, variable.datatype, variable.dimensions
        )
        variable_copy.setncatts(variable.__dict__)
        variable_copy[:] = variable[:]

    def copy_ugrid(self, target_file: Path) -> None:
        """
        Copy UGRID mesh data from one netCDF file to another.

        Copy UGRID mesh data (mesh variable, all attributes, all variables that the
        UGRID attributes depend on) from source file to destination file.

        Arguments
        ---------
        target_file : Path
            Path to the target file.
        """
        target_file.unlink(missing_ok=True)

        with nc.Dataset(self._file) as source_dataset:
            with nc.Dataset(target_file, "w", format="NETCDF4") as target_dataset:

                mesh_variable = source_dataset.variables[self.mesh2d_name]

                self._copy_var(source_dataset, self.mesh2d_name, target_dataset)

                mesh_attrs = [
                    "face_node_connectivity",
                    "edge_node_connectivity",
                    "edge_face_connectivity",
                    "face_coordinates",
                    "edge_coordinates",
                    "node_coordinates",
                ]
                for mesh_attr in mesh_attrs:
                    self._copy_mesh_attr_variable(
                        mesh_variable, mesh_attr, source_dataset, target_dataset
                    )

    def _copy_mesh_attr_variable(
        self, mesh_variable, mesh_attr, source_dataset, target_dataset
    ):
        var_names = self._get_var_names_from_var_attribute(mesh_variable, mesh_attr)
        for var_name in var_names:
            self._copy_var(source_dataset, var_name, target_dataset)

            # check if variable has bounds attribute, if so copy those as well
            variable = source_dataset.variables[var_name]

            bounds_attr = "bounds"
            bounds_var_names = self._get_var_names_from_var_attribute(
                variable, bounds_attr
            )
            for bounds_var_name in bounds_var_names:
                self._copy_var(source_dataset, bounds_var_name, target_dataset)

    def _get_var_names_from_var_attribute(
        self, variable: nc.Variable, attr_name: str
    ) -> List[str]:
        try:
            var_names = variable.getncattr(attr_name).split()
        except AttributeError:
            var_names = []

        return var_names

    def add_variable(
        self,
        variable_name: str,
        data: np.array,
        mesh_name: str,
        face_dimension_name: str,
        long_name: str,
        unit: str,
    ) -> None:
        """
        Add a new variable defined at faces to an existing UGRID netCDF file

        Arguments
        ---------
        variable_name : str
            Name of netCDF variable to be written.
        data : numpy.array
            Linear array containing the data to be written.
        mesh_name : str
            Name of mesh variable in the netCDF file.
        face_dimension_name : str
            Name of the face dimension of the selected mesh.
        long_name : str
            Long descriptive name for the variable ("None" if no long name attribute
            should be written).
        unit : str
            String indicating the unit ("None" if no unit attribute should be written).
        """
        with nc.Dataset(self._file, "a") as dst:

            var = dst.createVariable(variable_name, "f8", (face_dimension_name,))

            var.mesh = mesh_name
            var.location = "face"
            var.long_name = long_name
            var.units = unit
            var[:] = data[:]
