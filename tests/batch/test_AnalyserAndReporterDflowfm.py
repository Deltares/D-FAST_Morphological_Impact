import os
from typing import Tuple

import pytest
from dfastmi.batch import AnalyserAndReporterDflowfm

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
    def given_when_then(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
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
    def given_when_then2(self, tmp_path, display : bool, needs_tide : bool, old_zmin_zmax : bool):
        report = None
        q_threshold = 1.0
        slength = 1.0
        nwidth = 1.0
        filenames = {}
        filenames[0] = ("name1", "name2")
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