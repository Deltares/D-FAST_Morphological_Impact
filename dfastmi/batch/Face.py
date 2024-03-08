import numpy

def face_all(bn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        bf = bn[FNC].all(axis=1)
    else:
        # varying number of nodes
        fnc = FNC.data
        fnc[FNC.mask] = 0
        bfn = numpy.ma.array(bn[fnc], mask=FNC.mask)
        bf = bfn.all(axis=1)

    return bf

def face_mean(vn: numpy.ndarray, FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        vf = vn[FNC].mean(axis=1)
    else:
        # varying number of nodes
        fnc = FNC.data
        fnc[FNC.mask] = 0
        vfn = numpy.ma.array(vn[fnc], mask=FNC.mask)
        vf = vfn.all(axis=1)

    return vf

def filter_faces_by_face_condition(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ma.masked_array, condition: numpy.ndarray) -> [numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    Reduces the mesh to only those cells in which the condition is True. 

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the mesh nodes [m or deg east].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the mesh nodes [m or deg north].
    FNC : numpy.ma.masked_array
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
    rFNC : numpy.ma.masked_array
        Masked M2 x N2 array containing the indices of (max N2) corner nodes for each of the M2 <= M cells [-].
        Node indices are 0-based, hence the maximum node index is K2-1.
    iface : numpy.ndarray
        Array of length M2 containing the indices of the faces to keep [-]. 
    inode : numpy.ndarray
        Array of length K2 containing the indices of the nodes to keep [-]. 
    """
    iface = numpy.where(condition)[0]
    FNCi = FNC[iface]
    inode = numpy.unique(FNCi.flatten())
    if len(inode) == 0:
        inode_max = 0
    else:
        inode_max = inode.max()

    FNCi.data[FNCi.mask] = 0
    renum = numpy.zeros(inode_max + 1, dtype=numpy.int64)
    renum[inode] = range(len(inode))
    rFNCi = numpy.ma.masked_array(renum[FNCi], mask=FNCi.mask)

    return xn[inode], yn[inode], rFNCi, iface, inode


def filter_faces_by_node_condition(xn: numpy.ndarray, yn: numpy.ndarray, FNC: numpy.ma.masked_array, condition: numpy.ndarray) -> [numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """
    Reduces the mesh to only those cells in which the condition is True. 

    Arguments
    ---------
    xn : numpy.ndarray
        Array of length K containing the x-coordinates of the mesh nodes [m or deg east].
    yn : numpy.ndarray
        Array of length K containing the y-coordinate of the mesh nodes [m or deg north].
    FNC : numpy.ma.masked_array
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
    rFNC : numpy.ma.masked_array
        Masked M2 x N2 array containing the indices of (max N2) corner nodes for each of the M2 <= M cells [-].
        Node indices are 0-based, hence the maximum node index is K2-1.
    iface : numpy.ndarray
        Array of length M2 containing the indices of the faces to keep [-]. 
    inode : numpy.ndarray
        Array of length K2 containing the indices of the nodes to keep [-]. 
    """
    fcondition = face_all(condition, FNC)
    rxn, ryn, rFNC, iface, inode = filter_faces_by_face_condition(xn, yn, FNC, fcondition)
    return rxn, ryn, rFNC, iface, inode


def count_nodes(FNC: numpy.ndarray) -> numpy.ndarray:
    if FNC.mask.shape == ():
        # all faces have the same number of nodes
        nnodes = numpy.ones(FNC.data.shape[0], dtype=numpy.int64) * FNC.data.shape[1]
    else:
        # varying number of nodes
        nnodes = FNC.mask.shape[1] - FNC.mask.sum(axis=1)

    return nnodes

def facenode_to_edgeface(FNC: numpy.ndarray) -> numpy.ndarray:
    """
    Derive face 2 face connectivity from face 2 node connectivity.

    Arguments
    ---------
    FNC : numpy.ma.masked_array
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells.
        Maximum node index is K-1.

    Returns
    -------
    FFC : numpy.ma.masked_array
        Masked K x 2 array containing the indices of neighbouring cell pairs.
    """
    nfaces = FNC.shape[0]
    nnodes = count_nodes(FNC) # nedges equals to nnodes
    tot_nedges = nnodes.sum()

    edges = numpy.zeros((tot_nedges, 2), dtype=numpy.int64)
    ie = 0
    for i in range(nfaces):
        nni = nnodes[i]
        fni = FNC[i][0:nni]
        fni2 = numpy.roll(fni, 1)

        m_fni = numpy.reshape(fni,(-1,1))
        m_fni2 = numpy.reshape(fni2,(-1,1))
        edgesi = numpy.concatenate((m_fni,m_fni2), axis=1)

        edges[ie + numpy.arange(nni),:] = edgesi
        ie = ie + nni

    edges = numpy.sort(edges, axis=1)
    edges, iedge = numpy.unique(edges, axis=0, return_inverse=True)
    nedges = edges.shape[0]

    #FEC = FNC.copy()
    #ie = 0
    #for i in range(nfaces):
    #    nni = nnodes[i]
    #    FEC[i][0:nni] = iedge[ie + numpy.arange(nni)]
    #    ie = ie + nni

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