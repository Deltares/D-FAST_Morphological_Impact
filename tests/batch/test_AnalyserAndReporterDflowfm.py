import os
import random
from ast import List
from typing import Any, Dict, TextIO, Tuple
from unittest.mock import patch

import numpy
import pytest
import shapely
from matplotlib import pyplot as plt
from mock import Mock

from dfastmi.batch import AnalyserAndReporterDflowfm
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.batch.SedimentationData import SedimentationData
from dfastmi.batch.XykmData import XykmData
from dfastmi.config.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
from dfastmi.io.MapFile import MapFile
from dfastmi.kernel.typehints import Vector
from tests.batch.Helper_AnalyserAndReporterDflowfm import (  # needed for fixture
    TestCase_display_needs_tide_old_zmin_zmax,
    TestCase_display_old_zmin_zmax,
    TestCase_needs_tide_old_zmin_zmax,
    display_needs_tide_old_zmin_zmax,
    display_old_zmin_zmax,
    needs_tide_old_zmin_zmax,
)


class Test_analyse_and_report_dflowfm_mode:

    report: TextIO
    nwidth: float
    filenames: Dict[Any, Tuple[str, str]]
    xykm: shapely.geometry.linestring.LineString
    plotting_options: PlotOptions
    initialized_config: AConfigurationInitializerBase
    xykm: shapely.geometry.linestring.LineString

    @pytest.fixture
    def setup(self):
        self.report = None
        self.normal_width = 1.0
        self.filenames = {}
        self.xykm = None
        self.plotting_options = Mock(spec=PlotOptions)

        initialized_config = Mock(spec=AConfigurationInitializerBase)
        initialized_config.q_threshold = 1.0
        initialized_config.tstag = 1.0
        initialized_config.discharges = [1.0, 2.0, 3.0]
        initialized_config.time_fractions_of_the_year = [1.0, 2.0, 3.0]
        initialized_config.rsigma = [0.1, 0.2, 0.3]
        initialized_config.slength = 1.0
        initialized_config.n_fields = 3
        initialized_config.tide_bc: Tuple[str, ...] = ("name1", "name2")
        initialized_config.ucrit = 0.3
        self.initialized_config = initialized_config

    def set_file_names(self):
        self.filenames[0] = ("intervention-Q1_map.nc", "intervention-Q1_map.nc")
        self.filenames[1] = ("intervention-Q2_map.nc", "intervention-Q2_map.nc")
        self.filenames[2] = ("intervention-Q3_map.nc", "intervention-Q3_map.nc")

    def set_plotting_on(self, tmp_path):
        self.plotting_options.plotting = True
        self.plotting_options.saveplot = True
        self.plotting_options.saveplot_zoomed = True
        self.plotting_options.figure_save_directory = tmp_path
        self.plotting_options.plot_extension = ".png"

        random_list: List[Tuple[float, float, float, float]] = [
            (
                random.uniform(0.0, 100.0),
                random.uniform(0.0, 100.0),
                random.uniform(0.0, 100.0),
                random.uniform(0.0, 100.0),
            )
        ]

        self.plotting_options.xyzoom = random_list

    def set_plotting_off(self):
        self.plotting_options.plotting = False

    def _get_mocked_mapfile(self, read_face_variable):
        map_file = Mock(spec=MapFile)
        map_file.node_x_coordinates = read_face_variable
        map_file.node_y_coordinates = read_face_variable
        map_file.x_velocity.return_value = read_face_variable
        map_file.y_velocity.return_value = read_face_variable
        map_file.water_depth.return_value = read_face_variable
        return map_file

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

    def given_no_file_names_when_analyse_and_report_dflowfm_then_return_true(
        self,
        tmp_path,
        display_needs_tide_old_zmin_zmax: TestCase_display_needs_tide_old_zmin_zmax,
        setup,
    ):
        """
        given : no file names
        when  : analyse and report dflowfm
        then  : return true
        """
        self.initialized_config.needs_tide = display_needs_tide_old_zmin_zmax.needs_tide
        outputdir = tmp_path

        succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
            display_needs_tide_old_zmin_zmax.display,
            self.report,
            self.normal_width,
            self.filenames,
            self.xykm,
            display_needs_tide_old_zmin_zmax.old_zmin_zmax,
            outputdir,
            self.plotting_options,
            self.initialized_config,
        )

        assert succes

    def given_file_names_based_on_string_when_analyse_and_report_dflowfm_then_return_true(
        self,
        tmp_path,
        display_needs_tide_old_zmin_zmax: TestCase_display_needs_tide_old_zmin_zmax,
        setup,
    ):
        """
        given : file names based on string
        when  : analyse and report dflowfm
        then  : return true
        """
        self.initialized_config.needs_tide = display_needs_tide_old_zmin_zmax.needs_tide
        outputdir = tmp_path

        self.filenames["0"] = ("intervention-Q1_map.nc", "intervention-Q1_map.nc")
        self.filenames["1"] = ("intervention-Q2_map.nc", "intervention-Q2_map.nc")
        self.filenames["2"] = ("intervention-Q3_map.nc", "intervention-Q3_map.nc")

        succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
            display_needs_tide_old_zmin_zmax.display,
            self.report,
            self.normal_width,
            self.filenames,
            self.xykm,
            display_needs_tide_old_zmin_zmax.old_zmin_zmax,
            outputdir,
            self.plotting_options,
            self.initialized_config,
        )

        assert succes

    def given_file_names_based_on_numbers_with_plotting_off_and_needs_tide_false_when_analyse_and_report_dflowfm_then_return_true_and_expect_eleven_grids_added_and_plotting_not_called(
        self, tmp_path, display_old_zmin_zmax: TestCase_display_old_zmin_zmax, setup
    ):
        """
        given : file names based on numbers with plotting off and needs tide false
        when  : analyse and report dflowfm
        then  : return true and expect eleven grids added and plotting not called
        """
        self.initialized_config.needs_tide = False
        self.initialized_config.n_fields = 1

        outputdir = tmp_path

        self.set_plotting_off()

        self.set_file_names()

        face_node_connectivity = numpy.array([0, 1, 2, 3, 4])
        mocked_mapfile = self._get_mocked_mapfile(face_node_connectivity)

        xykm_data = self._get_mocked_xykm_data(self.xykm)

        with (
            patch("dfastmi.batch.ReporterDflowfm.MapFile", return_value=mocked_mapfile),
            patch(
                "dfastmi.batch.AnalyserDflowfm.OutputFileFactory.generate",
                return_value=mocked_mapfile,
            ),
            patch(
                "dfastmi.batch.AnalyserDflowfm.AnalyserDflowfm._get_face_node_connectivity",
                return_value=face_node_connectivity,
            ),
            patch(
                "dfastmi.batch.ReporterDflowfm.plot_overview"
            ) as mocked_plotting_plot_overview,
            patch(
                "dfastmi.batch.ReporterDflowfm.zoom_xy_and_save"
            ) as mocked_plotting_zoom_xy_and_save,
            patch("dfastmi.batch.ReporterDflowfm.savefig") as mocked_plotting_savefig,
            patch("dfastmi.batch.AnalyserDflowfm.XykmData", return_value=xykm_data),
        ):

            mocked_plotting_plot_overview.return_value = (
                plt.figure(figsize=(8, 6)),
                plt.axes(),
            )

            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"

            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display_old_zmin_zmax.display,
                    self.report,
                    self.normal_width,
                    self.filenames,
                    self.xykm,
                    display_old_zmin_zmax.old_zmin_zmax,
                    outputdir,
                    self.plotting_options,
                    self.initialized_config,
                )
            finally:
                os.chdir(cwd)

        assert succes
        assert mocked_plotting_plot_overview.call_count == 0
        assert mocked_plotting_zoom_xy_and_save.call_count == 0
        assert mocked_plotting_savefig.call_count == 0
        assert mocked_mapfile.add_variable.call_count == 11

    def given_file_names_based_on_numbers_with_plotting_off_and_needs_tide_true_when_analyse_and_report_dflowfm_then_return_true_and_expect_zero_grids_added_and_plotting_not_called(
        self, tmp_path, display_old_zmin_zmax: TestCase_display_old_zmin_zmax, setup
    ):
        """
        given : file names based on numbers with plotting off and needs tide true
        when  : analyse and report dflowfm
        then  : return true and expect zero grids added and plotting not called
        """
        self.initialized_config.needs_tide = True
        self.initialized_config.n_fields = 1

        outputdir = tmp_path

        self.set_plotting_off()

        self.set_file_names()

        mocked_mapfile = Mock(spec=MapFile)

        with (
            patch("dfastmi.batch.ReporterDflowfm.MapFile", return_value=mocked_mapfile),
            patch(
                "dfastmi.batch.ReporterDflowfm.plot_overview"
            ) as mocked_plotting_plot_overview,
            patch(
                "dfastmi.batch.ReporterDflowfm.zoom_xy_and_save"
            ) as mocked_plotting_zoom_xy_and_save,
            patch("dfastmi.batch.ReporterDflowfm.savefig") as mocked_plotting_savefig,
        ):

            mocked_plotting_plot_overview.return_value = (
                plt.figure(figsize=(8, 6)),
                plt.axes(),
            )

            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display_old_zmin_zmax.display,
                    self.report,
                    self.normal_width,
                    self.filenames,
                    self.xykm,
                    display_old_zmin_zmax.old_zmin_zmax,
                    outputdir,
                    self.plotting_options,
                    self.initialized_config,
                )
            finally:
                os.chdir(cwd)

        assert succes
        assert mocked_plotting_plot_overview.call_count == 0
        assert mocked_plotting_zoom_xy_and_save.call_count == 0
        assert mocked_plotting_savefig.call_count == 0
        assert mocked_mapfile.add_variable.call_count == 0

    def given_file_names_with_plotting_on_and_needs_tide_false_when_analyse_and_report_dflowfm_then_return_true_and_expect_eleven_grids_added_and_plotting_called(
        self, tmp_path, display_old_zmin_zmax: TestCase_display_old_zmin_zmax, setup
    ):
        """
        given : file names with plotting on and needs tide false
        when  : analyse and report dflowfm
        then  : return true and expect eleven grids added and plotting called
        """
        self.initialized_config.needs_tide = False
        self.initialized_config.n_fields = 1

        outputdir = tmp_path

        self.set_plotting_on(tmp_path)

        self.set_file_names()

        mocked_mapfile = Mock(spec=MapFile)

        with (
            patch("dfastmi.batch.ReporterDflowfm.MapFile", return_value=mocked_mapfile),
            patch(
                "dfastmi.batch.ReporterDflowfm.plot_overview"
            ) as mocked_plotting_plot_overview,
            patch(
                "dfastmi.batch.ReporterDflowfm.zoom_xy_and_save"
            ) as mocked_plotting_zoom_xy_and_save,
            patch("dfastmi.batch.ReporterDflowfm.savefig") as mocked_plotting_savefig,
        ):

            mocked_plotting_plot_overview.return_value = (
                plt.figure(figsize=(8, 6)),
                plt.axes(),
            )

            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display_old_zmin_zmax.display,
                    self.report,
                    self.normal_width,
                    self.filenames,
                    self.xykm,
                    display_old_zmin_zmax.old_zmin_zmax,
                    outputdir,
                    self.plotting_options,
                    self.initialized_config,
                )
            finally:
                os.chdir(cwd)

        assert succes
        assert mocked_plotting_plot_overview.call_count == 1
        assert mocked_plotting_zoom_xy_and_save.call_count == 1
        assert mocked_plotting_savefig.call_count == 1
        assert mocked_mapfile.add_variable.call_count == 11

    def given_file_names_with_plotting_on_and_needs_tide_true_when_analyse_and_report_dflowfm_then_return_true_and_expect_zero_grids_added_and_plotting_not_called(
        self, tmp_path, display_old_zmin_zmax: TestCase_display_old_zmin_zmax, setup
    ):
        """
        given : file names with plotting on and needs tide false
        when  : analyse and report dflowfm
        then  : return true and expect zero grids added and plotting not called
        """
        self.initialized_config.needs_tide = True
        self.initialized_config.n_fields = 1

        outputdir = tmp_path

        self.set_plotting_on(tmp_path)

        self.set_file_names()

        mocked_mapfile = Mock(spec=MapFile)

        with (
            patch("dfastmi.batch.ReporterDflowfm.MapFile", return_value=mocked_mapfile),
            patch(
                "dfastmi.batch.ReporterDflowfm.plot_overview"
            ) as mocked_plotting_plot_overview,
            patch(
                "dfastmi.batch.ReporterDflowfm.zoom_xy_and_save"
            ) as mocked_plotting_zoom_xy_and_save,
            patch("dfastmi.batch.ReporterDflowfm.savefig") as mocked_plotting_savefig,
        ):

            mocked_plotting_plot_overview.return_value = (
                plt.figure(figsize=(8, 6)),
                plt.axes(),
            )

            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display_old_zmin_zmax.display,
                    self.report,
                    self.normal_width,
                    self.filenames,
                    self.xykm,
                    display_old_zmin_zmax.old_zmin_zmax,
                    outputdir,
                    self.plotting_options,
                    self.initialized_config,
                )
            finally:
                os.chdir(cwd)

        assert succes
        assert mocked_plotting_plot_overview.call_count == 0
        assert mocked_plotting_zoom_xy_and_save.call_count == 0
        assert mocked_plotting_savefig.call_count == 0
        assert mocked_mapfile.add_variable.call_count == 0

    def given_xykm_and_no_display_when_analyse_and_report_dflowfm_then_return_true_and_expect_sixteen_grids_added_and_plotting_called(
        self,
        tmp_path,
        needs_tide_old_zmin_zmax: TestCase_needs_tide_old_zmin_zmax,
        setup,
    ):
        """
        given : xykm and no display
        when  : analyse and report dflowfm
        then  : return true and expect sixteen grids addedand plotting called
        """
        outputdir = tmp_path

        self.initialized_config.n_fields = 1
        self.initialized_config.needs_tide = needs_tide_old_zmin_zmax.needs_tide

        self.set_plotting_on(tmp_path)

        self.set_file_names()

        mocked_mapfile = Mock(spec=MapFile)

        # _replace_coordinates_in_destination_file is mocked in regard to the access to netCDF4 file.
        with (
            patch("dfastmi.batch.ReporterDflowfm.MapFile", return_value=mocked_mapfile),
            patch(
                "dfastmi.batch.ReporterDflowfm.ReporterDflowfm._replace_coordinates_in_destination_file"
            ) as mocked_internal_method,
            patch(
                "dfastmi.batch.ReporterDflowfm.plot_overview"
            ) as mocked_plotting_plot_overview,
            patch(
                "dfastmi.batch.ReporterDflowfm.zoom_xy_and_save"
            ) as mocked_plotting_zoom_xy_and_save,
            patch("dfastmi.batch.ReporterDflowfm.savefig") as mocked_plotting_savefig,
            patch(
                "dfastmi.batch.AnalyserDflowfm.comp_sedimentation_volume"
            ) as mocked_comp_sedimentation_volume,
        ):

            mocked_plotting_plot_overview.return_value = (
                plt.figure(figsize=(8, 6)),
                plt.axes(),
            )
            mocked_comp_sedimentation_volume.return_value = SedimentationData(
                None, None, [], None, None, [], numpy.zeros(0), numpy.zeros(0)
            )

            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)

                testing_working_dir = os.getcwd()
                kmfile = testing_working_dir + "\\..\\files\\read_xyc_test.xyc"
                self.xykm = DataTextFileOperations.get_xykm(kmfile)

                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    False,
                    self.report,
                    self.normal_width,
                    self.filenames,
                    self.xykm,
                    needs_tide_old_zmin_zmax.old_zmin_zmax,
                    outputdir,
                    self.plotting_options,
                    self.initialized_config,
                )
            finally:
                os.chdir(cwd)

        assert succes
        assert mocked_plotting_plot_overview.call_count == 1
        assert mocked_plotting_zoom_xy_and_save.call_count == 1
        assert mocked_plotting_savefig.call_count == 1
        assert mocked_internal_method.call_count == 1
        assert mocked_mapfile.add_variable.call_count == 16
