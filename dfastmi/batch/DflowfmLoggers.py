from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper

from typing import TextIO

class XykmDataLogger():
    def __init__(self, display : bool):
        self.display = display
    
    def print_apply_filter(self):
        print("apply filter")

    def print_prepare_filter(self, step : int):
        print(f"prepare filter step {step}")

    def print_prepare(self):
        print("prepare")

    def print_buffer(self):
        print("buffer")
        
    def log_done(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- done')

    def log_direction(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- direction')

    def log_chainage(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- chainage')

    def log_project(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- project')

    def log_identify_region_of_interest(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- identify region of interest')

class AnalyserDflowfmLogger():
    
    xykm_data_logger : XykmDataLogger
    
    def __init__(self, display : bool, report : TextIO):
        self.display = display
        self.report = report
        self.xykm_data_logger = XykmDataLogger(display)

    def log_char_bed_changes(self):
        if self.display:
            ApplicationSettingsHelper.log_text("char_bed_changes")

    def log_load_mesh(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- load mesh')

    def log_identify_region_of_interest(self):
        if self.display:
            ApplicationSettingsHelper.log_text('-- identify region of interest')

    def report_missing_calculation_values(self, needs_tide, q, t):
        if needs_tide:
            ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=self.report)
        else:
            ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_missing_calculation_dzq_values(self, q, t):
        if t > 0:
            ApplicationSettingsHelper.log_text("no_file_specified_q_and_t", dict={"q": q, "t": t}, file=self.report)
        else:
            ApplicationSettingsHelper.log_text("no_file_specified_q_only", dict={"q": q}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_file_not_specified(self, q):
        ApplicationSettingsHelper.log_text("no_file_specified", dict={"q": q}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def report_file_not_found(self, filename):
        ApplicationSettingsHelper.log_text("file_not_found", dict={"name": filename}, file=self.report)
        ApplicationSettingsHelper.log_text("end_program", file=self.report)

    def print_riverkm_needed_for_tidal(self):
        print("RiverKM needs to be specified for tidal applications.")

    def print_measure_not_active_for_checked_conditions(self):
        print("The measure is not active for any of the checked conditions.")