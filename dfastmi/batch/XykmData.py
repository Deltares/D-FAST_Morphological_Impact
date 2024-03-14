from dfastmi.batch.Distance import get_direction
from dfastmi.batch.Projection import project_xy_point_onto_line
from dfastmi.batch.Face import filter_faces_by_node_condition, face_mean
from dfastmi.batch.DflowfmLoggers import XykmDataLogger
from shapely.geometry.linestring import LineString

import numpy
import shapely

class XykmData():
    """
    Class that initializes and keeps Xykm related data.
    """
    
    _logger : XykmDataLogger
    
    def __init__(self, logger : XykmDataLogger):
        """
        Arguments
        ---------
        logger : XykmDataLogger
            Logger that logs information for this class.
        """
        self._xykm : LineString = None
        self._xni : numpy.ndarray = None
        self._yni : numpy.ndarray = None
        self._face_node_connectivity_index : numpy.ma.masked_array = None
        self._iface : numpy.ndarray = None
        self._inode : numpy.ndarray = None
        self._xmin : numpy.ndarray = None
        self._xmax : numpy.ndarray = None
        self._ymin : numpy.ndarray = None
        self._ymax : numpy.ndarray = None
        self._dxi : numpy.ndarray = None
        self._dyi : numpy.ndarray = None
        self._xykline : numpy.ndarray = None
        self._interest_region : numpy.ndarray = None
        self._sni : numpy.ndarray = None
        self._nni : numpy.ndarray = None

        self._logger = logger
        
    @property
    def xykm(self) -> LineString:
        """
        Original river chainage line.
        """
        return self._xykm
    
    @property
    def xni(self) -> numpy.ndarray:
        """
        X-coordinates of the mesh nodes.
        """
        return self._xni

    @property
    def yni(self) -> numpy.ndarray:
        """
        Y-coordinates of the mesh nodes.
        """
        return self._yni
    
    @property
    def face_node_connectivity_index(self) -> numpy.ma.masked_array:
        """
        Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
        Node indices are 0-based, hence the maximum node index is K-1.
        """
        return self._face_node_connectivity_index
    
    @property
    def iface(self) -> numpy.ndarray:
        """
        Array of length M2 containing the indices of the faces to keep [-]. 
        """
        return self._iface
    
    @property
    def inode(self) -> numpy.ndarray:
        """
        Array of length K2 containing the indices of the nodes to keep [-]. 
        """
        return self._inode
    
    @property
    def xmin(self) -> numpy.ndarray:
        """
        boundary limits x min in [m]
        """
        return self._xmin
    
    @property
    def xmax(self) -> numpy.ndarray:
        """
        boundary limits x max in [m]
        """
        return self._xmax
    
    @property
    def ymin(self) -> numpy.ndarray:
        """
        boundary limits y min in [m]
        """
        return self._ymin
    
    @property
    def ymax(self) -> numpy.ndarray:
        """
        boundary limits y max in [m]
        """
        return self._ymax
    
    @property
    def dxi(self) -> numpy.ndarray:
        """
        Array of length N containing x-component of the unit direction vector at the given points.
        """
        return self._dxi
    
    @property
    def dyi(self) -> numpy.ndarray:
        """
        Array of length N containing y-component of the unit direction vector at the given points.
        """
        return self._dyi
    
    @property
    def xykline(self) -> numpy.ndarray:
        """
        Array containing the x,y and chainage data of a line.
        """
        return self._xykline
    
    @property
    def interest_region(self) -> numpy.ndarray:
        """
        Region on which the sedimentation analysis is performed.
        """
        return self._interest_region
    
    @property
    def sni(self) -> numpy.ndarray:
        """
        """
        return self._sni
    
    @property
    def nni(self) -> numpy.ndarray:
        """
        """
        return self._nni
            
    def initialize_data(self, xykm : LineString, xn : numpy.ndarray, yn : numpy.ndarray, face_node_connectivity : numpy.ndarray):
        """
        initializes the properties in the XykmData object.
        
        Arguments
        ---------
        xykm : LineString
            Array containing the x, y, and chainage; unit m for x and y, km for chainage.
        xn : numpy.ndarray
            X-coordinates of the mesh nodes.
        yn : numpy.ndarray
            Y-coordinates of the mesh nodes.
        face_node_connectivity : numpy.ndarray
            Masked M x N array containing the indices of (max N) corner nodes for each of the M cells [-].
            Node indices are 0-based, hence the maximum node index is K-1.
        """
        self._xykm = xykm
        
        if self._xykm is None:
            # keep all nodes and faces
            keep = numpy.full(xn.shape, True)
            self._xni, self._yni, self._face_node_connectivity_index, self._iface, self._inode = filter_faces_by_node_condition(xn, yn, face_node_connectivity, keep)
            self._xmin = xn.min()
            self._xmax = xn.max()
            self._ymin = yn.min()
            self._ymax = yn.max()
        else:
            dnmax = 3000.0
            self._logger.log_identify_region_of_interest()
            self._logger.print_buffer()
            xybuffer = xykm.buffer(dnmax)
            bbox = xybuffer.envelope.exterior
            self._logger.print_prepare()
            xybprep = shapely.prepared.prep(xybuffer)

            self._logger.print_prepare_filter(1)
            self._xmin = bbox.coords[0][0]
            self._xmax = bbox.coords[1][0]
            self._ymin = bbox.coords[0][1]
            self._ymax = bbox.coords[2][1]
            keep = (xn > self._xmin) & (xn < self._xmax) & (yn > self._ymin) & (yn < self._ymax)
            self._logger.print_prepare_filter(2)
            for i in range(xn.size):
                if keep[i] and not xybprep.contains(shapely.geometry.Point((xn[i], yn[i]))):
                    keep[i] = False

            self._logger.print_apply_filter()
            self._xni, self._yni, self._face_node_connectivity_index, self._iface, self._inode = filter_faces_by_node_condition(xn, yn, face_node_connectivity, keep)
            self._interest_region = numpy.zeros(face_node_connectivity.shape[0], dtype=numpy.int64)
            self._interest_region[self._iface] = 1

            self._xykline = numpy.array(xykm.coords)

            # project all nodes onto the line, obtain the distance along (self._sni) and normal (dni) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            xyline = self._xykline[:,:2]

            # project all nodes onto the line, obtain the distance along (sfi) and normal (nfi) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            self._logger.log_project()
            self._sni, self._nni = project_xy_point_onto_line(self._xni, self._yni, xyline)
            sfi = face_mean(self._sni, self._face_node_connectivity_index)

            # determine chainage values of each cell
            self._logger.log_chainage()

            # determine line direction for each cell
            self._logger.log_direction()
            self._dxi, self._dyi = get_direction(xyline, sfi)

            self._logger.log_done()