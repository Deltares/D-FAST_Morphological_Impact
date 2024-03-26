from pathlib import Path
from mock import Mock, patch
import numpy
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.io.DFastMIConfigParser import DFastMIConfigParser
from shapely.geometry.linestring import LineString


class Test_PlotOptions():
    
    def test_PlotOptions_set_plotting_flags_sets_object_data(self):
        plot_options = PlotOptions()
        rootdir = ""
        display = True
        data = Mock(spec=DFastMIConfigParser)
        
        xykm_mock = Mock(spec=LineString)
        xykm_mock.coords = (0,3)
        
        mocked_kmzoom = []
        mocked_xyzoom = []
        
        data.config_get.side_effect = custom_config_get
        data.config_get_range.return_value = (0,0)
        
        with patch('dfastmi.batch.PlotOptions.DataTextFileOperations.get_xykm') as get_xykm,\
             patch('dfastmi.batch.PlotOptions.ApplicationSettingsHelper.log_text') as log_text,\
             patch('dfastmi.batch.PlotOptions.numpy.array', return_value=numpy.array([[1, 2, 3],[4, 5, 6],[7, 8, 9]])),\
             patch('dfastmi.batch.PlotOptions.get_zoom_extends') as get_zoom_extends:
            get_xykm.return_value = xykm_mock
            get_zoom_extends.return_value = (mocked_kmzoom, mocked_xyzoom)
            
            plot_options.set_plotting_flags(rootdir, display, data)
            assert get_xykm.call_count == 1
            assert get_zoom_extends.call_count == 1
            assert log_text.call_count == 3
            
        assert plot_options
        assert plot_options.plotting
        assert plot_options.saveplot
        assert plot_options.saveplot_zoomed
        assert plot_options.closeplot
        assert plot_options.figure_save_directory == Path('default_value')
        assert plot_options.plot_extension == ".png"
        assert plot_options.xykm is xykm_mock
        assert plot_options.kmbounds == (0,0)
        assert plot_options.kmzoom is mocked_kmzoom
        assert plot_options.xyzoom is mocked_xyzoom
    
def custom_config_get(*args, **kwargs):
    # Check if the arguments match the expected values
    if args == (str, "General", "RiverKM", ""):
        return "mock_return_value"
    if args == (bool, "General", "Plotting", False):
        return True
    if args == (bool, "General", "SavePlots", True):
        return True
    if args == (bool, "General", "SaveZoomPlots", False):
        return True
    if args == (float, "General", "ZoomStepKM", 1.0):
        return 1.0
    if args == (bool, "General", "ClosePlots", False):
        return True
    if args == (str, "General", "FigureExt", ".png"):
        return ".png"
    else:
        # Handle other cases if needed
        return "default_value"