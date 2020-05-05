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

import numpy
import netCDF4
import configparser


"""Read data columns from a SIMONA XYZ file"""
def read_waqua_xyz(filename, cols=(2)):
    data = numpy.genfromtxt(filename, delimiter=',', skip_header=1, usecols=cols)
    return data


"""Read the last time step of any quantity defined at faces from a D-Flow FM map-file"""
def read_fm_map(filename, stdname):
    # open file
    rootgrp  = netCDF4.Dataset(filename)
    # locate variable
    var = rootgrp.get_variables_by_attributes(standard_name=stdname, location='face')
    if len(var) != 1:
        raise Exception('Expected one variable for "{}", but obtained {}.',stdname,len(var))
    var = var[0]
    dims = var.dimensions
    # assume first dimension is 'time', and obtain last time step
    data   = var[-1,:]
    # close file
    rootgrp.close()
    # return data
    return data


"""Copy UGRID mesh data from source file to destination file"""
def copy_ugrid(src, meshname, dst):
    # if src is string, then open the file
    if isinstance(src,str):
        src = netCDF4.Dataset(src)
        srcclose = True
    else:
        dstclose = False

    # locate source mesh
    mesh = src.variables[meshname]
        
    # if dst is string, then open the file
    if isinstance(dst,str):
        dst = netCDF4.Dataset(dst, "w", format="NETCDF4")
        dstclose = True
    else:
        dstclose = False
    
    # copy mesh variable
    copy_var(src, meshname, dst)
    atts = ['face_node_connectivity','edge_node_connectivity','edge_face_connectivity','face_coordinates','edge_coordinates','node_coordinates']
    for att in atts:
        try:
            varlist = mesh.getncattr(att).split()
        except:
            varlist = []
        for varname in varlist:
            copy_var(src, varname, dst)
            
            # check if variable has bounds attribute, if so copy those as well
            var = src.variables[varname]
            atts2 = ['bounds']
            for att2 in atts2:
                try:
                    varlist2 = var.getncattr(att2).split()
                except:
                    varlist2 = []
                for varname2 in varlist2:
                    copy_var(src, varname2, dst)
    
    # close files if strings where provided
    if srcclose:
        src.close()
    if dstclose:
        dst.close()


"""Copy a single NetCDF variable including attributes from source file to destination file. Create dimensions as necessary."""
def copy_var(src, varname, dst):
    srcvar = src.variables[varname]
    # copy dimensions
    for name in srcvar.dimensions:
        dimension = src.dimensions[name]
        if name not in dst.dimensions.keys():
            dst.createDimension(
                name, (len(dimension) if not dimension.isunlimited() else None))

    # copy variable
    dstvar = dst.createVariable(varname, srcvar.datatype, srcvar.dimensions)

    # copy variable attributes all at once via dictionary
    dstvar.setncatts(srcvar.__dict__)
    dstvar[:] = srcvar[:]


"""Add a new variable defined at faces to an existing UGRID NetCDF file"""
def ugrid_add(dstfile, varname, ldata, meshname, facedim):
    # open destination file
    dst    = netCDF4.Dataset(dstfile, "a")
    # check if face dimension exists
    dim = dst.dimensions[facedim]
    # add variable and write data
    var = dst.createVariable(varname,"f8",(facedim,))
    var.mesh = meshname
    var.location = 'face'
    var[:] = ldata[:]
    # close destination file
    dst.close()


"""Write a SIMONA BOX file"""
def write_simona_box(filename, rdata, firstm, firstn):
    boxfile = open (filename, 'w')
    shp = numpy.shape(rdata)
    mmax = shp[0]
    nmax = shp[1]
    boxheader = '      BOX MNMN=({m1:4d},{n1:5d},{m2:5d},{n2:5d}), VARIABLE_VAL=\n'
    nstep     = 10
    for j in range(firstn,nmax,nstep):
        k = min(nmax, j+nstep)
        boxfile.write(boxheader.format(m1=firstm+1, n1=j+1, m2=mmax, n2=k))
        nvalues = (mmax-firstm)*(k-j)
        boxdata = ('   '+'{:12.3f}'*(k-j)+'\n')*(mmax-firstm)
        values  = tuple(rdata[:,j:k].reshape(nvalues))
        boxfile.write(boxdata.format(*values))
    
    boxfile.close()


"""Read program dialog texts"""
def read_program_texts(filename):
    all_lines = open(filename, 'r').read().splitlines()
    dict      = {}
    str       = []
    key       = None
    for line in all_lines:
        rline = line.strip()
        if rline.startswith('[') and rline.endswith(']'):
            if not key is None:
                dict[key] = str
            key = rline[1:-1]
            str = []
        else:
            str.append(line)
    dict[key] = str
    return dict


"""Read the configuration file containing the listing of various branches/reaches and associated default parameter settings"""
def read_rivers(filename = 'rivers.ini'):
    # read the file
    config = configparser.ConfigParser()
    with open(filename, 'r') as configfile:
        config.read_file(configfile)

    # initialize rivers
    rivers = {}

    # parse branches
    branches = []
    i = 0
    while True:
        i = i+1
        name = 'Name'+str(i)
        try:
            branch = config['Branches'][name]
            branches.extend([branch])
        except:
            break
    rivers['branches'] = branches

    # parse reaches
    allreaches    = []
    qlocations    = []
    for branch in branches:
        qlocation = config[branch]['QLocation']
        qlocations.extend([qlocation])

        i          = 0
        reaches    = []
        while True:
            i = i+1
            try:
                 reach = config[branch]['Reach'+str(i)]
                 reaches.extend([reach])
            except:
                 break
        allreaches.extend([reaches])
    rivers['reaches']    = allreaches
    rivers['qlocations'] = qlocations

    nreaches = [len(x) for x in allreaches]
    rivers['proprate_high'] = collect_values(config, branches, nreaches, 1, 'PrHigh')
    rivers['proprate_low']  = collect_values(config, branches, nreaches, 1, 'PrLow')
    rivers['normal_width']  = collect_values(config, branches, nreaches, 1, 'NWidth')
    rivers['ucritical']     = collect_values(config, branches, nreaches, 1, 'UCrit')
    rivers['qbankfull']     = collect_values(config, branches, nreaches, 1, 'QBankfull')
    rivers['qstagnant']     = collect_values(config, branches, nreaches, 1, 'QStagnant')
    rivers['qmin']          = collect_values(config, branches, nreaches, 1, 'QMin')
    rivers['qfit']          = collect_values(config, branches, nreaches, 2, 'QFit')
    rivers['qlevels']       = collect_values(config, branches, nreaches, 4, 'QLevels')
    rivers['dq']            = collect_values(config, branches, nreaches, 2, 'dQ')

    return rivers


"""Read river configuration data"""
def collect_values(config, branches, nreaches, nval, key):
    try:
        g_val = config['Branches'][key]
    except:
        g_val = None
    allvalues = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val
        values = []
        for i in range(nreaches[ib]):
            stri = str(i+1)
            try:
                val = config[branch][key+stri]
            except:
                val = b_val
            if nval==1:
                vals = float(val)
            else:
                vals = [float(x) for x in val.split()]
                if len(vals) != nval:
                    raise Exception('Incorrect number of values read from "{}". Need {} values.',val,nval)
            values.extend([vals])
        allvalues.extend([values])
    return allvalues
