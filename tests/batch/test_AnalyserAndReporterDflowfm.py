import os
from typing import Tuple
from unittest.mock import patch
import pytest
from dfastmi.batch import AnalyserAndReporterDflowfm
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

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
    def given_file_names_with_plotting_off_when_analyse_and_report_dflowfm_then_expect_return_true_and_elven_grids_added(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
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