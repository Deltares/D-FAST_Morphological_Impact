import numpy
from dfastmi.batch.XykmData import XykmData
from unittest.mock import patch

class Test_XykmData():
    def test_keep_all_nodes_and_faces(self):
        xykm = None
        xn = numpy.array([10,20,30])
        yn = numpy.array([40,50,60])
        face_node_connectivity = numpy.array([70,80,90])
        
        xni = numpy.array([1,2,3])
        yni = numpy.array([4,5,6])
        face_node_connectivity_index = numpy.array([7,8,9])
        iface = numpy.array([10,11,12])
        inode = numpy.array([13,14,15])
        
        with patch('dfastmi.batch.DflowfmLoggers.XykmDataLogger', autospec=True) as xykm_data_logger, \
             patch('dfastmi.batch.XykmData.filter_faces_by_node_condition') as filter_faces_by_node_condition:
                 xykm_data = XykmData(xykm_data_logger)
                 filter_faces_by_node_condition.return_value = (xni, yni, face_node_connectivity_index, iface, inode)
                 xykm_data.initialize_data(xykm,xn,yn,face_node_connectivity)
                 
                 assert xykm_data.xykm == None
                 numpy.testing.assert_array_equal(xykm_data.xni, xni)
                 numpy.testing.assert_array_equal(xykm_data.yni, yni)
                 numpy.testing.assert_array_equal(xykm_data.face_node_connectivity_index, face_node_connectivity_index)
                 numpy.testing.assert_array_equal(xykm_data.iface, iface)
                 numpy.testing.assert_array_equal(xykm_data.inode, inode)
                 assert xykm_data.xmin == xn.min()
                 assert xykm_data.xmax == xn.max()
                 assert xykm_data.ymin == yn.min()
                 assert xykm_data.ymax == yn.max()
                 assert xykm_data.dxi == None
                 assert xykm_data.dyi == None
                 assert xykm_data.xykline == None
                 assert xykm_data.interest_region == None
                 assert xykm_data.sni == None
                 assert xykm_data.nni == None
