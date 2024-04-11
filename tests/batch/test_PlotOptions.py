from pathlib import Path

import numpy
from mock import ANY, Mock, patch
from shapely.geometry.linestring import LineString

from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.io.DFastAnalysisConfigFileParser import DFastAnalysisConfigFileParser


class Test_PlotOptions:

    def test_PlotOptions_set_plotting_flags_sets_object_data(self, tmp_path):
        plot_options = PlotOptions()
        rootdir = tmp_path
        display = True
        data = Mock(spec=DFastAnalysisConfigFileParser)

        xykm_mock = Mock(spec=LineString)
        xykm_mock.coords = (0, 3)

        mocked_kmzoom = []
        mocked_xyzoom = []

        data.getboolean.return_value = True
        data.getfloat.return_value = 1.0
        data.getstring.side_effect = custom_getstring
        data.get_range.return_value = (0, 0)

        with (
            patch(
                "dfastmi.batch.PlotOptions.DataTextFileOperations.get_xykm"
            ) as get_xykm,
            patch("dfastmi.batch.PlotOptions.ApplicationSettingsHelper.log_text"),
            patch(
                "dfastmi.batch.PlotOptions.numpy.array",
                return_value=numpy.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
            ),
            patch("dfastmi.batch.PlotOptions.get_zoom_extends") as get_zoom_extends,
        ):
            get_xykm.return_value = xykm_mock
            get_zoom_extends.return_value = (mocked_kmzoom, mocked_xyzoom)

            plot_options.set_plotting_flags(rootdir, display, data)
            assert get_xykm.call_count == 1
            assert get_zoom_extends.call_count == 1

        assert plot_options
        assert plot_options.plotting
        assert plot_options.saveplot
        assert plot_options.saveplot_zoomed
        assert plot_options.closeplot
        assert plot_options.figure_save_directory == Path("default_value")
        assert plot_options.plot_extension == ".png"
        assert plot_options.xykm is xykm_mock
        assert plot_options.kmbounds == (0, 0)
        assert plot_options.kmzoom is mocked_kmzoom
        assert plot_options.xyzoom is mocked_xyzoom


def custom_getstring(*args, **kwargs):
    if args == ("General", "RiverKM", ""):
        return "mock_return_value"
    if args == ("General", "FigureExt", ".png"):
        return ".png"
    if args == ("General", "FigureDir", ANY):
        return "default_value"
