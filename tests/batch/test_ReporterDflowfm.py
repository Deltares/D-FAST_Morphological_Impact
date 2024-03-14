import random
from typing import Dict, List, Tuple
from matplotlib import pyplot as plt
from mock import Mock, patch
import numpy
import pytest
from dfastmi.batch.OutputDataDflowfm import OutputDataDflowfm
from dfastmi.batch.ReporterDflowfm import ReporterDflowfm
from dfastmi.batch.XykmData import XykmData


class Test_ReporterDflowfm_Report():
    
    def set_plotting_on(self, tmp_path) -> Dict:
        plotops = {}
        plotops['plotting'] = True
        plotops['saveplot'] = True
        plotops['saveplot_zoomed'] = True
        plotops['figdir'] = str(tmp_path)
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
        rsigma = [0.1, 0.2, 0.3]
        one_fm_filename = str(tmp_path)
        
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
        
        xykm_data = Mock(spec=XykmData)
        xykm_data.iface = numpy.array([0, 1, 2, 3, 4])
        xykm_data.xykm = None
        xykm_data.face_node_connectivity_index.mask.shape = ()
        xykm_data.face_node_connectivity_index.data.shape = numpy.array([1, 1])
        xykm_data.xmin = 1
        xykm_data.ymin = 1
        xykm_data.xmax = 2
        xykm_data.ymax = 2
        xykm_data.xykline = None
        xykm_data.xni = numpy.array([0, 1, 2, 3, 4])
        xykm_data.yni = numpy.array([0, 1, 2, 3, 4])
        
        report_data =  OutputDataDflowfm(rsigma, one_fm_filename, xn, face_node_connectivity, dzq, dzgemi, dzmaxi, dzmini, dzbi, "zmax_str", "zmin_str", xykm_data, None)
        return report_data
    
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
            reporter.report(str(tmp_path), plotops, report_data)
                
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
            reporter.report(str(tmp_path), plotops, report_data)
                
            assert mocked_ugrid_add.call_count == 10
            assert mocked_plotting_plot_overview.call_count == 1
            assert mocked_plotting_zoom_xy_and_save.call_count == 1
            assert mocked_plotting_savefig.call_count == 1