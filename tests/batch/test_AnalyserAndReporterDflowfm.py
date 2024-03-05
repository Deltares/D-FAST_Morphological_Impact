from ast import List
import os
import random
from typing import Tuple
from unittest.mock import patch
from matplotlib import pyplot as plt
import numpy
import pytest
from dfastmi.batch import AnalyserAndReporterDflowfm
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.DataTextFileOperations import DataTextFileOperations

class Test_analyse_and_report_dflowfm_mode():
    
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
    def given_no_file_names_when_analyse_and_report_dflowfm_then_return_true(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
        report = None
        q_threshold = 1.0
        slength = 1.0
        nwidth = 1.0
        filenames = {}
        xykm = None
        n_fields = 3
        tide_bc: Tuple[str, ...] = ("name1", "name2")
        kmbounds : Tuple[float, float] = (1.0, 2.0)
        plotops = {}
        
        tstag = 1.0
        Q = [1.0, 2.0, 3.0]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        

        succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                display,
                report,
                q_threshold,
                tstag,
                Q,
                T,
                rsigma,
                slength,
                nwidth,
                ucrit,
                filenames,
                xykm,
                needs_tide,
                n_fields,
                tide_bc,
                old_zmin_zmax,
                kmbounds,
                outputdir,
                plotops)

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
    def given_file_names_based_on_string_when_analyse_and_report_dflowfm_then_return_true(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
        report = None
        q_threshold = 1.0
        slength = 1.0
        nwidth = 1.0
        filenames = {}
        filenames["0"] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        filenames["1"] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        filenames["2"] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        xykm = None
        n_fields = 3
        tide_bc: Tuple[str, ...] = ("name1", "name2")
        kmbounds : Tuple[float, float] = (1.0, 2.0)
        plotops = {}
        
        tstag = 1.0
        Q = [1.0, 2.0, 3.0]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        

        succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                display,
                report,
                q_threshold,
                tstag,
                Q,
                T,
                rsigma,
                slength,
                nwidth,
                ucrit,
                filenames,
                xykm,
                needs_tide,
                n_fields,
                tide_bc,
                old_zmin_zmax,
                kmbounds,
                outputdir,
                plotops)

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
    def given_file_names_with_plotting_off_when_analyse_and_report_dflowfm_then_expect_return_true_and_eleven_grids_added(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
        report = None
        q_threshold = 1.0
        slength = 1.0
        nwidth = 1.0
        filenames = {}
        filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        xykm = None
        n_fields = 1
        tide_bc: Tuple[str, ...] = ("name1", "name2")
        kmbounds : Tuple[float, float] = (1.0, 2.0)
        plotops = {}
        plotops['plotting'] = False
        
        tstag = 1.0
        Q = [1.0, 2.0, 3.0]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add:
        
            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display,
                    report,
                    q_threshold,
                    tstag,
                    Q,
                    T,
                    rsigma,
                    slength,
                    nwidth,
                    ucrit,
                    filenames,
                    xykm,
                    needs_tide,
                    n_fields,
                    tide_bc,
                    old_zmin_zmax,
                    kmbounds,
                    outputdir,
                    plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_ugrid_add.call_count == 11
        
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
    def given_file_names_with_plotting_on_when_analyse_and_report_dflowfm_then_expect_return_true_and_eleven_grids_added(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
        report = None
        q_threshold = 1.0
        slength = 1.0
        nwidth = 1.0
        filenames = {}
        filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        xykm = None
        n_fields = 1
        tide_bc: Tuple[str, ...] = ("name1", "name2")
        kmbounds : Tuple[float, float] = (1.0, 2.0)
        plotops = {}
        plotops['plotting'] = True
        plotops['saveplot'] = True
        plotops['saveplot_zoomed'] = True
        plotops['figdir'] = str(tmp_path)
        plotops['plot_ext'] = "plot_ext"
        
        random_list: List[Tuple[float, float, float, float]] = [
            (random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0))]
        
        plotops['xyzoom'] = random_list
        
        tstag = 1.0
        Q = [1.0, 2.0, 3.0]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig:
            
            Figure = plt.figure
            Axes = plt.axes
            mocked_plotting_plot_overview.return_value = ((Figure(figsize=(8, 6)) ,Axes()))
            
            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    display,
                    report,
                    q_threshold,
                    tstag,
                    Q,
                    T,
                    rsigma,
                    slength,
                    nwidth,
                    ucrit,
                    filenames,
                    xykm,
                    needs_tide,
                    n_fields,
                    tide_bc,
                    old_zmin_zmax,
                    kmbounds,
                    outputdir,
                    plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 1
        assert mocked_plotting_zoom_xy_and_save.call_count == 1
        assert mocked_plotting_savefig.call_count == 1
        assert mocked_ugrid_add.call_count == 11
        
        
    @pytest.mark.parametrize("needs_tide, old_zmin_zmax", [
        (False, False),
        (True, False),
        (True, True),
        (False, True),
    ])
    def given_xykm_display_false_when_analyse_and_report_dflowfm_then_expect_return_true_and_sixteen_grids_added(self, tmp_path, needs_tide : bool, old_zmin_zmax : bool):
        report = None
        q_threshold = 1.0
        slength = 1.0
        nwidth = 1.0
        filenames = {}
        filenames[0] = ("measure-Q1_map.nc", "measure-Q1_map.nc")
        filenames[1] = ("measure-Q2_map.nc", "measure-Q2_map.nc")
        filenames[2] = ("measure-Q3_map.nc", "measure-Q3_map.nc")
        n_fields = 1
        tide_bc: Tuple[str, ...] = ("name1", "name2")
        kmbounds : Tuple[float, float] = (1.0, 2.0)
        plotops = {}
        plotops['plotting'] = True
        plotops['saveplot'] = True
        plotops['saveplot_zoomed'] = True
        plotops['figdir'] = str(tmp_path)
        plotops['plot_ext'] = "plot_ext"
        
        random_list: List[Tuple[float, float, float, float]] = [
            (random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0), random.uniform(0.0, 100.0))]
        
        plotops['xyzoom'] = random_list
        
        tstag = 1.0
        Q = [1.0, 2.0, 3.0]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        ucrit = 0.3
        outputdir = str(tmp_path)
        
        with patch('dfastmi.batch.AnalyserAndReporterDflowfm.GridOperations.ugrid_add') as mocked_ugrid_add, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.plot_overview') as mocked_plotting_plot_overview, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.zoom_xy_and_save') as mocked_plotting_zoom_xy_and_save, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.dfastmi.plotting.savefig') as mocked_plotting_savefig, \
             patch('dfastmi.batch.AnalyserAndReporterDflowfm.comp_sedimentation_volume') as mocked_comp_sedimentation_volume:

            Figure = plt.figure
            Axes = plt.axes
            mocked_plotting_plot_overview.return_value = ((Figure(figsize=(8, 6)) ,Axes()))
            
            sedarea = None
            sedvol = None
            sed_area_list = []
            eroarea = None
            erovol = None
            ero_area_list = []
            wght_area_tot = numpy.zeros(2555)
            wbini = numpy.zeros(2555)
            mocked_comp_sedimentation_volume.return_value = (sedarea, sedvol, sed_area_list, eroarea, erovol, ero_area_list, wght_area_tot, wbini)

            ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

            cwd = os.getcwd()
            tstdir = "tests/c01 - GendtseWaardNevengeul"
            try:
                os.chdir(tstdir)
                
                testing_working_dir = os.getcwd()
                kmfile = testing_working_dir + "\\..\\files\\read_xyc_test.xyc"
                xykm = DataTextFileOperations.get_xykm(kmfile)
                
                succes = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
                    False,
                    report,
                    q_threshold,
                    tstag,
                    Q,
                    T,
                    rsigma,
                    slength,
                    nwidth,
                    ucrit,
                    filenames,
                    xykm,
                    needs_tide,
                    n_fields,
                    tide_bc,
                    old_zmin_zmax,
                    kmbounds,
                    outputdir,
                    plotops)
            finally:
                os.chdir(cwd)
        
        assert succes
        assert mocked_plotting_plot_overview.call_count == 1
        assert mocked_plotting_zoom_xy_and_save.call_count == 1
        assert mocked_plotting_savefig.call_count == 1
        assert mocked_ugrid_add.call_count == 16