from typing import Any, Dict, TextIO, Tuple
from mock import Mock, patch
from dfastmi.batch.AnalyserDflowfm import AnalyserDflowfm
from shapely.geometry.linestring import LineString
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from dfastmi.kernel.typehints import Vector

import numpy
import shapely
import pytest

class Test_AnalyserDflowfm():
    
    report: TextIO
    q_threshold: float
    tstag: float
    discharges: Vector
    fraction_of_year: Vector
    rsigma: Vector
    slength: float
    nwidth: float
    ucrit: float
    filenames: Dict[Any, Tuple[str,str]]
    xykm: shapely.geometry.linestring.LineString
    n_fields: int
    tide_bc: Tuple[str, ...]
    kmbounds: Tuple[float, float]
    plotops: Dict
    
    @pytest.fixture
    def setup(self):
        self.report = None
        self.q_threshold = 1.0
        self.slength = 1.0
        self.nwidth = 1.0
        self.filenames = {}
        self.xykm = None
        self.n_fields = 3
        self.tide_bc: Tuple[str, ...] = ("name1", "name2")
        self.tstag = 1.0
        self.discharges = [1.0, 2.0, 3.0]
        self.fraction_of_year = [1.0, 2.0, 3.0]
        self.rsigma = [0.1, 0.2, 0.3]
        self.ucrit = 0.3
        self.plotops = None
    
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
        return xykm_data
    

    def _set_file_name_based_on_number(self):
        self.filenames[0] = ("file1.extension", "file1.extension2")
        self.filenames[1] = ("file2.extension", "file2.extension2")
        self.filenames[2] = ("file3.extension", "file3.extension2")
        
    def _set_file_name_based_on_discharge(self):
        self.filenames[self.discharges[0]] = ("file1.extension", "file1.extension2")
        self.filenames[self.discharges[1]] = ("file2.extension", "file2.extension2")
        self.filenames[self.discharges[2]] = ("file3.extension", "file3.extension2")
        
    def _get_dz_mock_data(self):
        dzgemi = numpy.array([5, 10, 20, 1., 0.])
        dzmaxi = numpy.array([5, 10, 20, 1., 0.])
        dzmini = numpy.array([5, 10, 20, 1., 0.])
        
        dzbi = [numpy.array([5, 10, 20, 1., 0.]),
                numpy.array([25, 30, 35, 1., 0.]),
                numpy.array([40, 45, 50, 1., 0.])]
                
        return dzgemi,dzmaxi,dzmini,dzbi
    
    def assert_report_data(self, dzgemi, dzmaxi, dzmini, dzbi, xn_yn_fnc, xykm_data, sedimentation_data, report_data):
        assert report_data.rsigma == (0.1, 1.0, 0.2, 0.3)
        assert report_data.one_fm_filename == "file2.extension"
        assert report_data.xn is xn_yn_fnc[0]
        assert report_data.face_node_connectivity is xn_yn_fnc[2]
        assert report_data.dzq
        assert report_data.dzgemi is dzgemi
        assert report_data.dzmaxi is dzmaxi
        assert report_data.dzmini is dzmini
        assert report_data.dzbi is dzbi
        assert report_data.zmax_str == "maximum value of bed level change without dredging"
        assert report_data.zmin_str == "minimum value of bed level change without dredging"
        assert report_data.xykm_data is xykm_data
        assert report_data.sedimentation_data is sedimentation_data
    
    def test_analyser_early_return(self, tmp_path, setup):
        display = False
        needs_tide = False
        old_zmin_zmax = False
        
        outputdir = str(tmp_path)
        
        analyser = AnalyserDflowfm(display, self.report, needs_tide, old_zmin_zmax, outputdir)
        missing_data, report_data = analyser.analyse(self.q_threshold, self.tstag, self.discharges, self.fraction_of_year, self.rsigma, self.slength, self.nwidth, self.ucrit, self.filenames, self.xykm, self.n_fields, self.tide_bc, self.plotops)
        
        assert missing_data
        assert report_data == None
        
        
    def test_analyser_early_return_when_xykm_missing(self, tmp_path, setup):
        display = True
        needs_tide = True
        old_zmin_zmax = False
        
        outputdir = str(tmp_path)
        self._set_file_name_based_on_number()
        
        xn_yn_fnc = (numpy.array([0, 1, 2, 3, 4]), numpy.array([0, 1, 2, 3, 4]), numpy.array([0, 1, 2, 3, 4]))
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_xynode_connect', return_value=xn_yn_fnc),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data):
                 
            analyser = AnalyserDflowfm(display, self.report, needs_tide, old_zmin_zmax, outputdir)
            missing_data, report_data = analyser.analyse(self.q_threshold, self.tstag, self.discharges, self.fraction_of_year, self.rsigma, self.slength, self.nwidth, self.ucrit, self.filenames, self.xykm, self.n_fields, self.tide_bc, self.plotops)
            
            assert missing_data
            assert report_data == None        
        
    def test_analyse_without_xykm(self, tmp_path, setup):
        display = False
        needs_tide = False
        old_zmin_zmax = False
        
        outputdir = str(tmp_path)
        self._set_file_name_based_on_discharge()
        
        dzgemi, dzmaxi, dzmini, dzbi = self._get_dz_mock_data()
        xn_yn_fnc = (numpy.array([0, 1, 2, 3, 4]), numpy.array([0, 1, 2, 3, 4]), numpy.array([0, 1, 2, 3, 4]))
        
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        sedimentation_data = None
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_xynode_connect', return_value=xn_yn_fnc),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data),\
             patch('dfastmi.batch.AnalyserDflowfm.os.path.isfile', return_value=True),\
             patch('dfastmi.batch.AnalyserDflowfm.GridOperations.read_fm_map', return_value=numpy.array([0, 1, 2, 3, 4])),\
             patch('dfastmi.batch.AnalyserDflowfm.dzq_from_du_and_h') as dzq_from_du_and_h,\
             patch('dfastmi.batch.AnalyserDflowfm.main_computation') as main_computation:
            
            main_computation.return_value = (dzgemi, dzmaxi, dzmini, dzbi)
        
            analyser = AnalyserDflowfm(display, self.report, needs_tide, old_zmin_zmax, outputdir)
            missing_data, report_data = analyser.analyse(self.q_threshold, self.tstag, self.discharges, self.fraction_of_year, self.rsigma, self.slength, self.nwidth, self.ucrit, self.filenames, self.xykm, self.n_fields, self.tide_bc, self.plotops)
            
            assert missing_data == False
            
            self.assert_report_data(dzgemi, dzmaxi, dzmini, dzbi, xn_yn_fnc, xykm_data, sedimentation_data, report_data)
            assert dzq_from_du_and_h.call_count == 3
            assert main_computation.call_count == 1
            
    def test_analyse_with_xykm(self, tmp_path, setup):
        display = True
        needs_tide = False
        old_zmin_zmax = False
        
        outputdir = str(tmp_path)
        self._set_file_name_based_on_discharge()
        
        dzgemi, dzmaxi, dzmini, dzbi = self._get_dz_mock_data()
        xn_yn_fnc = (numpy.array([0, 1, 2, 3, 4]), numpy.array([0, 1, 2, 3, 4]), numpy.array([0, 1, 2, 3, 4]))
        
        self.xykm = Mock(spec=LineString)
        xykm_data = self._get_mocked_xykm_data(self.xykm)
        sedimentation_data = Mock(spec=SedimentationData)
        
        with patch('dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_xynode_connect', return_value=xn_yn_fnc),\
             patch('dfastmi.batch.AnalyserDflowfm.XykmData', return_value =xykm_data),\
             patch('dfastmi.batch.AnalyserDflowfm.os.path.isfile', return_value=True),\
             patch('dfastmi.batch.AnalyserDflowfm.GridOperations.read_fm_map', return_value=numpy.array([0, 1, 2, 3, 4])),\
             patch('dfastmi.batch.AnalyserDflowfm.dzq_from_du_and_h') as dzq_from_du_and_h,\
             patch('dfastmi.batch.AnalyserDflowfm.main_computation') as main_computation,\
             patch('dfastmi.batch.AnalyserDflowfm.comp_sedimentation_volume', return_value=sedimentation_data):
            
            main_computation.return_value = (dzgemi, dzmaxi, dzmini, dzbi)
        
            analyser = AnalyserDflowfm(display, self.report, needs_tide, old_zmin_zmax, outputdir)
            missing_data, report_data = analyser.analyse(self.q_threshold, self.tstag, self.discharges, self.fraction_of_year, self.rsigma, self.slength, self.nwidth, self.ucrit, self.filenames, self.xykm, self.n_fields, self.tide_bc, self.plotops)
            
            assert missing_data == False
            
            self.assert_report_data(dzgemi, dzmaxi, dzmini, dzbi, xn_yn_fnc, xykm_data, sedimentation_data, report_data)
            assert dzq_from_du_and_h.call_count == 3
            assert main_computation.call_count == 1
