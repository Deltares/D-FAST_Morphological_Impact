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
from typing import Optional, Tuple
import os
import numpy
import netCDF4

class GridOperations:
    @staticmethod
    def read_fm_map(
        filename: str,
        varname: str,
        location: str = "face",
        ifld: Optional[int] = None,
    ) -> numpy.ndarray:
        """
        Read the last time step of any quantity defined at faces from a D-Flow FM map-file.

        Arguments
        ---------
        filename : str
            Name of the D-Flow FM map.nc file to read the data.
        varname : str
            Name of the netCDF variable to be read.
        location : str
            Name of the stagger location at which the data should be located
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
        rootgrp = netCDF4.Dataset(filename)

        # locate 2d mesh variable
        mesh2d = rootgrp.get_variables_by_attributes(
            cf_role="mesh_topology", topology_dimension=2
        )
        if len(mesh2d) != 1:
            raise Exception(
                "Currently only one 2D mesh supported ... this file contains {} 2D meshes.".format(
                    len(mesh2d)
                )
            )
        meshname = mesh2d[0].name

        # define a default start_index
        start_index = 0

        # locate the requested variable ... start with some special cases
        if varname == "x":
            # the x-coordinate or longitude
            crdnames = mesh2d[0].getncattr(location + "_coordinates").split()
            for n in crdnames:
                stdname = rootgrp.variables[n].standard_name
                if stdname == "projection_x_coordinate" or stdname == "longitude":
                    var = rootgrp.variables[n]
                    break

        elif varname == "y":
            # the y-coordinate or latitude
            crdnames = mesh2d[0].getncattr(location + "_coordinates").split()
            for n in crdnames:
                stdname = rootgrp.variables[n].standard_name
                if stdname == "projection_y_coordinate" or stdname == "latitude":
                    var = rootgrp.variables[n]
                    break

        elif varname[-12:] == "connectivity":
            # a mesh connectivity variable with corrected index
            varname = mesh2d[0].getncattr(varname)
            var = rootgrp.variables[varname]
            if "start_index" in var.ncattrs():
                start_index = var.getncattr("start_index")

        else:
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

        # read data checking for time dimension
        dims = var.dimensions
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

            data = var[...] - start_index

        # close file
        rootgrp.close()

        # return data
        return data

    @staticmethod
    def get_mesh_and_facedim_names(filename: str) -> Tuple[str, str]:
        """
        Obtain the names of 2D mesh and face dimension from netCDF UGRID file.

        Arguments
        ---------
        filename : str
            Name of the netCDF file.

        Raises
        ------
        Exception
            If there is not one mesh in the netCDF file.

        Returns
        -------
        tuple : Tuple[str, str]
            Name of the 2D mesh variable
            Name of the face dimension of that 2D mesh
        """
        # open file
        rootgrp = netCDF4.Dataset(filename)

        # locate 2d mesh variable
        mesh2d = rootgrp.get_variables_by_attributes(
            cf_role="mesh_topology", topology_dimension=2
        )
        if len(mesh2d) != 1:
            raise Exception(
                "Currently only one 2D mesh supported ... this file contains {} 2D meshes.".format(
                    len(mesh2d)
                )
            )

        #
        facenodeconnect_varname = mesh2d[0].face_node_connectivity
        fnc = rootgrp.get_variables_by_attributes(name=facenodeconnect_varname)[0]

        # default
        facedim = fnc.dimensions[0]
        mesh2d_name = mesh2d[0].name

        rootgrp.close()        
        return mesh2d_name, facedim

    @staticmethod
    def copy_var(src: netCDF4.Dataset, varname: str, dst: netCDF4.Dataset) -> None:
        """
        Copy a single variable from one netCDF file to another.

        Copy a single netCDF variable including all attributes from source file to
        destination file. Create dimensions as necessary.

        Arguments
        ---------
        src : netCDF4.Dataset
            Dataset object representing the source file.
        varname : str
            Name of the netCDF variable to be copied from source to destination.
        dst : netCDF4.Dataset
            Dataset object representing the destination file.
        """
        # locate the variable to be copied
        srcvar = src.variables[varname]

        # copy dimensions
        for name in srcvar.dimensions:
            dimension = src.dimensions[name]
            if name not in dst.dimensions.keys():
                dst.createDimension(
                    name, (len(dimension) if not dimension.isunlimited() else None)
                )

        # copy variable
        dstvar = dst.createVariable(varname, srcvar.datatype, srcvar.dimensions)

        # copy variable attributes all at once via dictionary
        dstvar.setncatts(srcvar.__dict__)
        dstvar[:] = srcvar[:]

    @staticmethod
    def copy_ugrid(srcname: str, meshname: str, dstname: str) -> None:
        """
        Copy UGRID mesh data from one netCDF file to another.

        Copy UGRID mesh data (mesh variable, all attributes, all variables that the
        UGRID attributes depend on) from source file to destination file.

        Arguments
        ---------
        srcname : str
            Name of source file.
        meshname : str
            Name of the UGRID mesh to be copied from source to destination.
        dstname : str
            Name of destination file, or dataset object representing the destination
            file.
        """
        # open source and destination files
        src = netCDF4.Dataset(srcname)
        if os.path.exists(dstname):
            os.remove(dstname)
        dst = netCDF4.Dataset(dstname, "w", format="NETCDF4")

        # locate source mesh
        mesh = src.variables[meshname]

        # copy mesh variable
        GridOperations.copy_var(src, meshname, dst)
        atts = [
            "face_node_connectivity",
            "edge_node_connectivity",
            "edge_face_connectivity",
            "face_coordinates",
            "edge_coordinates",
            "node_coordinates",
        ]
        for att in atts:
            try:
                varlist = mesh.getncattr(att).split()
            except:
                varlist = []
            for varname in varlist:
                GridOperations.copy_var(src, varname, dst)

                # check if variable has bounds attribute, if so copy those as well
                var = src.variables[varname]
                atts2 = ["bounds"]
                for att2 in atts2:
                    try:
                        varlist2 = var.getncattr(att2).split()
                    except:
                        varlist2 = []
                    for varname2 in varlist2:
                        GridOperations.copy_var(src, varname2, dst)

        # close files
        src.close()
        dst.close()

    @staticmethod
    def ugrid_add(
        dstfile: str,
        varname: str,
        ldata: numpy.array,
        meshname: str,
        facedim: str,
        long_name: str = "None",
        units: str = "None",
    ) -> None:
        """
        Add a new variable defined at faces to an existing UGRID netCDF file

        Arguments
        ---------
        dstfile : str
            Name of netCDF file to write data to.
        varname : str
            Name of netCDF variable to be written.
        ldata : numpy.array
            Linear array containing the data to be written.
        meshname : str
            Name of mesh variable in the netCDF file.
        facedim : str
            Name of the face dimension of the selected mesh.
        long_name : str
            Long descriptive name for the variable ("None" if no long name attribute
            should be written).
        units : str
            String indicating the unit ("None" if no unit attribute should be written).
        """
        # open destination file
        dst = netCDF4.Dataset(dstfile, "a")

        # check if face dimension exists
        dim = dst.dimensions[facedim]

        # add variable and write data
        var = dst.createVariable(varname, "f8", (facedim,))
        var.mesh = meshname
        var.location = "face"
        if long_name != "None":
            var.long_name = long_name
        if units != "None":
            var.units = units
        var[:] = ldata[:]

        # close destination file
        dst.close()
