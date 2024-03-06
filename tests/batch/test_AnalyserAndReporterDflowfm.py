from ast import List
import os
import random
from typing import Any, Dict, TextIO, Tuple
from unittest.mock import patch
from matplotlib import pyplot as plt
import numpy
import pytest
import shapely
from dfastmi.batch import AnalyserAndReporterDflowfm
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations
from dfastmi.kernel.typehints import Vector

class Test_analyse_and_report_dflowfm_mode():

    report: TextIO
    q_threshold: float
    tstag: float
    Q: Vector
    T: Vector
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
        self.kmbounds : Tuple[float, float] = (1.0, 2.0)
        self.plotops = {}
        self.tstag = 1.0
        self.Q = [1.0, 2.0, 3.0]
        self.T = [1.0, 2.0, 3.0]
        self.rsigma = [0.1, 0.2, 0.3]
        self.ucrit = 0.3
        
    
    @pytest.mark.parametrize("display, needs_tide, old_zmin_zmax", [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (True, True, True),
        (False, True, False),
        (False, True, True),
        (False, False, True),
        (True, False, True),
    ])   
    def given_no_file_names_when_analyse_and_report_dflowfm_then_return_true(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool, setup):
        """
        given : no file names
        when  : analyse and report dflowfm
        then  : return true
        """
        outputdir = str(tmp_path)

        succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                display,
                self.report,
                self.q_threshold,
                self.tstag,
                self.Q,
                self.T,
                self.rsigma,
                self.slength,
                self.nwidth,
                self.ucrit,
                self.filenames,
                self.xykm,
                needs_tide,
                self.n_fields,
                self.tide_bc,
                old_zmin_zmax,
                self.kmbounds,
                outputdir,
                self.plotops)

        assert succes
        
    @pytest.mark.parametrize("display, needs_tide, old_zmin_zmax", [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (True, True, True),
        (False, True, False),
        (False, True, True),
        (False, False, True),
        (True, False, True),
    ])   
    def given_file_names_based_on_string_when_analyse_and_report_dflowfm_then_return_true(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool, setup):
        """
        given : file names based on string
        when  : analyse and report dflowfm
        then  : return true
        """
        outputdir = str(tmp_path)
        
        self.filenames["0"] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        self.filenames["1"] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        self.filenames["2"] = ("measure-Q3_map.nc", "measure-Q3_map.nc")

        succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                display,
                self.report,
                self.q_threshold,
                self.tstag,
                self.Q,
                self.T,
                self.rsigma,
                self.slength,
                self.nwidth,
                self.ucrit,
                self.filenames,
                self.xykm,
                needs_tide,
                self.n_fields,
                self.tide_bc,
                old_zmin_zmax,
                self.kmbounds,
                outputdir,
                self.plotops)

        assert succes

        
    @pytest.mark.parametrize("display, old_zmin_zmax", [
        (False, False),
        (True,False),
        (True,True),
        (False, True),
    ])   
    def given_file_names_based_on_numbers_with_plotting_off_and_needs_tide_false_when_analyse_and_report_dflowfm_then_return_true_and_expect_eleven_grids_added_and_plotting_not_called(self, tmp_path, display : bool, old_zmin_zmax : bool , setup):        
        """
        given : file names based on numbers with plotting off and needs tide false
        when  : analyse and report dflowfm
        then  : return true and expect eleven grids added and plotting not called
        """
        needs_tide = False
        
        outputdir = str(tmp_path)
        
        self.n_fields = 1
        
        self.plotops['plotting'] = False
        
        self.filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        self.filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        self.filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.comp_sedimentation_volume') as mocked_comp_sedimentation_volume:

            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
            mocked_comp_sedimentation_volume.return_value = (None, None, [], None, None, [], numpy.zeros(2555), numpy.zeros(2555))
            
            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display,
                    self.report,
                    self.q_threshold,
                    self.tstag,
                    self.Q,
                    self.T,
                    self.rsigma,
                    self.slength,
                    self.nwidth,
                    self.ucrit,
                    self.filenames,
                    self.xykm,
                    needs_tide,
                    self.n_fields,
                    self.tide_bc,
                    old_zmin_zmax,
                    self.kmbounds,
                    outputdir,
                    self.plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 0
        assert mocked_plotting_zoom_xy_and_save.call_count == 0
        assert mocked_plotting_savefig.call_count == 0
        assert mocked_ugrid_add.call_count == 11

    @pytest.mark.parametrize("display, old_zmin_zmax", [
        (False, False),
        (True,False),
        (True,True),
        (False, True),
    ])   
    def given_file_names_based_on_numbers_with_plotting_off_and_needs_tide_true_when_analyse_and_report_dflowfm_then_return_true_and_expect_zero_grids_added_and_plotting_not_called(self, tmp_path, display : bool, old_zmin_zmax : bool , setup):        
        """
        given : file names based on numbers with plotting off and needs tide true
        when  : analyse and report dflowfm
        then  : return true and expect zero grids added and plotting not called
        """
        needs_tide = True
        
        outputdir = str(tmp_path)
        
        self.n_fields = 1
        
        self.plotops['plotting'] = False
        
        self.filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        self.filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        self.filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.comp_sedimentation_volume') as mocked_comp_sedimentation_volume:

            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
            mocked_comp_sedimentation_volume.return_value = (None, None, [], None, None, [], numpy.zeros(2555), numpy.zeros(2555))
            
            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display,
                    self.report,
                    self.q_threshold,
                    self.tstag,
                    self.Q,
                    self.T,
                    self.rsigma,
                    self.slength,
                    self.nwidth,
                    self.ucrit,
                    self.filenames,
                    self.xykm,
                    needs_tide,
                    self.n_fields,
                    self.tide_bc,
                    old_zmin_zmax,
                    self.kmbounds,
                    outputdir,
                    self.plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 0
        assert mocked_plotting_zoom_xy_and_save.call_count == 0
        assert mocked_plotting_savefig.call_count == 0
        assert mocked_ugrid_add.call_count == 0
        
    @pytest.mark.parametrize("display, old_zmin_zmax", [
        (False, False),
        (True,False),
        (True,True),
        (False, True),
    ])
    def given_file_names_with_plotting_on_and_needs_tide_false_when_analyse_and_report_dflowfm_then_return_true_and_expect_eleven_grids_added_and_plotting_called(self, tmp_path, display : bool, old_zmin_zmax : bool, setup):        
        """
        given : file names with plotting on and needs tide false
        when  : analyse and report dflowfm
        then  : return true and expect eleven grids added and plotting called
        """
        needs_tide = False
        
        outputdir = str(tmp_path)
        
        self.n_fields = 1
        
        self.plotops['plotting'] = True
        self.plotops['saveplot'] = True
        self.plotops['saveplot_zoomed'] = True
        self.plotops['figdir'] = str(tmp_path)
        self.plotops['plot_ext'] = "plot_ext"
        
        random_list: List[Tuple[float, float, float, float]] = [
            (random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0))]
        
        self.plotops['xyzoom'] = random_list
        
        self.filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        self.filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        self.filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.comp_sedimentation_volume') as mocked_comp_sedimentation_volume:

            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
            mocked_comp_sedimentation_volume.return_value = (None, None, [], None, None, [], numpy.zeros(2555), numpy.zeros(2555))
            
            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display,
                    self.report,
                    self.q_threshold,
                    self.tstag,
                    self.Q,
                    self.T,
                    self.rsigma,
                    self.slength,
                    self.nwidth,
                    self.ucrit,
                    self.filenames,
                    self.xykm,
                    needs_tide,
                    self.n_fields,
                    self.tide_bc,
                    old_zmin_zmax,
                    self.kmbounds,
                    outputdir,
                    self.plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 1
        assert mocked_plotting_zoom_xy_and_save.call_count == 1
        assert mocked_plotting_savefig.call_count == 1
        assert mocked_ugrid_add.call_count == 11
        
    @pytest.mark.parametrize("display, old_zmin_zmax", [
        (False, False),
        (True,False),
        (True,True),
        (False, True),
    ])
    def given_file_names_with_plotting_on_and_needs_tide_true_when_analyse_and_report_dflowfm_then_return_true_and_expect_zero_grids_added_and_plotting_not_called(self, tmp_path, display : bool, old_zmin_zmax : bool, setup):        
        """
        given : file names with plotting on and needs tide false
        when  : analyse and report dflowfm
        then  : return true and expect zero grids added and plotting not called
        """
        needs_tide = True
        
        outputdir = str(tmp_path)
        
        self.n_fields = 1
        
        self.plotops['plotting'] = True
        self.plotops['saveplot'] = True
        self.plotops['saveplot_zoomed'] = True
        self.plotops['figdir'] = str(tmp_path)
        self.plotops['plot_ext'] = "plot_ext"
        
        random_list: List[Tuple[float, float, float, float]] = [
            (random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0))]
        
        self.plotops['xyzoom'] = random_list
        
        self.filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        self.filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        self.filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.comp_sedimentation_volume') as mocked_comp_sedimentation_volume:

            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
            mocked_comp_sedimentation_volume.return_value = (None, None, [], None, None, [], numpy.zeros(2555), numpy.zeros(2555))
            
            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display,
                    self.report,
                    self.q_threshold,
                    self.tstag,
                    self.Q,
                    self.T,
                    self.rsigma,
                    self.slength,
                    self.nwidth,
                    self.ucrit,
                    self.filenames,
                    self.xykm,
                    needs_tide,
                    self.n_fields,
                    self.tide_bc,
                    old_zmin_zmax,
                    self.kmbounds,
                    outputdir,
                    self.plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 0
        assert mocked_plotting_zoom_xy_and_save.call_count == 0
        assert mocked_plotting_savefig.call_count == 0
        assert mocked_ugrid_add.call_count == 0
        
        
    @pytest.mark.parametrize("needs_tide, old_zmin_zmax", [
        (False, False),
        (True, False),
        (True, True),
        (False, True),
    ])
    def given_xykm_and_no_display_when_analyse_and_report_dflowfm_then_return_true_and_expect_sixteen_grids_added_and_plotting_called(self, tmp_path, needs_tide : bool, old_zmin_zmax : bool, setup):
        """
        given : xykm and no display
        when  : analyse and report dflowfm
        then  : return true and expect sixteen grids addedand plotting called
        """
        outputdir = str(tmp_path)
        
        self.n_fields = 1
        
        self.plotops['plotting'] = True
        self.plotops['saveplot'] = True
        self.plotops['saveplot_zoomed'] = True
        self.plotops['figdir'] = str(tmp_path)
        self.plotops['plot_ext'] = "plot_ext"
        
        random_list: List[Tuple[float, float, float, float]] = [
            (random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0))]
        
        self.plotops['xyzoom'] = random_list
        
        self.filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        self.filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        self.filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.comp_sedimentation_volume') as mocked_comp_sedimentation_volume:

            mocked_plotting_plot_overview.return_value = ((plt.figure(figsize=(8, 6)) ,plt.axes()))
            mocked_comp_sedimentation_volume.return_value = (None, None, [], None, None, [], numpy.zeros(0), numpy.zeros(0))

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
                    self.q_threshold,
                    self.tstag,
                    self.Q,
                    self.T,
                    self.rsigma,
                    self.slength,
                    self.nwidth,
                    self.ucrit,
                    self.filenames,
                    self.xykm,
                    needs_tide,
                    self.n_fields,
                    self.tide_bc,
                    old_zmin_zmax,
                    self.kmbounds,
                    outputdir,
                    self.plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 1
        assert mocked_plotting_zoom_xy_and_save.call_count == 1
        assert mocked_plotting_savefig.call_count == 1
        assert mocked_ugrid_add.call_count == 16