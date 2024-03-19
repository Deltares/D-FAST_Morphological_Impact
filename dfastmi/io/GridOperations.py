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
from pathlib import Path
from typing import List, Optional
import numpy
import numpy.ma as ma
import netCDF4 as nc
    
class GridOperations:
    def __init__(self, map_file: Path):
        """Initializes a new instance of the 'GridOperations' class for the provided map file.

        Arguments
        ---------
            map_file : Path
                The path to the map file.
        """
        self._map_file = map_file
        self._mesh2d_name = None
        self._face_dimension_name = None
    
    @property
    def node_x_coordinates(self) -> numpy.ndarray:
        """Get the x-coordinates of the nodes.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of nodes.
        """
        return self._get_node_coordinate_data(["projection_x_coordinate", "longitude"])
    
    @property
    def node_y_coordinates(self) -> numpy.ndarray:
        """Get the y-coordinates of the nodes.

        Returns
        -------
        numpy.ndarray
            Array with shape (N,) where N is the number of nodes.
        """
        return self._get_node_coordinate_data(["projection_y_coordinate", "latitude"])
    
    @property
    def face_node_connectivity(self)-> ma.masked_array:
        """Get the face-node connectivity from the 2d mesh.

        Returns
        -------
        ma.masked_array
            Array with shape (N,M) where N is the number of faces and M the maximum number of nodes per face.
            If not all the faces have the same number of nodes, a boolean mask is provided with shape (N,M) 
            where each True value indicates a fill value.
        """
        with nc.Dataset(self._map_file) as rootgrp:
            mesh2d = self._get_mesh2d_variable(rootgrp)

            start_index = 0
            varname = mesh2d.getncattr("face_node_connectivity")
            var = rootgrp.variables[varname]
            if "start_index" in var.ncattrs():
                start_index = var.getncattr("start_index")

            data = var[...] - start_index

        return data
    
    def read_face_variable(self, 
                      varname: str, 
                      ifld: Optional[int] = None,
    ) -> numpy.ndarray:
        """
        Read the last time step of any quantity defined at faces from a D-Flow FM map-file.

        Arguments
        ---------
        varname : str
            Name of the netCDF variable to be read.
        location : Location
            The stagger location at which the data should be located
            (default is "face")
        ifld : Optional[int]
            Time step offset index from the last time step written.

        Raises
        ------
        Exception
            If the data file doesn't include a 2D mesh.
            If it cannot uniquely identify the variable to be read.

        Returns
        -------
        data
            Data of the requested variable (for the last time step only if the variable is
            time dependent).
        """
        # open file
        with nc.Dataset(self._map_file) as rootgrp:
            location = "face"

            # locate 2d mesh variable
            mesh2d = self._get_mesh2d_variable(rootgrp)
            meshname = mesh2d.name

            # find any other variable by standard_name or long_name
            var = rootgrp.get_variables_by_attributes(
                standard_name=varname, mesh=meshname, location=location
            )
            if len(var) == 0:
                var = rootgrp.get_variables_by_attributes(
                    long_name=varname, mesh=meshname, location=location
                )
            if len(var) != 1:
                raise Exception(
                    'Expected one variable for "{}", but obtained {}.'.format(
                        varname, len(var)
                    )
                )
            var = var[0]

            if var.get_dims()[0].isunlimited():
                # assume that time dimension is unlimited and is the first dimension
                # slice to obtain last time step or earlier as requested
                if ifld is None:
                    data = var[-1, :]
                else:
                    data = var[-1 - ifld, :]
            else:
                if not ifld is None:
                    raise Exception(
                        'Trying to access time-independent variable "{}" with time offset {}.'.format(
                            varname, -1 - ifld
                        )
                    )

                data = var[...]



        # return data
        return data

    @property
    def mesh2d_name(self) -> str:
        """Get the name of the mesh2d variable.

        Returns
        -------
        str
            String containing the name of the mesh2d variable.
        """
        if not self._mesh2d_name:
            with nc.Dataset(self._map_file) as rootgrp:
                mesh2d = GridOperations._get_mesh2d_variable(rootgrp)
                self._mesh2d_name = mesh2d.name    
 
        return self._mesh2d_name

    @property
    def face_dimension_name(self) -> str:
        """Get the name of the face dimension.

        Returns
        -------
        str
            String containing the name of the face dimension.
        """
        if not self._face_dimension_name:
            with nc.Dataset(self._map_file) as rootgrp:
                mesh2d = GridOperations._get_mesh2d_variable(rootgrp)
                facenodeconnect_varname = mesh2d.face_node_connectivity
                fnc = rootgrp.get_variables_by_attributes(name=facenodeconnect_varname)[0]
                self._face_dimension_name = fnc.dimensions[0]
            
        return self._face_dimension_name
    
    @staticmethod
    def _get_mesh2d_variable(dataset: nc.Dataset) -> nc.Variable:
        # locate 2d mesh variable
        mesh2d = dataset.get_variables_by_attributes(
            cf_role="mesh_topology", topology_dimension=2
        )
        if len(mesh2d) != 1:
            raise Exception(
                "Currently only one 2D mesh supported ... this file contains {} 2D meshes.".format(
                    len(mesh2d)
                )
            )
        
        return mesh2d[0]


    @staticmethod
    def _copy_var(source_dataset: nc.Dataset, var_name: str, target_dataset: nc.Dataset) -> None:
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
        # locate the variable to be copied
        variable = source_dataset.variables[var_name]

        # copy dimensions
        for dim_name in variable.dimensions:
            dimension = source_dataset.dimensions[dim_name]
            if dim_name not in target_dataset.dimensions.keys():
                target_dataset.createDimension(
                    dim_name, (len(dimension) if not dimension.isunlimited() else None)
                )

        # copy variable
        variable_copy = target_dataset.createVariable(var_name, variable.datatype, variable.dimensions)

        # copy variable attributes all at once via dictionary
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
        
        with nc.Dataset(self._map_file) as source_dataset:
            with nc.Dataset(target_file, "w", format="NETCDF4") as target_dataset:

                mesh_variable = source_dataset.variables[self.mesh2d_name]

                GridOperations._copy_var(source_dataset, self.mesh2d_name, target_dataset)
                
                mesh_attrs = [
                    "face_node_connectivity",
                    "edge_node_connectivity",
                    "edge_face_connectivity",
                    "face_coordinates",
                    "edge_coordinates",
                    "node_coordinates",
                ]
                for mesh_attr in mesh_attrs:
                    var_names = GridOperations._get_var_names_from_var_attribute(mesh_variable, mesh_attr)
                    for var_name in var_names:
                        GridOperations._copy_var(source_dataset, var_name, target_dataset)

                        # check if variable has bounds attribute, if so copy those as well
                        variable = source_dataset.variables[var_name]

                        bounds_attr = "bounds"
                        bounds_var_names = GridOperations._get_var_names_from_var_attribute(variable, bounds_attr)
                        for bounds_var_name in bounds_var_names:
                            GridOperations._copy_var(source_dataset, bounds_var_name, target_dataset)

    @staticmethod
    def _get_var_names_from_var_attribute(variable: nc.Variable, attr_name: str) -> List[str]:
        try:
            var_names = variable.getncattr(attr_name).split()
        except:
            var_names = []
            
        return var_names
        
    def add_variable(
        self,
        variable_name: str,
        data: numpy.array,
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
        with nc.Dataset(self._map_file, "a") as dst:

            var = dst.createVariable(variable_name, "f8", (face_dimension_name,))

            var.mesh = mesh_name
            var.location = "face"
            var.long_name = long_name
            var.units = unit
            var[:] = data[:]

        
    def _get_node_coordinate_data(self, standard_names: List[str]) -> numpy.ndarray:
        # open file
        with nc.Dataset(self._map_file) as rootgrp:
            mesh2d = self._get_mesh2d_variable(rootgrp)
    
            crdnames = mesh2d.getncattr("node_coordinates").split()
            for n in crdnames:
                stdname = rootgrp.variables[n].standard_name
                if stdname in standard_names:
                    var = rootgrp.variables[n]
                    break
                
            data = var[...]

        return data