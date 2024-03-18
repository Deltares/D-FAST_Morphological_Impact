import random
from typing import Dict, List, Tuple
from matplotlib import pyplot as plt
from mock import Mock, patch
import numpy
import pytest
from dfastmi.batch.DflowfmLoggers import ReporterDflowfmLogger
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm
from dfastmi.batch.ReporterDflowfm import ReporterDflowfm
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from shapely.geometry.linestring import LineString

class Test_ReporterDflowfm_Report():
    
    def set_plotting_on(self, tmp_path) -> Dict:
        plotops = {}
        plotops['plotting'] = True
        plotops['saveplot'] = True
        plotops['saveplot_zoomed'] = True
        plotops['figdir'] = tmp_path
        plotops['plot_ext'] = "plot_ext"
        
        random_list: List[Tuple[float, float, float, float]] = [
            (random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0))]
        
        plotops['xyzoom'] = random_list
        return plotops
    
    def set_plotting_off(self) -> Dict:
        plotops = {}
        plotops['plotting'] = False
        return plotops

    def set_report_data_without_xykm(self, tmp_path):
        return self._get_report_data(tmp_path, False)
    
    def set_report_data_with_xykm(self, tmp_path):
        return self._get_report_data(tmp_path, True)
    
    def _get_report_data(self, tmp_path, enable_xykm):
        rsigma = [0.1, 0.2, 0.3]
        one_fm_filename = tmp_path
        
        xn = numpy.array([5, 10, 20, 1., 0.])
        face_node_connectivity = numpy.array([5, 10, 20, 1., 0.])
        
        dzq = [numpy.array([5, 10, 20, 1., 0.]),
                numpy.array([25, 30, 35, 1., 0.]),
                numpy.array([40, 45, 50, 1., 0.])]
        
        dzgemi = numpy.array([5, 10, 20, 1., 0.])
        dzmaxi = numpy.array([5, 10, 20, 1., 0.])
        dzmini = numpy.array([5, 10, 20, 1., 0.])
        
        dzbi = [numpy.array([5, 10, 20, 1., 0.]),
                numpy.array([25, 30, 35, 1., 0.]),
                numpy.array([40, 45, 50, 1., 0.])]
        
        xykm_data = self._get_mocked_xykm_data(enable_xykm)
        sedimentation_data = self._get_sedimentation_mocked_data()
        
        report_data =  OutputDataDflowfm(rsigma, one_fm_filename, xn, face_node_connectivity, dzq, dzgemi, dzmaxi, dzmini, dzbi, "zmax_str", "zmin_str", xykm_data, sedimentation_data)
        return report_data

    def _get_sedimentation_mocked_data(self):
        sedimentation_data = Mock(spec=SedimentationData)
        sedimentation_data.sedarea = numpy.array([0, 1, 2, 3, 4])
        sedimentation_data.sedvol = numpy.array([0, 1, 2, 3, 4])
        sedimentation_data.sed_area_list = [True, True]
        sedimentation_data.eroarea = numpy.array([0, 1, 2, 3, 4])
        sedimentation_data.erovol = numpy.array([0, 1, 2, 3, 4])
        sedimentation_data.ero_area_list = [True, True]
        sedimentation_data.wght_estimate1i = numpy.array([0, 1, 2, 3, 4])
        sedimentation_data.wbini = numpy.array([0, 1, 2, 3, 4])
        return sedimentation_data

    def _get_mocked_xykm_data(self, enable_xykm):
        if enable_xykm:
            xykm = LineString()
        else:
            xykm = None
        
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
    
    @pytest.mark.parametrize("display", [True, False])
    def test_report_without_xykm_without_plotting(self, tmp_path, display):
        plotops = self.set_plotting_off()
        report_data = self.set_report_data_without_xykm(tmp_path)
        
        with patch('dfastmi.batch.ReporterDflowfm.GridOperations.get_mesh_and_facedim_names', return_value=("filename1.ext", "filename2.ext")), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.copy_ugrid'), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.ReporterDflowfm.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.ReporterDflowfm.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.ReporterDflowfm.savefig') as mocked_plotting_savefig:
        
            reporter = ReporterDflowfm(display)
            reporter.report(tmp_path, plotops, report_data)
                
            assert mocked_ugrid_add.call_count == 10
            assert mocked_plotting_plot_overview.call_count == 0
            assert mocked_plotting_zoom_xy_and_save.call_count == 0
            assert mocked_plotting_savefig.call_count == 0
        
    @pytest.mark.parametrize("display", [True, False])
    def test_report_without_xykm_with_plotting(self, tmp_path, display):
        plotops = self.set_plotting_on(tmp_path)
        report_data = self.set_report_data_without_xykm(tmp_path)
        
        with patch('dfastmi.batch.ReporterDflowfm.GridOperations.get_mesh_and_facedim_names', return_value=("filename1.ext", "filename2.ext")), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.copy_ugrid'), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.ReporterDflowfm.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.ReporterDflowfm.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.ReporterDflowfm.savefig') as mocked_plotting_savefig:
                 
            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
        
            reporter = ReporterDflowfm(display)
            reporter.report(tmp_path, plotops, report_data)
                
            assert mocked_ugrid_add.call_count == 10
            assert mocked_plotting_plot_overview.call_count == 1
            assert mocked_plotting_zoom_xy_and_save.call_count == 1
            assert mocked_plotting_savefig.call_count == 1
    
    @pytest.mark.parametrize("display", [True, False])
    def test_report_with_xykm_without_plotting(self, tmp_path, display):
        plotops = self.set_plotting_off()
        report_data = self.set_report_data_with_xykm(tmp_path)
        
        # private method _replace_coordinates_in_destination_file is mocked because it tries to access netCDF4 file and this test is no data access, thus this called is mocked.
        with patch('dfastmi.batch.ReporterDflowfm.GridOperations.get_mesh_and_facedim_names', return_value=("filename1.ext", "filename2.ext")), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.copy_ugrid'), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.ReporterDflowfm.ReporterDflowfm._replace_coordinates_in_destination_file'), \
             patch('dfastmi.batch.ReporterDflowfm.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.ReporterDflowfm.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.ReporterDflowfm.savefig') as mocked_plotting_savefig:
        
            reporter = ReporterDflowfm(display)
            reporter._logger = Mock(spec=ReporterDflowfmLogger)
            reporter.report(tmp_path, plotops, report_data)
                
            assert mocked_ugrid_add.call_count == 15
            assert mocked_plotting_plot_overview.call_count == 0
            assert mocked_plotting_zoom_xy_and_save.call_count == 0
            assert mocked_plotting_savefig.call_count == 0
            
    @pytest.mark.parametrize("display", [True, False])
    def test_report_with_xykm_with_plotting(self, tmp_path, display):
        plotops = self.set_plotting_on(tmp_path)
        report_data = self.set_report_data_with_xykm(tmp_path)
        
        # private method _replace_coordinates_in_destination_file is mocked because it tries to access netCDF4 file and this test is no data access, thus this called is mocked.
        with patch('dfastmi.batch.ReporterDflowfm.GridOperations.get_mesh_and_facedim_names', return_value=("filename1.ext", "filename2.ext")), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.copy_ugrid'), \
             patch('dfastmi.batch.ReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.ReporterDflowfm.ReporterDflowfm._replace_coordinates_in_destination_file'), \
             patch('dfastmi.batch.ReporterDflowfm.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.ReporterDflowfm.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.ReporterDflowfm.savefig') as mocked_plotting_savefig:
        
            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
            
            reporter = ReporterDflowfm(display)
            reporter._logger = Mock(spec=ReporterDflowfmLogger)
            reporter.report(tmp_path, plotops, report_data)
                
            assert mocked_ugrid_add.call_count == 15
            assert mocked_plotting_plot_overview.call_count == 1
            assert mocked_plotting_zoom_xy_and_save.call_count == 1
            assert mocked_plotting_savefig.call_count == 1