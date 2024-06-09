from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

import numpy
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from dfastmi.batch.AreaDetector import AreaData
from dfastmi.batch.AreaPlotter import ErosionAreaPlotter, SedimentationAreaPlotter
from dfastmi.batch.PlotOptions import PlotOptions


def plotting_off():
    plotting_options = Mock(spec=PlotOptions)
    plotting_options.plotting = False
    return plotting_options


def mock_area_data():
    area_data = Mock(spec=AreaData)
    area_data.volume = numpy.array(
        [
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            [[10, 11, 12], [13, 14, 15], [16, 17, 18]],
            [[19, 20, 21], [22, 23, 24], [25, 26, 27]],
            [[28, 29, 30], [31, 32, 33], [34, 35, 36]],
        ]
    )
    area_data.area_list = [True, True, True]
    return area_data


def plotting_on(tmp_path):
    plotting_options = Mock(spec=PlotOptions)
    plotting_options.plotting = True
    plotting_options.saveplot = True
    plotting_options.saveplot_zoomed = True
    plotting_options.figure_save_directory = Path(tmp_path)
    plotting_options.plot_extension = ".png"
    plotting_options.kmzoom = []
    return plotting_options


class Test_SedimentationAreaPlotter:

    dzgemi: numpy.ndarray
    areai: numpy.ndarray
    wbin: numpy.ndarray
    wbin_labels: list[str]
    wthresh: numpy.ndarray
    siface: numpy.ndarray
    afrac: numpy.ndarray
    sbin: numpy.ndarray
    sthresh: numpy.ndarray
    kmid: numpy.ndarray
    binvol: List[numpy.ndarray]

    @pytest.fixture
    def setup(self):
        self.dzgemi: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.areai: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.wbin: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.wbin_labels: list[str] = ["1", "2", "3"]
        self.wthresh: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.siface: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.afrac: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.sbin: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.sthresh: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.kmid: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.binvol = []
        self.binvol.append(numpy.array([0, 1, 2, 3, 4]))
        self.binvol.append(numpy.array([0, 1, 2, 3, 4]))
        self.binvol.append(numpy.array([0, 1, 2, 3, 4]))

    def test_init_sets_protected_variables(self, tmp_path):
        plotting_options = plotting_on(tmp_path)
        area_data = mock_area_data()
        plot_n = 3

        plotter = SedimentationAreaPlotter(plotting_options, plot_n, area_data)

        assert plotter._template_graph_title_of_the_sub_areas == "sedimentation area {}"
        assert plotter._graph_title_of_the_total_area == "total sedimentation volume"
        assert plotter._positive_up

    def test_plot_areas_with_plotting_plots_areas(self, setup, tmp_path: Path):
        plotting_options = plotting_on(tmp_path)
        area_data = mock_area_data()
        plot_n = 3

        expected_amount_of_sedimentation_calls = 10
        expected_amount_of_zoom_x_and_save_calls = 10
        expected_amount_of_savefig_calls = 10

        plotter = SedimentationAreaPlotter(plotting_options, plot_n, area_data)

        with (
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.plot_sedimentation"
            ) as plot_sedimentation,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.zoom_x_and_save"
            ) as zoom_x_and_save,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.savefig"
            ) as savefig,
        ):
            plot_sedimentation.return_value = (Mock(spec=Figure), Mock(spec=Axes))

            plotter.plot_areas(
                self.dzgemi,
                self.areai,
                self.wbin,
                self.wbin_labels,
                self.wthresh,
                self.siface,
                self.afrac,
                self.sbin,
                self.sthresh,
                self.kmid,
                self.binvol,
            )

            assert (
                plot_sedimentation.call_count == expected_amount_of_sedimentation_calls
            )
            assert (
                zoom_x_and_save.call_count == expected_amount_of_zoom_x_and_save_calls
            )
            assert savefig.call_count == expected_amount_of_savefig_calls

    def test_plot_areas_with_plotting_without_saving_saves_no_plot_areas(
        self, setup, tmp_path: Path
    ):
        plotting_options = plotting_on(tmp_path)
        plotting_options.saveplot = False
        area_data = mock_area_data()
        plot_n = 3

        expected_amount_of_sedimentation_calls = 10
        expected_amount_of_zoom_x_and_save_calls = 0
        expected_amount_of_savefig_calls = 0

        plotter = SedimentationAreaPlotter(plotting_options, plot_n, area_data)

        with (
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.plot_sedimentation"
            ) as plot_sedimentation,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.zoom_x_and_save"
            ) as zoom_x_and_save,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.savefig"
            ) as savefig,
        ):
            plot_sedimentation.return_value = (Mock(spec=Figure), Mock(spec=Axes))

            plotter.plot_areas(
                self.dzgemi,
                self.areai,
                self.wbin,
                self.wbin_labels,
                self.wthresh,
                self.siface,
                self.afrac,
                self.sbin,
                self.sthresh,
                self.kmid,
                self.binvol,
            )

            assert (
                plot_sedimentation.call_count == expected_amount_of_sedimentation_calls
            )
            assert (
                zoom_x_and_save.call_count == expected_amount_of_zoom_x_and_save_calls
            )
            assert savefig.call_count == expected_amount_of_savefig_calls

    def test_plot_areas_without_plotting_plot_no_areas(self, setup):
        plotting_options = plotting_off()
        area_data = mock_area_data()
        plot_n = 3

        expected_amount_of_sedimentation_calls = 0
        expected_amount_of_zoom_x_and_save_calls = 0
        expected_amount_of_savefig_calls = 0

        plotter = SedimentationAreaPlotter(plotting_options, plot_n, area_data)

        with (
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.plot_sedimentation"
            ) as plot_sedimentation,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.zoom_x_and_save"
            ) as zoom_x_and_save,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.savefig"
            ) as savefig,
        ):
            plot_sedimentation.return_value = (Mock(spec=Figure), Mock(spec=Axes))

            plotter.plot_areas(
                self.dzgemi,
                self.areai,
                self.wbin,
                self.wbin_labels,
                self.wthresh,
                self.siface,
                self.afrac,
                self.sbin,
                self.sthresh,
                self.kmid,
                self.binvol,
            )

            assert (
                plot_sedimentation.call_count == expected_amount_of_sedimentation_calls
            )
            assert (
                zoom_x_and_save.call_count == expected_amount_of_zoom_x_and_save_calls
            )
            assert savefig.call_count == expected_amount_of_savefig_calls


class Test_ErosionAreaPlotter:

    dzgemi: numpy.ndarray
    areai: numpy.ndarray
    wbin: numpy.ndarray
    wbin_labels: list[str]
    wthresh: numpy.ndarray
    siface: numpy.ndarray
    afrac: numpy.ndarray
    sbin: numpy.ndarray
    sthresh: numpy.ndarray
    kmid: numpy.ndarray
    binvol: List[numpy.ndarray]

    @pytest.fixture
    def setup(self):
        self.dzgemi: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.areai: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.wbin: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.wbin_labels: list[str] = ["1", "2", "3"]
        self.wthresh: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.siface: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.afrac: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.sbin: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.sthresh: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.kmid: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])
        self.binvol = []
        self.binvol.append(numpy.array([0, 1, 2, 3, 4]))
        self.binvol.append(numpy.array([0, 1, 2, 3, 4]))
        self.binvol.append(numpy.array([0, 1, 2, 3, 4]))

    def test_init_sets_protected_variables(self, tmp_path):
        plotting_options = plotting_on(tmp_path)
        area_data = mock_area_data()
        plot_n = 3

        plotter = ErosionAreaPlotter(plotting_options, plot_n, area_data)

        assert plotter._template_graph_title_of_the_sub_areas == "erosion area {}"
        assert plotter._graph_title_of_the_total_area == "total erosion volume"
        assert not plotter._positive_up

    def test_plot_areas_with_plotting_plots_areas(self, setup, tmp_path: Path):
        plotting_options = plotting_on(tmp_path)
        area_data = mock_area_data()
        plot_n = 3

        expected_amount_of_sedimentation_calls = 10
        expected_amount_of_zoom_x_and_save_calls = 10
        expected_amount_of_savefig_calls = 10

        plotter = ErosionAreaPlotter(plotting_options, plot_n, area_data)

        with (
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.plot_sedimentation"
            ) as plot_sedimentation,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.zoom_x_and_save"
            ) as zoom_x_and_save,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.savefig"
            ) as savefig,
        ):
            plot_sedimentation.return_value = (Mock(spec=Figure), Mock(spec=Axes))

            plotter.plot_areas(
                self.dzgemi,
                self.areai,
                self.wbin,
                self.wbin_labels,
                self.wthresh,
                self.siface,
                self.afrac,
                self.sbin,
                self.sthresh,
                self.kmid,
                self.binvol,
            )

            assert (
                plot_sedimentation.call_count == expected_amount_of_sedimentation_calls
            )
            assert (
                zoom_x_and_save.call_count == expected_amount_of_zoom_x_and_save_calls
            )
            assert savefig.call_count == expected_amount_of_savefig_calls

    def test_plot_areas_with_plotting_without_saving_saves_no_plot_areas(
        self, setup, tmp_path: Path
    ):
        plotting_options = plotting_on(tmp_path)
        plotting_options.saveplot = False
        area_data = mock_area_data()
        plot_n = 3

        expected_amount_of_sedimentation_calls = 10
        expected_amount_of_zoom_x_and_save_calls = 0
        expected_amount_of_savefig_calls = 0

        plotter = SedimentationAreaPlotter(plotting_options, plot_n, area_data)

        with (
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.plot_sedimentation"
            ) as plot_sedimentation,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.zoom_x_and_save"
            ) as zoom_x_and_save,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.savefig"
            ) as savefig,
        ):
            plot_sedimentation.return_value = (Mock(spec=Figure), Mock(spec=Axes))

            plotter.plot_areas(
                self.dzgemi,
                self.areai,
                self.wbin,
                self.wbin_labels,
                self.wthresh,
                self.siface,
                self.afrac,
                self.sbin,
                self.sthresh,
                self.kmid,
                self.binvol,
            )

            assert (
                plot_sedimentation.call_count == expected_amount_of_sedimentation_calls
            )
            assert (
                zoom_x_and_save.call_count == expected_amount_of_zoom_x_and_save_calls
            )
            assert savefig.call_count == expected_amount_of_savefig_calls

    def test_plot_areas_without_plotting_plot_no_areas(self, setup):
        plotting_options = plotting_off()
        area_data = mock_area_data()
        plot_n = 3

        expected_amount_of_sedimentation_calls = 0
        expected_amount_of_zoom_x_and_save_calls = 0
        expected_amount_of_savefig_calls = 0

        plotter = SedimentationAreaPlotter(plotting_options, plot_n, area_data)

        with (
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.plot_sedimentation"
            ) as plot_sedimentation,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.zoom_x_and_save"
            ) as zoom_x_and_save,
            patch(
                "dfastmi.batch.AreaPlotter.dfastmi.batch.plotting.savefig"
            ) as savefig,
        ):
            plot_sedimentation.return_value = (Mock(spec=Figure), Mock(spec=Axes))

            plotter.plot_areas(
                self.dzgemi,
                self.areai,
                self.wbin,
                self.wbin_labels,
                self.wthresh,
                self.siface,
                self.afrac,
                self.sbin,
                self.sthresh,
                self.kmid,
                self.binvol,
            )

            assert (
                plot_sedimentation.call_count == expected_amount_of_sedimentation_calls
            )
            assert (
                zoom_x_and_save.call_count == expected_amount_of_zoom_x_and_save_calls
            )
            assert savefig.call_count == expected_amount_of_savefig_calls
