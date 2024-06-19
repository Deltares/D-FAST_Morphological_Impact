# -*- coding: utf-8 -*-
"""
Copyright © 2024 Stichting Deltares.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation version 2.1.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see <http://www.gnu.org/licenses/>.

contact: delft3d.support@deltares.nl
Stichting Deltares
P.O. Box 177
2600 MH Delft, The Netherlands

All indications and logos of, and references to, "Delft3D" and "Deltares"
are registered trademarks of Stichting Deltares, and remain the property of
Stichting Deltares. All rights reserved.

INFORMATION
This file is part of D-FAST Morphological Impact: https://github.com/Deltares/D-FAST_Morphological_Impact
"""

import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Dict, Optional, TextIO, Tuple

import matplotlib
from packaging.version import InvalidVersion, Version

import dfastmi.kernel.core
from dfastmi.batch import AnalyserAndReporterDflowfm, AnalyserAndReporterWaqua
from dfastmi.batch.FileNameRetrieverFactory import FileNameRetrieverFactory
from dfastmi.batch.PlotOptions import PlotOptions
from dfastmi.config.AConfigurationInitializerBase import AConfigurationInitializerBase
from dfastmi.config.ConfigFileOperations import ConfigFileOperations
from dfastmi.config.ConfigurationInitializerFactory import (
    ConfigurationInitializerFactory,
)
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.Branch import Branch
from dfastmi.io.DFastAnalysisConfigFileParser import DFastAnalysisConfigFileParser
from dfastmi.io.IReach import IReach
from dfastmi.io.Reach import Reach
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import Vector

WAQUA_EXPORT = "WAQUA export"
DFLOWFM_MAP = "D-Flow FM map"


def batch_mode(config_file: str, rivers: RiversObject, reduced_output: bool) -> None:
    """
    Run the program in batch mode.

    Load the configuration file and run the analysis.

    Arguments
    ---------
    config_file : str
        Name of the configuration file.
    rivers : RiversObject
        An object containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.

    Return
    ------
    None
    """
    if reduced_output:
        ApplicationSettingsHelper.log_text("reduce_output")

    try:
        config = ConfigFileOperations.load_configuration_file(config_file)
        rootdir = Path(config_file).parent
    except:
        print(sys.exc_info()[1])
    else:
        batch_mode_core(rivers, reduced_output, config, rootdir=rootdir)


def batch_mode_core(
    rivers: RiversObject,
    reduced_output: bool,
    config: ConfigParser,
    rootdir: Path = None,
    gui: bool = False,
) -> bool:
    """
    Run the analysis for a given configuration in batch mode.

    Arguments
    ---------
    rivers : RiversObject
        An object containing the river data.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    config : configparser.ConfigParser
        Configuration of the analysis to be run.
    rootdir : Path
        Reference directory for default output folders.
    gui : bool
        Flag indicating whether this routine is called from the GUI.

    Return
    ------
    success : bool
        Flag indicating whether the analysis could be completed successfully.
    """
    display = False
    data = DFastAnalysisConfigFileParser(config)

    # check outputdir
    rootdir = _get_root_dir(rootdir)
    outputdir = _get_output_dir(rootdir, display, data)
    report_path = outputdir.joinpath(
        ApplicationSettingsHelper.get_filename("report.out")
    )

    with report_path.open(mode="w", encoding="utf-8") as report:
        _log_header(report)

        cfg_version = _get_version(rivers, config)

        branch_name = config.get("General", "Branch", fallback="")
        branch = rivers.get_branch(branch_name)
        if not branch:
            ApplicationSettingsHelper.log_text(
                "invalid_branch", dict={"branch": branch_name}, file=report
            )
            success = False
        else:
            reach_name = config.get("General", "Reach", fallback="")
            reach = branch.get_reach(reach_name)
            if not reach:
                ApplicationSettingsHelper.log_text(
                    "invalid_reach",
                    dict={"reach": reach_name, "branch": branch_name},
                    file=report,
                )
                success = False
            else:
                success = _analyse_and_report(
                    config,
                    data,
                    cfg_version,
                    reach,
                    branch,
                    display,
                    report,
                    reduced_output,
                    rootdir,
                    outputdir,
                    gui,
                )

        ApplicationSettingsHelper.log_text("end", file=report)

    return success


def _report_section_break(report: TextIO):
    ApplicationSettingsHelper.log_text("===", file=report)


def _report_analysis_configuration(
    imode: int,
    branch: Branch,
    reach: IReach,
    initialized_config: AConfigurationInitializerBase,
    config: ConfigParser,
    report: TextIO,
):
    """Basic WAQUA analysis configuration will not be reported."""
    if imode == 0:
        return

    _report_analysis_settings_header(report)
    _report_case_description(initialized_config.case_description, report)
    _report_basic_analysis_configuration(
        branch,
        reach,
        branch.qlocation,
        initialized_config,
        report,
    )
    _report_critical_velocity(initialized_config.ucrit, report)
    _report_analysis_conditions_header(report)
    _report_used_file_names(config, initialized_config, report)
    _report_section_break(report)


def _report_case_description(case_description: str, report):
    settings = {
        "case_description": case_description,
    }
    ApplicationSettingsHelper.log_text("case_description", file=report, dict=settings)


def _report_analysis_settings_header(report: TextIO):
    ApplicationSettingsHelper.log_text("analysis_settings_header", report)


def _report_basic_analysis_configuration(
    branch: Branch,
    reach: Reach,
    qlocation: str,
    initialized_config: AConfigurationInitializerBase,
    report: TextIO,
):
    settings = {
        "branch": branch.name,
        "reach": reach.name,
        "location": qlocation,
        "q_threshold": initialized_config.q_threshold,
        "slength": int(initialized_config.slength),
    }
    ApplicationSettingsHelper.log_text("analysis_settings", file=report, dict=settings)


def _report_critical_velocity(
    ucrit: float,
    report: TextIO,
):
    settings = {
        "u_critical": ucrit,
    }
    ApplicationSettingsHelper.log_text(
        "analysis_settings_critical_velocity", file=report, dict=settings
    )


def _report_analysis_conditions_header(report: TextIO):
    ApplicationSettingsHelper.log_text("analysis_settings_conditions_header", report)


def _report_used_file_names(
    config: ConfigParser,
    initialized_config: AConfigurationInitializerBase,
    report: TextIO,
):
    imode = _get_mode_usage(config)
    filenames = get_filenames(imode, initialized_config.needs_tide, config)
    for i, q in enumerate(initialized_config.discharges):
        if not q:  # should only happen for version 1 files
            continue
        if 0 in filenames:
            key = i
        elif initialized_config.needs_tide:
            key = (q, initialized_config.tide_bc[i])
        else:
            key = q
            
        condition, reference_file_name, measure_file_name, comment = get_analysis_condition_values_for_logging(initialized_config, filenames, q, key)

        _report_analysis_conditions_values(
            condition, reference_file_name, measure_file_name, comment, report
        )

def get_analysis_condition_values_for_logging(initialized_config : AConfigurationInitializerBase, filenames, q, key):
    condition = "{:7.1f} m3/s".format(q)
    
    if q <= initialized_config.q_threshold:
        reference_file_name = "---"
        measure_file_name = "---"
        comment = "(measure not active)"
    elif key in filenames:
        files = filenames[key]
        reference_file_name = _get_file_name(files[0])
        measure_file_name = _get_file_name(files[1])
        comment = ""
    else:
        reference_file_name = "xxx"
        measure_file_name = "xxx"
        comment = "(not specified)"
        
    return condition, reference_file_name, measure_file_name, comment


def _get_file_name(location: str) -> str:
    path = Path(location)
    return path.name


def _report_analysis_conditions_values(
    condition: str, reference: str, measure: str, comment : str, report: TextIO
):
    settings = {
        "condition": condition,
        "reference": reference,
        "measure": measure,
        "comment": comment,
    }
    ApplicationSettingsHelper.log_text(
        "analysis_settings_conditions_values", file=report, dict=settings
    )


def _get_mode_usage(config: ConfigParser) -> int:
    """
    Detect which mode is used to create the output report.
    The mode could be using WAQUA or (default) DFLOWFM.
    Depending on the mode select the appropriate analysis runner.

    Arguments
    ---------
    config: ConfigParser
        Configuration of the analysis to be run.

    Return
    ------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).
    """
    mode_str = config.get("General", "Mode", fallback=DFLOWFM_MAP)
    if mode_str == WAQUA_EXPORT:
        return 0
    else:
        return 1


def _report_mode_usage(imode: int, report: TextIO) -> int:
    """
    Log which mode is used to create the output report.
    The mode could be using WAQUA or (default) DFLOWFM.

    Arguments
    ---------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).
    report : TextIO
        Text stream for log file.
    """
    if imode == 0:
        ApplicationSettingsHelper.log_text(
            "results_with_input_waqua",
            file=report,
            dict={
                "avgdzb": ApplicationSettingsHelper.get_filename("avgdzb.out"),
                "maxdzb": ApplicationSettingsHelper.get_filename("maxdzb.out"),
                "mindzb": ApplicationSettingsHelper.get_filename("mindzb.out"),
            },
        )
    else:
        ApplicationSettingsHelper.log_text(
            "results_with_input_dflowfm",
            file=report,
            dict={"netcdf": ApplicationSettingsHelper.get_filename("netcdf.out")},
        )


def _get_version(rivers: RiversObject, config: ConfigParser) -> Version:
    """
    Will get the stated version string from the application config
    and convert this to a Version object.
    This can be used to determine which Rivers configuration should
    be used in the calculation.

    Arguments
    ---------
    rivers : RiversObject
        An object containing the river data.
    config: ConfigParser
        Configuration of the analysis to be run.

    Return
    ------
    version : Version
        Version object extracted from the configuration file.
    """
    cfg_version = config.get("General", "Version", fallback="")
    try:
        cfg_version = Version(cfg_version)
    except InvalidVersion as exception:
        raise LookupError(
            f"Wrong version detected in configuration file, when parsing the value got this : {exception}"
        )

    if cfg_version != rivers.version:
        raise LookupError(
            f"Version number of configuration file ({cfg_version}) must match version number of rivers file ({rivers.version})"
        )

    return cfg_version


def _log_header(report: TextIO) -> None:
    """
    Will log into the report default static header information

    Arguments
    ---------
    report: TextIO
        An object containing the river data.

    Returns
    -------
    None
    """
    prog_version = dfastmi.__version__
    ApplicationSettingsHelper.log_text(
        "header", dict={"version": prog_version}, file=report
    )
    ApplicationSettingsHelper.log_text("limits", file=report)
    _report_section_break(report)


def _get_output_dir(
    rootdir: str, display: bool, data: DFastAnalysisConfigFileParser
) -> Path:
    """
    Will get the string containing the explicit output directory from the dfast configuration.
    If not available it will create an explicit output directory relative to the root directory.
    From this string it will create a PathLib Path object.

    Arguments
    ---------
    rootdir : str
        Reference directory for default folders.
    display : bool
        Flag indicating text output to stdout.
    data : DFastAnalysisConfigFileParser
        DFast MI application config file.

    Return
    ------
    outputdir : Path
        A Path object to the output directory location.
    """
    outputdir = Path(
        data.getstring("General", "OutputDir", str(Path(rootdir).joinpath("output")))
    )
    if outputdir.exists():
        if display:
            ApplicationSettingsHelper.log_text("overwrite_dir", dict={"dir": outputdir})
    else:
        outputdir.mkdir()
    return outputdir


def _get_root_dir(rootdir: Path) -> Path:
    """
    Return a new path object representing the current directory.

    Arguments
    ---------
    rootdir : Path
        Reference directory for default folders.

    Return
    ------
    rootdir : Path
        A Path object to the currenct directory
        location or default directory location.
    """
    if not rootdir:
        rootdir = Path.cwd()
    return rootdir


def count_discharges(discharges: Vector) -> int:
    """
    Count the number of non-empty discharges.

    Arguments
    ---------
    discharges : Vector
        Tuple of (at most) three characteristic discharges (Q).

    Returns
    -------
    n : int
        Number of non-empty discharges.
    """
    return sum([q is not None for q in discharges])


def get_filenames(
    imode: int,
    needs_tide: bool,
    config: Optional[ConfigParser] = None,
) -> Dict[Any, Tuple[str, str]]:
    """
    Extract the list of six file names from the configuration.

    Arguments
    ---------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).

    needs_tide : bool
        Specifies whether the tidal boundary is needed.

    config : Optional[ConfigParser]
        The variable containing the configuration (may be None for imode = 0).

    Returns
    -------
    filenames : Dict[Any, Tuple[str,str]]
        Dictionary of string tuples representing the D-Flow FM file names for
        each reference/with measure pair. The keys of the dictionary vary. They
        can be the discharge index, discharge value or a tuple of forcing
        conditions, such as a Discharge and Tide forcing tuple.
    """

    if imode != 0:
        general_version = config.get("General", "Version", fallback=None)
    else:
        general_version = None

    if general_version:
        file_name_retriever_version = Version(general_version)
    else:
        file_name_retriever_version = None

    file_name_retriever = FileNameRetrieverFactory.generate(
        file_name_retriever_version, needs_tide
    )
    return file_name_retriever.get_file_names(config)


def _analyse_and_report(
    config: ConfigParser,
    data: DFastAnalysisConfigFileParser,
    cfg_version: Version,
    reach: IReach,
    branch: Branch,
    display: bool,
    report: TextIO,
    reduced_output: bool,
    rootdir: Path,
    outputdir: Path,
    gui: bool,
) -> bool:
    """
    Perform analysis for any model.

    Depending on the mode select the appropriate analysis runner.

    Arguments
    ---------
    config : ConfigParser
        The variable containing the configuration.
    data : DFastAnalysisConfigFileParser
        DFast MI application config file.
    cfg_version : Version,
        Version object extracted from the configuration file.
    branch : Branch
        Branch object we want to do analysis on.
    reach: IReach,
        Reach object we want to do analysis on,
    display : bool
        Flag indicating text output to stdout.
    report : TextIO
        Text stream for log file.
    reduced_output : bool
        Flag to indicate whether WAQUA output should be reduced to the area of
        interest only.
    rootdir : Path
        Reference directory for default folders.
    outputdir : Path
        Reference directory for default output folders.
    gui : bool
        Flag indicating whether this routine is called from the GUI.

    Returns
    -------
    success : bool
        Flag indicating whether analysis could be carried out.
    """
    initialized_config = ConfigurationInitializerFactory.generate(
        cfg_version, reach, config
    )

    old_zmin_zmax = False

    plotting_options = PlotOptions()
    plotting_options.set_plotting_flags(rootdir, display, data)

    imode = _get_mode_usage(config)
    _report_analysis_configuration(
        imode,
        branch,
        reach,
        initialized_config,
        config,
        report,
    )
    _report_mode_usage(imode, report)
    filenames = get_filenames(imode, initialized_config.needs_tide, config)
    success = False

    if imode == 0:
        success = AnalyserAndReporterWaqua.analyse_and_report_waqua(
            display,
            report,
            reduced_output,
            initialized_config.tstag,
            initialized_config.discharges,
            initialized_config.apply_q,
            initialized_config.time_fractions_of_the_year,
            initialized_config.rsigma,
            initialized_config.ucrit,
            old_zmin_zmax,
            outputdir,
        )
    else:
        success = AnalyserAndReporterDflowfm.analyse_and_report_dflowfm(
            display,
            report,
            reach.normal_width,
            filenames,
            plotting_options.xykm,
            old_zmin_zmax,
            outputdir,
            plotting_options,
            initialized_config,
        )

    _log_length_estimate(report, initialized_config.slength)

    _finalize_plotting(plotting_options, gui)

    return success


def _finalize_plotting(plotting_options: PlotOptions, gui: bool) -> None:
    """
    When plotting the analysis results and done analysing we need to
    finalize some actions to stop the plotting.

    Arguments
    ---------
    plotops : dict[str, Any]
        The variable with the key values
    gui : bool
        Flag indicating whether this routine is called from the GUI.

    Returns
    -------
    None
    """
    if plotting_options.plotting:
        if plotting_options.closeplot:
            matplotlib.pyplot.close("all")
        else:
            matplotlib.pyplot.show(block=not gui)


def _log_length_estimate(report: TextIO, slength: float) -> None:
    """
    After analysis is done we want to report the used estimated
    length in the report.

    Arguments
    ---------
    report : TextIO
        Text stream for log file.
    slength : float
        The expected yearly impacted sedimentation length.

    Returns
    -------
    None
    """
    if slength > 1:
        nlength = f"{int(slength)}"
    else:
        nlength = f"{slength}"
    ApplicationSettingsHelper.log_text(
        "length_estimate", dict={"nlength": nlength}, file=report
    )


def write_report(
    report: TextIO,
    reach: str,
    q_location: str,
    q_threshold: Optional[float],
    q_bankfull: float,
    q_stagnant: float,
    tstag: float,
    q_fit: Tuple[float, float],
    discharges: Vector,
    t: Vector,
    slength: float,
) -> None:
    """
    Write the analysis report to file.

    Arguments
    ---------
    report : TextIO
        Text stream for log file.
    reach : str
        The name of the selected reach.
    q_location : str
        The name of the discharge location.
    q_threshold : Optional[float]
        The discharge below which the measure is not flow-carrying (None if always flowing above 1000 m3/s or when barriers are opened).
    q_bankull : float
        The discharge at which the measure is bankfull.
    q_stagnant : float
        Discharge below which the river flow is negligible.
    tstag : float
        Fraction of year during which the flow velocity is negligible.
    q_fit : Tuple[float, float]
        A discharge and dicharge change determining the discharge exceedance curve (from rivers configuration file).
    discharges : Vector
        A tuple of 3 discharges (Q) for which simulation results are (expected to be) available.
    t : Vector
        A tuple of 3 values each representing the fraction of the year during which the discharge is given by the corresponding entry in Q.
    slength : float
        The expected yearly impacted sedimentation length.

    Returns
    -------
    None
    """
    ApplicationSettingsHelper.log_text("", file=report)
    ApplicationSettingsHelper.log_text("reach", dict={"reach": reach}, file=report)
    ApplicationSettingsHelper.log_text("", file=report)
    if q_threshold is not None:
        ApplicationSettingsHelper.log_text(
            "report_qthreshold",
            dict={"q": q_threshold, "border": q_location},
            file=report,
        )
    ApplicationSettingsHelper.log_text(
        "report_qbankfull",
        dict={"q": q_bankfull, "border": q_location},
        file=report,
    )
    ApplicationSettingsHelper.log_text("", file=report)
    if q_stagnant > q_fit[0]:
        ApplicationSettingsHelper.log_text(
            "closed_barriers", dict={"ndays": int(365 * tstag)}, file=report
        )
        ApplicationSettingsHelper.log_text("", file=report)
    for i in range(3):
        if discharges[i] is not None:
            ApplicationSettingsHelper.log_text(
                "char_discharge",
                dict={"n": i + 1, "q": discharges[i], "border": q_location},
                file=report,
            )
            if i < 2:
                tdays = int(365 * t[i])
            else:
                tdays = max(
                    0, 365 - int(365 * t[0]) - int(365 * t[1]) - int(365 * tstag)
                )
            ApplicationSettingsHelper.log_text(
                "char_period", dict={"n": i + 1, "ndays": tdays}, file=report
            )
            if i < 2:
                ApplicationSettingsHelper.log_text("", file=report)
            else:
                ApplicationSettingsHelper.log_text("---", file=report)
    number_of_discharges = count_discharges(discharges)
    if number_of_discharges == 1:
        ApplicationSettingsHelper.log_text(
            "need_single_input", dict={"reach": reach}, file=report
        )
    else:
        ApplicationSettingsHelper.log_text(
            "need_multiple_input",
            dict={"reach": reach, "numq": number_of_discharges},
            file=report,
        )

    stagenames = ["lowwater", "transition", "highwater"]
    # Code name of the discharge level.

    for i in range(3):
        if discharges[i] is not None:
            ApplicationSettingsHelper.log_text(
                stagenames[i],
                dict={"q": discharges[i], "border": q_location},
                file=report,
            )
    ApplicationSettingsHelper.log_text("---", file=report)
    if slength > 1:
        nlength = int(slength)
    else:
        nlength = slength
    ApplicationSettingsHelper.log_text(
        "length_estimate", dict={"nlength": nlength}, file=report
    )
    ApplicationSettingsHelper.log_text("prepare_input", file=report)
