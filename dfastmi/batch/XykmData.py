import dfastmi.batch.Distance
import dfastmi.batch.Face
import dfastmi.batch.Projection
from dfastmi.batch.DflowfmLoggers import XykmDataLogger

import numpy
import shapely

class XykmData():
    
    _logger : XykmDataLogger
    
    def __init__(self, logger : XykmDataLogger):
        self.xykm = None
        self.xni = None
        self.yni = None
        self.face_node_connectivity_index = None
        self.iface = None
        self.inode = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.dxi = None
        self.dyi = None
        self.xykline = None
        self.interest_region = None
        self.sni = None
        self.nni = None

        self._logger = logger
        
    def initialize_data(self, xykm, xn, yn, face_node_connectivity):
        self.xykm = xykm
        
        if self.xykm is None:
            # keep all nodes and faces
            keep = numpy.full(xn.shape, True)
            self.xni, self.yni, self.face_node_connectivity_index, self.iface, self.inode = dfastmi.batch.Face.filter_faces_by_node_condition(xn, yn, face_node_connectivity, keep)
            self.xmin = xn.min()
            self.xmax = xn.max()
            self.ymin = yn.min()
            self.ymax = yn.max()
        else:
            dnmax = 3000.0
            self._logger.log_identify_region_of_interest()
            self._logger.print_buffer()
            xybuffer = xykm.buffer(dnmax)
            bbox = xybuffer.envelope.exterior
            self._logger.print_prepare()
            xybprep = shapely.prepared.prep(xybuffer)

            self._logger.print_prepare_filter(1)
            self.xmin = bbox.coords[0][0]
            self.xmax = bbox.coords[1][0]
            self.ymin = bbox.coords[0][1]
            self.ymax = bbox.coords[2][1]
            keep = (xn > self.xmin) & (xn < self.xmax) & (yn > self.ymin) & (yn < self.ymax)
            self._logger.print_prepare_filter(2)
            for i in range(xn.size):
                if keep[i] and not xybprep.contains(shapely.geometry.Point((xn[i], yn[i]))):
                    keep[i] = False

            self._logger.print_apply_filter()
            self.xni, self.yni, self.face_node_connectivity_index, self.iface, self.inode = dfastmi.batch.Face.filter_faces_by_node_condition(xn, yn, face_node_connectivity, keep)
            self.interest_region = numpy.zeros(face_node_connectivity.shape[0], dtype=numpy.int64)
            self.interest_region[self.iface] = 1

            self.xykline = numpy.array(xykm.coords)

            # project all nodes onto the line, obtain the distance along (self.sni) and normal (dni) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            xyline = self.xykline[:,:2]

            # project all nodes onto the line, obtain the distance along (sfi) and normal (nfi) the line
            # note: we use distance along line here instead of chainage since the latter may locally not be a linear function of the distance
            self._logger.log_project()
            self.sni, self.nni = dfastmi.batch.Projection.project_xy_point_onto_line(self.xni, self.yni, xyline)
            sfi = dfastmi.batch.Face.face_mean(self.sni, self.face_node_connectivity_index)

            # determine chainage values of each cell
            self._logger.log_chainage()

            # determine line direction for each cell
            self._logger.log_direction()
            self.dxi, self.dyi = dfastmi.batch.Distance.get_direction(xyline, sfi)

            self._logger.log_done()