# -*- coding: utf-8 -*-
"""
Copyright (C) 2020 Stichting Deltares.

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

from typing import Tuple, Any, List, Union, Dict, Optional, TypedDict, TextIO
import fiona
fiona.supported_drivers['kml'] = 'rw' # enable KML support which is disabled by default
fiona.supported_drivers['KML'] = 'rw' # enable KML support which is disabled by default

import numpy
import netCDF4
import configparser
import os
import pathlib
import pandas
import geopandas
import shapely

DataField = List[List[Union[float, List[float]]]]

PROGTEXTS: Dict[str, List[str]]


def load_program_texts(filename: str) -> None:
    """
    Load texts from configuration file, and store globally for access.

    This routine reads the text file "filename", and detects the keywords
    indicated by lines starting with [ and ending with ]. The content is
    placed in a global dictionary PROGTEXTS which may be queried using the
    routine "get_text". These routines are used to implement multi-
    language support.

    Parameters
    ----------
    filename : str
        The name of the file to be read and parsed.
    """
    text: List[str]
    dict: Dict[str, List[str]]

    global PROGTEXTS

    all_lines = open(filename, "r").read().splitlines()
    dict = {}
    text = []
    key = None
    for line in all_lines:
        rline = line.strip()
        if rline.startswith("[") and rline.endswith("]"):
            if not key is None:
                dict[key] = text
            key = rline[1:-1]
            text = []
        else:
            text.append(line)
    if key in dict.keys():
        raise Exception('Duplicate entry for "{}" in "{}".'.format(key, filename))
    if not key is None:
        dict[key] = text
    PROGTEXTS = dict


def log_text(
    key: str,
    file: Optional[TextIO] = None,
    dict: Dict[str, Any] = {},
    repeat: int = 1,
) -> None:
    """
    Write a text to standard out or file.

    Arguments
    ---------
    key : str
        The key for the text to show to the user.
    file : Optional[TextIO]
        The file to write to (None for writing to standard out).
    dict : Dict[str, Any]
        A dictionary used for placeholder expansions (default empty).
    repeat : int
        The number of times that the same text should be repeated (default 1).

    Returns
    -------
    None
    """
    the_text = get_text(key)
    for r in range(repeat):
        for line in the_text:
            expanded_line = line.format(**dict)
            if file is None:
                print(expanded_line)
            else:
                file.write(expanded_line + "\n")


def get_filename(key: str) -> str:
    """
    Query the global dictionary of texts for a file name.

    The file name entries in the global dictionary have a prefix "filename_"
    which will be added to the key by this routine.

    Arguments
    ---------
    key : str
        The key string used to query the dictionary.

    Results
    -------
    filename : str
        File name.
    """
    filename = get_text("filename_" + key)[0]
    return filename


def get_text(key: str) -> List[str]:
    """
    Query the global dictionary of texts via a string key.

    Query the global dictionary PROGTEXTS by means of a string key and return
    the list of strings contained in the dictionary. If the dictionary doesn't
    include the key, a default string is returned.

    Parameters
    ----------
    key : str
        The key string used to query the dictionary.

    Returns
    -------
    text : List[str]
        The list of strings returned contain the text stored in the dictionary
        for the key. If the key isn't available in the dictionary, the routine
        returns the default string "No message found for <key>"
    """

    global PROGTEXTS

    try:
        str = PROGTEXTS[key]
    except:
        str = ["No message found for " + key]
    return str


def collect_int_values1(
    config: configparser.ConfigParser,
    branches: List[str],
    nreaches: List[int],
    key: str,
    default: Optional[int] = None,
) -> List[List[int]]:
    """
    Collect river parameter data from river configuration object.

    This routines collects entries of type integer.

    Arguments
    ---------
    config : configparser.ConfigParser
        The dictionary containing river data.
    branches : List[str]
        The list of river branches. The length of this list is nBranches.
    nreaches : List[int]
        The number of reaches per river branch. The length of this list is nBranches.
    key : str
        The name of the parameter for which the values are to be retrieved.

    Raises
    ------
    Exception
        If the number of values read from the file doesn't match 1.

    Returns
    -------
    data : List[List[int]]
        A list of lists. Each list contains per reach within the corresponding
        branch one integer.
    """
    try:
        g_val = config["General"][key]
    except:
        g_val = ""

    all_values = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val

        values_per_branch = []
        for i in range(nreaches[ib]):
            stri = str(i + 1)
            try:
                val = config[branch][key + stri]
            except:
                val = b_val
            if val == "" and default is not None:
                ival = default
            else:
                try:
                    vals = tuple(int(x) for x in val.split())
                except:
                    vals = ()
                if len(vals) != 1:
                    raise Exception(
                        'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                            key, i+1, branches[ib], val, 1
                        )
                    )
                ival = vals[0]
            values_per_branch.append(ival)

        all_values.append(values_per_branch)

    return all_values
    

def collect_values_logical(
    config: configparser.ConfigParser,
    branches: List[str],
    nreaches: List[int],
    key: str,
    default: Optional[bool] = None,
) -> List[List[bool]]:
    """
    Collect river parameter data from river configuration object.

    This routines collects entries of type float.

    Arguments
    ---------
    config : configparser.ConfigParser
        The dictionary containing river data.
    branches : List[str]
        The list of river branches. The length of this list is nBranches.
    nreaches : List[int]
        The number of reaches per river branch. The length of this list is nBranches.
    key : str
        The name of the parameter for which the values are to be retrieved.

    Raises
    ------
    Exception
        If the number of values read from the file doesn't match 1.

    Returns
    -------
    data : List[List[bool]]
        A list of lists. Each list contains per reach within the corresponding
        branch one float or a list of floats depending on input argument nval.
    """
    try:
        g_val = config["General"][key]
    except:
        g_val = ""
    all_values = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val
        values_per_branch = []
        for i in range(nreaches[ib]):
            stri = str(i + 1)
            try:
                val = config[branch][key + stri]
            except:
                val = b_val
            if val == "" and default is not None:
                bval = default
            else:
                try:
                    vals = tuple(x.lower() in ['true', '1', 't', 'y', 'yes'] for x in val.split())
                except:
                    vals = ()
                if len(vals) != 1:
                    raise Exception(
                        'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                            key, i+1, branches[ib], val, 1
                        )
                    )
                bval = vals[0]
            values_per_branch.append(bval)
        all_values.append(values_per_branch)
    return all_values

def write_config(filename: str, config: configparser.ConfigParser) -> None:
    """Pretty print a configParser object (configuration file) to file.

    This function ...
        aligns the equal signs for all keyword/value pairs.
        adds a two space indentation to all keyword lines.
        adds an empty line before the start of a new block.

    Arguments
    ---------
    filename : str
        Name of the configuration file to be written.
    config : configparser.ConfigParser
        The variable containing the configuration.
    """
    sections = config.sections()
    ml = 0
    for s in sections:
        options = config.options(s)
        if len(options) > 0:
            ml = max(ml, max([len(x) for x in options]))

    OPTIONLINE = "  {{:{}s}} = {{}}\n".format(ml)
    with open(filename, "w") as configfile:
        first = True
        for s in sections:
            if first:
                first = False
            else:
                configfile.write("\n")
            configfile.write("[{}]\n".format(s))
            options = config.options(s)
            for o in options:
                configfile.write(OPTIONLINE.format(o, config[s][o]))


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
    return mesh2d[0].name, facedim


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
    copy_var(src, meshname, dst)
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
            copy_var(src, varname, dst)

            # check if variable has bounds attribute, if so copy those as well
            var = src.variables[varname]
            atts2 = ["bounds"]
            for att2 in atts2:
                try:
                    varlist2 = var.getncattr(att2).split()
                except:
                    varlist2 = []
                for varname2 in varlist2:
                    copy_var(src, varname2, dst)

    # close files
    src.close()
    dst.close()


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


def absolute_path(rootdir: str, file: str) -> str:
    """
    Convert a relative path to an absolute path.

    Arguments
    ---------
    rootdir : str
        Any relative paths should be given relative to this location.
    file : str
        A relative or absolute location.

    Returns
    -------
    afile : str
        An absolute location.
    """
    if file == "":
        return file
    else:
        try:
            return os.path.normpath(os.path.join(rootdir, file))
        except:
            return file


def relative_path(rootdir: str, file: str) -> str:
    """
    Convert an absolute path to a relative path.

    Arguments
    ---------
    rootdir : str
        Any relative paths will be given relative to this location.
    file : str
        An absolute location.

    Returns
    -------
    rfile : str
        An absolute or relative location (relative only if it's on the same drive as rootdir).
    """
    if file == "":
        return file
    else:
        try:
            rfile = os.path.relpath(file, rootdir)
            return rfile
        except:
            return file


def get_progloc() -> str:
    """
    Get the location of the program.

    Arguments
    ---------
    None
    """
    progloc = str(pathlib.Path(__file__).parent.absolute())
    return progloc


def read_xyc(
    filename: str, ncol: int = 2, delimiter = None, hasHeader = False
) -> shapely.geometry.linestring.LineString:
    """
    Read lines from a file.

    Arguments
    ---------
    filename : str
        Name of the file to be read.
    ncol : int
        Number of columns to be read (2 or 3)

    Returns
    -------
    L : shapely.geometry.linestring.LineString
        Line strings.
    """
    fileroot, ext = os.path.splitext(filename)
    if ext.lower() == ".xyc":
        if ncol == 3:
            colnames = ["Val", "X", "Y"]
        else:
            colnames = ["X", "Y"]
        if hasHeader:
            if delimiter != None:
                P = pandas.read_csv(
                    filename, names=colnames, skipinitialspace=True, header=0, delimiter=delimiter
                )
            else:
                P = pandas.read_csv(
                filename, names=colnames, skipinitialspace=True, header=0, delim_whitespace=True
                )
        else:
            if delimiter != None:
                P = pandas.read_csv(
                    filename, names=colnames, skipinitialspace=True, delimiter=delimiter
                )
            else:
                P = pandas.read_csv(
                    filename, names=colnames, skipinitialspace=True, delim_whitespace=True
                )
            
        nPnts = len(P.X)
        x = P.X.to_numpy().reshape((nPnts, 1))
        y = P.Y.to_numpy().reshape((nPnts, 1))
        if ncol == 3:
            z = P.Val.to_numpy().reshape((nPnts, 1))
            LC = numpy.concatenate((x, y, z), axis=1)
        else:
            LC = numpy.concatenate((x, y), axis=1)
        L = shapely.geometry.LineString(LC)
    else:
        GEO = geopandas.read_file(filename)["geometry"]
        L = GEO[0]
    return L


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
    xykm = read_xyc(kmfile, ncol=3)

    # make sure that chainage is increasing with node index
    if xykm.coords[0][2] > xykm.coords[1][2]:
        xykm = shapely.geometry.asLineString(xykm.coords[::-1])

    return xykm


def config_get_bool(
    config: configparser.ConfigParser,
    group: str,
    key: str,
    default: Optional[bool] = None,
) -> bool:
    """
    Get a boolean from a selected group and keyword in the analysis settings.

    Arguments
    ---------
    config : configparser.ConfigParser
        Settings for the D-FAST analysis.
    group : str
        Name of the group from which to read.
    key : str
        Name of the keyword from which to read.
    default : Optional[bool]
        Optional default value.

    Raises
    ------
    Exception
        If the keyword isn't specified and no default value is given.

    Returns
    -------
    val : bool
        Boolean value.
    """
    try:
        str = config[group][key].lower()
        val = (
            (str == "yes")
            or (str == "y")
            or (str == "true")
            or (str == "t")
            or (str == "1")
        )
    except:
        if not default is None:
            val = default
        else:
            raise Exception(
                'No boolean value specified for required keyword "{}" in block "{}".'.format(
                    key, group
                )
            )
    return val


def config_get_int(
    config: configparser.ConfigParser,
    group: str,
    key: str,
    default: Optional[int] = None,
    positive: bool = False,
) -> int:
    """
    Get an integer from a selected group and keyword in the analysis settings.

    Arguments
    ---------
    config : configparser.ConfigParser
        Settings for the D-FAST analysis.
    group : str
        Name of the group from which to read.
    key : str
        Name of the keyword from which to read.
    default : Optional[int]
        Optional default value.
    positive : bool
        Flag specifying whether all integers are accepted (if False), or only strictly positive integers (if True).

    Raises
    ------
    Exception
        If the keyword isn't specified and no default value is given.
        If a negative or zero value is specified when a positive value is required.

    Returns
    -------
    val : int
        Integer value.
    """
    try:
        val = int(config[group][key])
    except:
        if not default is None:
            val = default
        else:
            raise Exception(
                'No integer value specified for required keyword "{}" in block "{}".'.format(
                    key, group
                )
            )
    if positive:
        if val <= 0:
            raise Exception(
                'Value for "{}" in block "{}" must be positive, not {}.'.format(
                    key, group, val
                )
            )
    return val


def config_get_float(
    config: configparser.ConfigParser,
    group: str,
    key: str,
    default: Optional[float] = None,
    positive: bool = False,
) -> float:
    """
    Get a floating point value from a selected group and keyword in the analysis settings.

    Arguments
    ---------
    config : configparser.ConfigParser
        Settings for the D-FAST analysis.
    group : str
        Name of the group from which to read.
    key : str
        Name of the keyword from which to read.
    default : Optional[float]
        Optional default value.
    positive : bool
        Flag specifying whether all floats are accepted (if False), or only positive floats (if True).

    Raises
    ------
    Exception
        If the keyword isn't specified and no default value is given.
        If a negative value is specified when a positive value is required.

    Returns
    -------
    val : float
        Floating point value.
    """
    try:
        val = float(config[group][key])
    except:
        if not default is None:
            val = default
        else:
            raise Exception(
                'No floating point value specified for required keyword "{}" in block "{}".'.format(
                    key, group
                )
            )
    if positive:
        if val < 0.0:
            raise Exception(
                'Value for "{}" in block "{}" must be positive, not {}.'.format(
                    key, group, val
                )
            )
    return val


def config_get_str(
    config: configparser.ConfigParser,
    group: str,
    key: str,
    default: Optional[str] = None,
) -> str:
    """
    Get a string from a selected group and keyword in the analysis settings.

    Arguments
    ---------
    config : configparser.ConfigParser
        Settings for the D-FAST analysis.
    group : str
        Name of the group from which to read.
    key : str
        Name of the keyword from which to read.
    default : Optional[str]
        Optional default value.

    Raises
    ------
    Exception
        If the keyword isn't specified and no default value is given.

    Returns
    -------
    val : str
        String.
    """
    try:
        val = config[group][key]
    except:
        if not default is None:
            val = default
        else:
            raise Exception(
                'No value specified for required keyword "{}" in block "{}".'.format(
                    key, group
                )
            )
    return val


def config_get_range(
    config: configparser.ConfigParser, group: str, key: str, default: Optional[Tuple[float,float]] = None,
) -> Tuple[float, float]:
    """
    Get a start and end value from a selected group and keyword in the analysis settings.

    Arguments
    ---------
    config : configparser.ConfigParser
        Settings for the D-FAST analysis.
    group : str
        Name of the group from which to read.
    key : str
        Name of the keyword from which to read.
    default : Optional[Tuple[float,float]]
        Optional default range.

    Returns
    -------
    val : Tuple[float,float]
        Lower and upper limit of the range.
    """
    try:
        str = config_get_str(config, group, key,"")
        obrack = str.find("[")
        cbrack = str.find("]")
        if obrack >= 0 and cbrack >= 0:
            str = str[obrack + 1 : cbrack - 1]
        vallist = [float(fstr) for fstr in str.split(":")]
        if vallist[0] > vallist[1]:
            val = (vallist[1], vallist[0])
        else:
            val = (vallist[0], vallist[1])
    except:
        if not default is None:
            val = default
        else:
            raise Exception(
                'Invalid range specification "{}" for required keyword "{}" in block "{}".'.format(
                    str, key, group
                )
            )
    return val
