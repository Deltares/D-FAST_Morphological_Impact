import os
import dfastmi.batch.AnalyserAndReporterWaqua
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

class Test_analyse_and_report_waqua_mode():
    def test_analyse_and_report_waqua(self, tmp_path):
        display = False
        reduced_output = False
        reach = "reach"
        q_location = "lobith"
        tstag = 0.0
        Q = [1.0, 2.0, 3.0]
        apply_q = [True, True, True]
        T = [1.0, 2.0, 3.0]
        rsigma = [0.1, 0.2, 0.3]
        slength = 1319.0
        ucrit = 0.3
        old_zmin_zmax = True
        outputdir = str(tmp_path)
        
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")

        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            succes = dfastmi.batch.AnalyserAndReporterWaqua.analyse_and_report_waqua(
            display,
            None,
            reduced_output,
            tstag,
            Q,
            apply_q,
            T,
            rsigma,
            ucrit,
            old_zmin_zmax,
            outputdir)
        finally:
            os.chdir(cwd)
        

        assert succes