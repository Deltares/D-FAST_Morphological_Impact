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

import numpy

def face_all(bn: numpy.ndarray, face_node_connectivity: numpy.ndarray) -> numpy.ndarray:
    if face_node_connectivity.mask.shape == ():
        # all faces have the same number of nodes
        bf = bn[face_node_connectivity].all(axis=1)
    else:
        # varying number of nodes
        face_node_connectivity_data = face_node_connectivity.data
        face_node_connectivity_data[face_node_connectivity.mask] = 0
        bfn = numpy.ma.array(bn[face_node_connectivity_data], mask=face_node_connectivity.mask)
        bf = bfn.all(axis=1)

    return bf

def face_mean(vn: numpy.ndarray, face_node_connectivity: numpy.ndarray) -> numpy.ndarray:
    if face_node_connectivity.mask.shape == ():
        # all faces have the same number of nodes
        vf = vn[face_node_connectivity].mean(axis=1)
    else:
        # varying number of nodes
        face_node_connectivity_data = face_node_connectivity.data
        face_node_connectivity_data[face_node_connectivity.mask] = 0
        vfn = numpy.ma.array(vn[face_node_connectivity_data], mask=face_node_connectivity.mask)
        vf = vfn.all(axis=1)

    return vf

def filter_faces_by_face_condition(xn: numpy.ndarray, yn: numpy.ndarray, face_node_connectivity: numpy.ma.masked_array, condition: numpy.ndarray) -> [numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    Reduces the mesh to only those cells in which the condition is True. 

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the mesh nodes [m or deg east].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the mesh nodes [m or deg north].
    face_node_connectivity : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
        Node indices are 0-based, hence the maximum node index is K-1.
    condition : numpy.ndarray
        Array of length M containing the boolean flag on the mesh cells [-].

    Results
    -------
    rxn : numpy.ndarray
        Array of length K2 <= K containing the x-coordinates of the reduced mesh nodes [m or deg east].
    ryn : numpy.ndarray
        Array of length K2 <= K containing the y-coordinate of the reduced mesh nodes [m or deg north].
    renumbered_face_node_connectivity : numpy.ma.masked_array
        Masked M2 x N2 array containing the indices of (max N2) corner nodes for each of the M2 <= M cells [-].
        Node indices are 0-based, hence the maximum node index is K2-1.
    iface : numpy.ndarray
        Array of length M2 containing the indices of the faces to keep [-]. 
    inode : numpy.ndarray
        Array of length K2 containing the indices of the nodes to keep [-]. 
    """
    iface = numpy.where(condition)[0]
    face_node_connectivity_index = face_node_connectivity[iface]
    inode = numpy.unique(face_node_connectivity_index.flatten())
    if len(inode) == 0:
        inode_max = 0
    else:
        inode_max = inode.max()

    face_node_connectivity_index.data[face_node_connectivity_index.mask] = 0
    renum = numpy.zeros(inode_max + 1, dtype=numpy.int64)
    renum[inode] = range(len(inode))
    renumbered_face_node_connectivity = numpy.ma.masked_array(renum[face_node_connectivity_index], mask=face_node_connectivity_index.mask)

    return xn[inode], yn[inode], renumbered_face_node_connectivity, iface, inode


def filter_faces_by_node_condition(xn: numpy.ndarray, yn: numpy.ndarray, face_node_connectivity: numpy.ma.masked_array, condition: numpy.ndarray) -> [numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    Reduces the mesh to only those cells in which the condition is True. 

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the mesh nodes [m or deg east].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the mesh nodes [m or deg north].
    face_node_connectivity : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
        Node indices are 0-based, hence the maximum node index is K-1.
    condition : numpy.ndarray
        Array of length K containing the boolean flag on the mesh nodes [-].

    Results
    -------
    rxn : numpy.ndarray
        Array of length K2 <= K containing the x-coordinates of the reduced mesh nodes [m or deg east].
    ryn : numpy.ndarray
        Array of length K2 <= K containing the y-coordinate of the reduced mesh nodes [m or deg north].
    renumbered_face_node_connectivity : numpy.ma.masked_array
        Masked M2 x N2 array containing the indices of (max N2) corner nodes for each of the M2 <= M cells [-].
        Node indices are 0-based, hence the maximum node index is K2-1.
    iface : numpy.ndarray
        Array of length M2 containing the indices of the faces to keep [-]. 
    inode : numpy.ndarray
        Array of length K2 containing the indices of the nodes to keep [-]. 
    """
    fcondition = face_all(condition, face_node_connectivity)
    rxn, ryn, renumbered_face_node_connectivity, iface, inode = filter_faces_by_face_condition(xn, yn, face_node_connectivity, fcondition)
    return rxn, ryn, renumbered_face_node_connectivity, iface, inode


def count_nodes(face_node_connectivity: numpy.ndarray) -> numpy.ndarray:
    if face_node_connectivity.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(face_node_connectivity.data.shape[0], dtype=numpy.int64) * face_node_connectivity.data.shape[1]
    else:
        # varying number of nodes
        nnodes = face_node_connectivity.mask.shape[1] - face_node_connectivity.mask.sum(axis=1)

    return nnodes

def facenode_to_edgeface(face_node_connectivity: numpy.ndarray) -> numpy.ndarray:
    """
    Derive face 2 face connectivity from face 2 node connectivity.

    Arguments
    ---------
    face_node_connectivity : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.

    Returns
    -------
    FFC : numpy.ma.masked_array
        Masked K x 2 array containing the indices of neighbouring cell pairs.
    """
    nfaces = face_node_connectivity.shape[0]
    nnodes = count_nodes(face_node_connectivity) # nedges equals to nnodes
    tot_nedges = nnodes.sum()

    edges = numpy.zeros((tot_nedges, 2), dtype=numpy.int64)
    ie = 0
    for i in range(nfaces):
        nni = nnodes[i]
        fni = face_node_connectivity[i][0:nni]
        fni2 = numpy.roll(fni, 1)

        m_fni = numpy.reshape(fni,(-1,1))
        m_fni2 = numpy.reshape(fni2,(-1,1))
        edgesi = numpy.concatenate((m_fni,m_fni2), axis=1)

        edges[ie + numpy.arange(nni),:] = edgesi
        ie = ie + nni

    edges = numpy.sort(edges, axis=1)
    edges, iedge = numpy.unique(edges, axis=0, return_inverse=True)
    nedges = edges.shape[0]

    EFC = -numpy.ones((nedges, 2), dtype=numpy.int64)
    ie = 0
    for i in range(nfaces):
        nni = nnodes[i]
        for j in range(nni):
            e = iedge[ie + j]
            if EFC[e,0]  < 0:
                EFC[e,0] = i
            else:
                EFC[e,1] = i
        ie = ie + nni

    EFC = EFC[EFC[:,1] > 0,:]
    return EFC