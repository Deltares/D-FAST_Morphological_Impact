from typing import Any, Dict, TextIO, Tuple
from mock import Mock, patch
from dfastmi.batch.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.batch.AnalyserDflowfm import AnalyserDflowfm
from shapely.geometry.linestring import LineString
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from tests.batch.Helper_AnalyserAndReporterDflowfm import TestCase_display_needs_tide_old_zmin_zmax, TestCase_display_old_zmin_zmax # needed for fixture
from tests.batch.Helper_AnalyserAndReporterDflowfm import display_needs_tide_old_zmin_zmax, display_old_zmin_zmax # needed for fixture

import numpy
import shapely
import pytest

class Test_AnalyserDflowfm():
    
    report: TextIO
    nwidth: float
    filenames: Dict[Any, Tuple[str,str]]
    xykm: shapely.geometry.linestring.LineString
    plotops: Dict
    
    @pytest.fixture
    def setup(self):
        self.report = None
        self.nwidth = 1.0
        self.filenames = {}
        self.xykm = None
        self.plotops = None
        
        initialized_config = Mock(spec=AConfigurationInitializerBase)
        initialized_config.q_threshold = 1.0
        initialized_config.tstag = 1.0
        initialized_config.discharges = [1.0, 2.0, 3.0]
        initialized_config.time_fractions_of_the_year = [1.0, 2.0, 3.0]
        initialized_config.rsigma = [0.1, 0.2, 0.3]
        initialized_config.slength = 1.0
        initialized_config.n_fields = 1
        initialized_config.tide_bc: Tuple[str, ...] = ("name1", "name2")
        initialized_config.ucrit = 0.3
        self.initialized_config = initialized_config
    
    def _get_mocked_xykm_data(self, xykm):
        xykm_data = Mock(spec=XykmData)
        xykm_data.iface = numpy.array([0, 1, 2, 3, 4])
        xykm_data.xykm = xykm
        xykm_data.face_node_connectivity_index.mask.shape = ()
        xykm_data.face_node_connectivity_index.data.shape = numpy.array([1, 1])
        xykm_data.xmin = 1
        xykm_data.ymin = 1
        xykm_data.xmax = 2
        xykm_data.ymax = 2
        xykm_data.xykline = numpy.array([0, 1, 2, 3, 4])
        xykm_data.interest_region = numpy.array([0, 1, 2, 3, 4])
        xykm_data.xni = numpy.array([0, 1, 2, 3, 4])
        xykm_data.yni = numpy.array([0, 1, 2, 3, 4])
        xykm_data.sni = numpy.array([0, 1, 2, 3, 4])
        xykm_data.nni = numpy.array([0, 1, 2, 3, 4])
        xykm_data.dxi = numpy.array([0, 1, 2, 3, 4])
        xykm_data.dyi = numpy.array([0, 1, 2, 3, 4])
        return xykm_data
    

    def _set_file_name_based_on_number(self):
        self.filenames[0] = ("file1.extension", "file1.extension2")
        self.filenames[1] = ("file2.extension", "file2.extension2")
        self.filenames[2] = ("file3.extension", "file3.extension2")
        
    def _set_file_name_based_on_discharge(self):
        self.filenames[self.initialized_config.discharges[0]] = ("file1.extension", "file1.extension2")
        self.filenames[self.initialized_config.discharges[1]] = ("file2.extension", "file2.extension2")
        self.filenames[self.initialized_config.discharges[2]] = ("file3.extension", "file3.extension2")
        
    def _get_dz_mock_data(self):
        dzgemi = numpy.array([5, 10, 20, 1., 0.])
        dzmaxi = numpy.array([5, 10, 20, 1., 0.])
        dzmini = numpy.array([5, 10, 20, 1., 0.])
        
        dzbi = [numpy.array([5, 10, 20, 1., 0.]),
                numpy.array([25, 30, 35, 1., 0.]),
                numpy.array([40, 45, 50, 1., 0.])]
                
        return dzgemi,dzmaxi,dzmini,dzbi
    
    def assert_report_data(self, dzgemi, dzmaxi, dzmini, dzbi, face_node_connectivity, read_fm_map, xykm_data, sedimentation_data, report_data, zmax_str, zmin_str):
        assert report_data.rsigma == (0.1, 1.0, 0.2, 0.3)
        assert report_data.one_fm_filename == "file2.extension"
        assert report_data.xn is read_fm_map
        assert report_data.face_node_connectivity is face_node_connectivity
        assert report_data.dzq
        assert report_data.dzgemi is dzgemi
        assert report_data.dzmaxi is dzmaxi
        assert report_data.dzmini is dzmini
        assert report_data.dzbi is dzbi
        assert report_data.zmax_str == zmax_str
        assert report_data.zmin_str == zmin_str
        assert report_data.xykm_data is xykm_data
        assert report_data.sedimentation_data is sedimentation_data
    
    def test_analyser_early_return_when_filenames_missing(self, tmp_path, display_needs_tide_old_zmin_zmax : TestCase_display_needs_tide_old_zmin_zmax, setup):       
        outputdir = str(tmp_path)
        self.initialized_config.needs_tide = display_needs_tide_old_zmin_zmax.needs_tide
        
        analyser = AnalyserDflowfm(display_needs_tide_old_zmin_zmax.display, self.report, display_needs_tide_old_zmin_zmax.old_zmin_zmax, outputdir, self.initialized_config)
        report_data = analyser.analyse(self.nwidth, self.filenames, self.xykm, self.plotops)
        
        assert analyser.missing_data
        assert report_data == None
        
    def test_analyser_early_return_when_xykm_missing(self, tmp_path, display_old_zmin_zmax : TestCase_display_old_zmin_zmax, setup):
        self.initialized_config.needs_tide = True
        outputdir = str(tmp_path)
        self._set_file_name_based_on_number()
        
        face_node_connectivity = numpy.array([0, 1, 2, 3, 4])
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_face_node_connectivity', return_value=face_node_connectivity),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data),\
             patch('dfastmi.batch.AnalyserDflowfm.os.path.isfile', return_value=True),\
             patch('dfastmi.batch.AnalyserDflowfm.GridOperations.read_fm_map', return_value=numpy.array([0, 1, 2, 3, 4])):
                 
            analyser = AnalyserDflowfm(display_old_zmin_zmax.display, self.report, display_old_zmin_zmax.old_zmin_zmax, outputdir, self.initialized_config)
            report_data = analyser.analyse(self.nwidth, self.filenames, self.xykm, self.plotops)
            
            assert analyser.missing_data
            assert report_data == None        

    @pytest.mark.parametrize("display", [True, False])
    def test_analyse_without_xykm_and_with_old_zmin_zmax(self, tmp_path, display : bool, setup):
        self.initialized_config.needs_tide = False
        old_zmin_zmax = False
        
        outputdir = str(tmp_path)
        self._set_file_name_based_on_discharge()
        
        dzgemi, dzmaxi, dzmini, dzbi = self._get_dz_mock_data()
        zmax_str="maximum value of bed level change without dredging"
        zmin_str = "minimum value of bed level change without dredging"
        face_node_connectivity = numpy.array([0, 1, 2, 3, 4])
        read_fm_map = numpy.array([0, 1, 2, 3, 4])
        
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        sedimentation_data = None
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_face_node_connectivity', return_value=face_node_connectivity),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data),\
             patch('dfastmi.batch.AnalyserDflowfm.os.path.isfile', return_value=True),\
             patch('dfastmi.batch.AnalyserDflowfm.GridOperations.read_fm_map', return_value=read_fm_map),\
             patch('dfastmi.batch.AnalyserDflowfm.dzq_from_du_and_h') as dzq_from_du_and_h,\
             patch('dfastmi.batch.AnalyserDflowfm.main_computation') as main_computation:
            
            main_computation.return_value = (dzgemi, dzmaxi, dzmini, dzbi)
        
            analyser = AnalyserDflowfm(display, self.report, old_zmin_zmax, outputdir, self.initialized_config)
            report_data = analyser.analyse(self.nwidth, self.filenames, self.xykm, self.plotops)
            
            assert analyser.missing_data == False
            
            self.assert_report_data(dzgemi, dzmaxi, dzmini, dzbi, face_node_connectivity, read_fm_map, xykm_data, sedimentation_data, report_data, zmax_str, zmin_str)
            assert dzq_from_du_and_h.call_count == 3
            assert main_computation.call_count == 1
            
    @pytest.mark.parametrize("display", [True, False])
    def test_analyse_with_xykm_and_with_old_zmin_zmax(self, tmp_path, display : bool, setup):
        self.initialized_config.needs_tide = False
        old_zmin_zmax = True
        
        outputdir = str(tmp_path)
        self._set_file_name_based_on_discharge()
        
        dzgemi, _, _, dzbi = self._get_dz_mock_data()
        dzmaxi = dzbi[0]
        zmax_str = "maximum bed level change after flood without dredging"
        dzmini = dzbi[1]
        zmin_str = "minimum bed level change after low flow without dredging"
        face_node_connectivity = numpy.array([0, 1, 2, 3, 4])
        read_fm_map = numpy.array([0, 1, 2, 3, 4])
        
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        sedimentation_data = None
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_face_node_connectivity', return_value=face_node_connectivity),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data),\
             patch('dfastmi.batch.AnalyserDflowfm.os.path.isfile', return_value=True),\
             patch('dfastmi.batch.AnalyserDflowfm.GridOperations.read_fm_map', return_value=read_fm_map),\
             patch('dfastmi.batch.AnalyserDflowfm.dzq_from_du_and_h') as dzq_from_du_and_h,\
             patch('dfastmi.batch.AnalyserDflowfm.main_computation') as main_computation:
            
            main_computation.return_value = (dzgemi, dzmaxi, dzmini, dzbi)
        
            analyser = AnalyserDflowfm(display, self.report, old_zmin_zmax, outputdir, self.initialized_config)
            report_data = analyser.analyse(self.nwidth, self.filenames, self.xykm, self.plotops)
            
            assert analyser.missing_data == False
            
            self.assert_report_data(dzgemi, dzmaxi, dzmini, dzbi, face_node_connectivity, read_fm_map, xykm_data, sedimentation_data, report_data, zmax_str, zmin_str)
            assert dzq_from_du_and_h.call_count == 3
            assert main_computation.call_count == 1
    
    @pytest.mark.parametrize("display", [True, False])        
    def test_analyse_with_xykm(self, tmp_path, display : bool, setup):
        self.initialized_config.needs_tide = False
        old_zmin_zmax = False
        
        outputdir = str(tmp_path)
        self._set_file_name_based_on_discharge()
        
        dzgemi, dzmaxi, dzmini, dzbi = self._get_dz_mock_data()
        zmax_str="maximum value of bed level change without dredging"
        zmin_str = "minimum value of bed level change without dredging"
        face_node_connectivity = numpy.array([0, 1, 2, 3, 4])
        read_fm_map = numpy.array([0, 1, 2, 3, 4])
        
        self.xykm = Mock(spec=LineString)
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        sedimentation_data = Mock(spec=SedimentationData)
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_face_node_connectivity', return_value=face_node_connectivity),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data),\
             patch('dfastmi.batch.AnalyserDflowfm.os.path.isfile', return_value=True),\
             patch('dfastmi.batch.AnalyserDflowfm.GridOperations.read_fm_map', return_value=read_fm_map),\
             patch('dfastmi.batch.AnalyserDflowfm.dzq_from_du_and_h') as dzq_from_du_and_h,\
             patch('dfastmi.batch.AnalyserDflowfm.main_computation') as main_computation,\
             patch('dfastmi.batch.AnalyserDflowfm.comp_sedimentation_volume', return_value=sedimentation_data):
            
            main_computation.return_value = (dzgemi, dzmaxi, dzmini, dzbi)
        
            analyser = AnalyserDflowfm(display, self.report, old_zmin_zmax, outputdir, self.initialized_config)
            report_data = analyser.analyse(self.nwidth, self.filenames, self.xykm, self.plotops)
            
            assert analyser.missing_data == False
            
            self.assert_report_data(dzgemi, dzmaxi, dzmini, dzbi, face_node_connectivity, read_fm_map, xykm_data, sedimentation_data, report_data, zmax_str, zmin_str)
            assert dzq_from_du_and_h.call_count == 3
            assert main_computation.call_count == 1
