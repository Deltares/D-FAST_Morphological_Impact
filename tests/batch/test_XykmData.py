import numpy
from dfastmi.batch.XykmData import XykmData
from unittest.mock import patch
from shapely.geometry import LineString
import shapely.prepared # needed for test_determine_xykm_data

class Test_XykmData_initialize_data():
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
        
        with patch('dfastmi.batch.DflowfmReporters.XykmDataReporter', autospec=True) as xykm_data_reporter, \
             patch('dfastmi.batch.XykmData.filter_faces_by_node_condition') as filter_faces_by_node_condition:
                 xykm_data = XykmData(xykm_data_reporter)
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
                 
                 assert len(xykm_data_reporter.mock_calls) == 0
                 
    def test_determine_xykm_data(self):
        xn = numpy.array([10,20,30])
        yn = numpy.array([40,50,60])
        face_node_connectivity = numpy.array([70,80,90])
        
        xni = numpy.array([1,2,3])
        yni = numpy.array([4,5,6])
        face_node_connectivity_index = numpy.array([7,8,9])
        iface = numpy.array([0,1,2], dtype=numpy.int64)
        inode = numpy.array([13,14,15])
        
        dxi = numpy.array([22,23,24])
        dyi = numpy.array([25,26,27])
        
        sni = numpy.array([16,17,18])
        nni = numpy.array([19,20,21])
        
        xykm = LineString([(1, -1), (1, 0), (2, 0), (2, 1)])
        
        xykline = numpy.array(xykm.coords)
        interest_region = numpy.array([1,1,1])
        
        with patch('dfastmi.batch.DflowfmReporters.XykmDataReporter', autospec=True) as xykm_data_reporter, \
             patch('dfastmi.batch.XykmData.project_xy_point_onto_line') as project_xy_point_onto_line,\
             patch('dfastmi.batch.XykmData.face_mean'),\
             patch('dfastmi.batch.XykmData.get_direction') as get_direction,\
             patch('dfastmi.batch.XykmData.filter_faces_by_node_condition') as filter_faces_by_node_condition:
                 xykm_data = XykmData(xykm_data_reporter)
                 
                 filter_faces_by_node_condition.return_value = (xni, yni, face_node_connectivity_index, iface, inode)
                 project_xy_point_onto_line.return_value = (sni, nni)
                 get_direction.return_value = (dxi, dyi)
                 
                 xykm_data.initialize_data(xykm,xn,yn,face_node_connectivity)
                 
                 assert xykm_data.xykm == xykm
                 numpy.testing.assert_array_equal(xykm_data.xni, xni)
                 numpy.testing.assert_array_equal(xykm_data.yni, yni)
                 numpy.testing.assert_array_equal(xykm_data.face_node_connectivity_index, face_node_connectivity_index)
                 numpy.testing.assert_array_equal(xykm_data.iface, iface)
                 numpy.testing.assert_array_equal(xykm_data.inode, inode)
                 assert xykm_data.xmin == -2999
                 assert xykm_data.xmax == 3002
                 assert xykm_data.ymin == -3001
                 assert xykm_data.ymax == 3001
                 numpy.testing.assert_array_equal(xykm_data.dxi, dxi)
                 numpy.testing.assert_array_equal(xykm_data.dyi, dyi)
                 numpy.testing.assert_array_equal(xykm_data.xykline, xykline)
                 numpy.testing.assert_array_equal(xykm_data.interest_region, interest_region)
                 numpy.testing.assert_array_equal(xykm_data.sni, sni)
                 numpy.testing.assert_array_equal(xykm_data.nni, nni)
                 
                 assert len(xykm_data_reporter.mock_calls) == 10
