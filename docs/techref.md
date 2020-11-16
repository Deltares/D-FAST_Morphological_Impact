# Software Requirements

## Introduction

The purpose of D-FAST Morphological Impact is to provide a first estimate of the bed level changes in the main channel if local measures were to be implemented outside the main channel.
It is based on the conceptual WAQMORF framework originally developed by Sieben (2008).
WAQMORF was developed for the SIMONA system.
D-FAST Morphological Impact implements the same functionality based on results obtained from D-Flow Flexible Mesh.
The detailed list of requirements is given below.

## Functional Requirements

1. This program must give the same results for the same data as WAQMORF.
1. Users must be able to run this program in batch mode from the command line.
1. Users must be able to run the analysis based on D-Flow FM results.
1. Users must be able to provide all data via an input file.
1. The input file must be easy to edit for users, i.e. a text file.
1. The report output must be a simple text file consistent with WAQMORF.
1. The spatial output must be easy to visualize in common software.

1. The should read relevant data directly from D-Flow FM map-files instead of intermediate XYZ files as required by WAQMORF for SIMONA results.

1. The input file could use the ini-format consistent with D-Flow FM input files.
1. A simple graphical user interface could support users in process of creating the input file.

1. It would be nice if the software would be more generally applicable than just the Dutch rivers.
1. It would be nice if the software would be able to run besides Dutch also in English.

All requirements are addressed by D-FAST Morphological Impact.

## Non-functional requirements

1. The performance of the tools must be similar to that of WAQMORF, i.e. it must run within seconds.
1. The software must be version controlled.
1. The software must have formal testing and support.
1. The software must run on Windows.
1. The software must be easy to distribute.
1. The software must have a user manual.
1. The software must have technical documentation.

1. The software should run on any common operating system.
1. The software should be available as open source.

All requirements are addressed by D-FAST Morphological Impact although the testing has been carried out on the Windows platform only.

# Code Design

## Introduction

The original WAQMORF code was developed in FORTRAN.
For D-FAST Morphological Impact we have selected Python because

* More domain specialists and users are familiar with Python and it's therefore easier for development cycle.
* Adding a graphical user interface (GUI) is easier in other languages than FORTRAN and by using the same language for kernel and GUI makes the code more consistent and reusable.
* The algorithm doesn't require large amounts of computations, so a native language isn't needed for adequate performance.
* The Python environment is available for free contrary to MATLAB which is also widely used in this community.
* Python supposedly allows for the creation of relatively small redistributable binaries.
* Python combines well with the open source nature of this software and other developments in the Delft3D / D-HYDRO environment.

The software uses a number of Python modules for specific functionality.
Most importantly the code builds on

* `netCDF4` for reading and writing netCDF files.
* `NumPy` for the numerical computations using arrays.
* `PyQt5` for the graphical user interface.

The next two sections describe the file formats used by the software and the subdivision into modules.

## File formats

The software distinguishes 6 files:

* The *rivers configuration file* defines the branches and reaches, and all parameter settings specific for the overall system, per branch or per reach.
* The *dialog text file* defines all strings to be used in the interaction with the users (GUI, report, or error messages).
* The *analysis configuration file* defines the settings that are relevant for a specific execution of the algorithm, i.e. for a specific branch, reach and measure.
* The *simulation result files* define the spatial variations in the velocities and water depths as needed by the algorithm.
* The *report file* contains a logging of the settings and lumped results for the analysis.
* The *spatial output file* contains the estimate of the spatial variation in the sedimentation and erosion patterns that will result from the measure (minimum, mean and maximum).

Each file type is addressed separately in the following subsections.

### rivers configuration file

The rivers configuration file follows the common ini-file format.
The file must contain a `[General]` block with a keyword `Version` to indicate the version number of the file.
The initial version number will be `1.0`.

Version 1.0 files must contain one `[Branches]` block defining the branches (in Dutch: takken) supported by the system and optionally global default values for parameters.
For every branch named in the `[Branches]` block, the file must contain a data block corresponding to the branch name that contains further information on that branch.
That block defines the reaches (in Dutch: stukken) to be distinguished as well as the branch or reach specific parameter settings.
Further details follow below.

| Block          | Keyword    | Description |
|----------------|------------|-------------|
| General        | Version    | Version number. Must be `1.0` |
| Branches       | Branch<i>  | Name of branch <i>, i.e. BranchName<i> |
| BranchName<i>  | Reach<j>   | Name of reach <j> within branch <i> |
| BranchName<i>  | QLocation  | Location at which discharges for branch <i> are defined |
| B*             | QStagnant  | Discharge [m3/s] below which main channel flow can be assumed stagnant |
| B*             | QMin       | Minimum discharge [m3/s] at which measure becomes active |
| B*             | QFit       | Two discharges [m3/s] used for representing the exceedance curve |
| B*             | QLevels    | Four characteristic discharges [m3/s] used by algorithm |
| B*             | dQ         | Two discharge adjustments [m3/s] used by algorithm |
| B*             | NWidth     | Normal width [m] of main channel |
| B*             | PRLow      | Low flow propagation rate [km/yr] |
| B*             | PRHigh     | High flow propagation rate [km/yr] |
| B*             | UCrit      | Critical (minimum) velocity [m/s] for sediment transport |

The second value of `QLevels` corresponds to the typical bankfull discharge.
All keywords listed for block `B*` may occur either in the `[Branches]` block or in one of the branch specific blocks where they may optionally be concatenated with the reach number <j>.
Those keywords may thus occur in three flavours:

1. Plain keyword in block `[Branches]`: global default value valid for all branches
1. Plain keyword in branch specific block: default value for that branch (overrules any global default)
1. Keyword followed by reach number <j> in branch specific block: value valid for that reach on that branch.

**Example**

The following excerpt of the default `Dutch_rivers.cfg` configuration file shows the `[General]` and `[Branches]` blocks as well as the first part of the `[Bovenrijn & Waal]` block for the first branch.
It includes a global value of 0.3 for `UCrit` and 100 for `QMin`.
The other parameters are specified at branch level and mostly uniform for the whole branch.
Only `NWidth` and `PRLow` vary depending on the reach selected.

    [General]
        Version    = 1.0

    [Branches]
        Name1      = Bovenrijn & Waal
        Name2      = Pannerdensch Kanaal & Nederrijn-Lek
        Name3      = IJssel
        Name4      = Merwedes
        Name5      = Maas
        UCrit      = 0.3
        QMin       = 1000

    [Bovenrijn & Waal]
        QLocation  = Lobith
        QStagnant  = 800
        QFit       = 800  1280
        QLevels    = 3000  4000  6000  10000
        dQ         = 1000  1000
        PRHigh     = 3.65
        
        Reach1     = Bovenrijn                    km  859-867
        NWidth1    = 340
        PRLow1     = 0.89
        
        Reach2     = Boven-Waal                   km  868-886
        NWidth2    = 260
        PRLow2     = 0.81

        ... continued ...


### dialog text file

The dialog text file uses the block labels enclosed by square brackets of the common ini-file format, but the lines in between the blocks are treated verbatim and don't list keyword/value pairs.
Every print statement in the program is associated with a short descriptive identifier.
These identifiers show up in the dialog text file as the block labels.
The text that follows the block label will be used at that location in the program.
The order of the blocks in the file is not important.
Please note that every line is used as is, so don't add indentations or blank lines unless you want those to show up during the program execution.
Most blocks may contain any number of lines, but some blocks may only contain a single line in particular block that start with `gui_` or `filename_`.
Some data blocks may contain one or more named placeholders, e.g. `{version}`, used for inserting values by means of the Python `format()` method.

**Example**

The following excerpt of the default `messages.NL.cfg` dialog text file shows the string definition for 5 identifiers, namely '' (the identifier for an empty line), 'header', 'confirm', 'confirm_or' and 'confirm_or_restart'.
The header string contains one placeholder, namely `{version}` for the the version number.

    []
    
    [header]
    Dit programma is de "WAQUA vuistregel" voor het schatten
    van lokale morfologische effecten door een lokale ingreep
    (zie RWS-WD memo WAQUA vuistregel 20-10-08).
    
    Het is een inschatting van evenwichtsbodemveranderingen
    in het zomerbed die als gevolg van een ingreep en zonder
    aangepast beheer na lange tijd ontstaan.
    
    Dit betreft het effect op de bodem in [m]:
    
        jaargemiddeld zonder baggeren
        maximaal (na hoogwater) zonder baggeren
        minimaal (na laagwater) zonder baggeren
    
    Met deze bodemveranderingen kunnen knelpunten worden
    gesignaleerd. De resultaten zijn niet direkt geschikt
    voor het bepalen van de invloed op vaargeulonderhoud!
    
    De jaarlijkse sedimentvracht door de rivier bepaalt de
    termijn waarbinnen dit evenwichtseffect kan ontwikkelen.'
    
    
    Dit is versie {version}.
    
    [confirm]
    Bevestig met "j" ...
    
    [confirm_or]
    Bevestig met "j", anders antwoord met "n" ...
    
    [confirm_or_restart]
    Bevestig met "j", of begin opnieuw met "n" ...
    
    ... continued ...


### analysis configuration file

The analysis configuration file follows the common ini-file format.
The file must contain a `[General]` block with a keyword `Version` to indicate the version number of the file.
The initial version number will be `1.0`.

Version 1.0 files must contain in the `[General]` block also the keywords `Branch` and `Reach` to identify the branch (in Dutch: tak) and reach (in Dutch: stuk) in which the measure is located.
The specified names may be shortened, but they should uniquely identify the branch and reach amongst the names of the other branches and reaches.
Optionally, the same block may also contain `Qmin`, `QBankfull` and `UCrit` values representative for this particular measure if they differ from those typical for the selected reach.
These items are sufficient for a basic analysis.
For a full spatial analysis the user needs to specify the names of the D-Flow FM map-files containing the results of the simulations without measure (reference) and with measure for the selected discharges Q1, Q2, and Q3.

| Block          | Keyword     | Description |
|----------------|-------------|-------------|
| General        | Version     | Version number. Must be `1.0` |
| General        | Mode        | `WAQUA export` or `D-Flow FM map` (the latter is the default) |
| General        | Branch      | Name of the selected branch   |
| General        | Reach       | Name of the selected reach    |
| General        | Qthreshold  | Threshold discharge [m3/s] at which measure becomes active |
| General        | Qbankfull   | Discharge [m3/s] at which measure reaches bankfull |
| General        | UCrit       | Critical (minimum) velocity [m/s] for sediment transport |
| Q1             | Discharge   | Discharge [m3/s] of the low flow simulation |
| Q1             | Reference   | Name of D-Flow FM map-file to be used for reference condition at Q1 |
| Q1             | WithMeasure | Name of D-Flow FM map-file that includes the measure at Q1 |
| Q2             | Discharge   | Discharge [m3/s] of the transitional regime |
| Q2             | Reference   | Name of D-Flow FM map-file to be used for reference condition at Q2 |
| Q2             | WithMeasure | Name of D-Flow FM map-file that includes the measure at Q2 |
| Q3             | Discharge   | Discharge [m3/s] of the high flow simulation |
| Q3             | Reference   | Name of D-Flow FM map-file to be used for reference condition at Q3 |
| Q3             | WithMeasure | Name of D-Flow FM map-file that includes the measure at Q3 |

The file names may be specified using relative or absolute paths.
The `Reference` and `WithMeasure` keywords are *not* used when the `Mode` equals `WAQUA export`; in that case the file name are standardized as `xyz_<quantity>-zeta.00<1/2>.Q<i>`.

**Example**

This example shows a complete analysis configuration file for a measure in the first branch/reach of the default `Dutch_rivers.cfg` configuration.
It reports the default settings.
Only the `Version`, `Branch`, `Reach`, `Reference` and `WithMeasure` keywords are required for the full analysis.

    [General]
      Version     = 1.0
      Mode        = D-Flow FM map
      Branch      = Bovenrijn & Waal
      Reach       = Bovenrijn                    km  859-867
      Qthreshold  = 1000.0
      Qbankfull   = 4000.0
      Ucrit       = 0.3
    
    [Q1]
      Discharge   = 1000.0
      Reference   = Measure42/Q1/Reference/DFM_OUTPUT_Q1/Q1_map.nc
      WithMeasure = Measure42/Q1/Updated/DFM_OUTPUT_Q1/Q1_map.nc
    
    [Q2]
      Discharge   = 4000.0
      Reference   = Measure42/Q2/Reference/DFM_OUTPUT_Q2/Q2_map.nc
      WithMeasure = Measure42/Q2/Updated/DFM_OUTPUT_Q2/Q2_map.nc
    
    [Q3]
      Discharge   = 6000.0
      Reference   = Measure42/Q3/Reference/DFM_OUTPUT_Q3/Q3_map.nc
      WithMeasure = Measure42/Q3/Updated/DFM_OUTPUT_Q3/Q3_map.nc


### simulation result files

The WAQMORF program required that the user had extracted the cell centred velocity magnitude and water depth from the the WAQUA SDS-output files and stored in `xyz_<quantity>-zeta.00<1/2>.Q<i>` files.
D-FAST Morphological Impact supports these files when running in legacy mode (see section on `dfastmi_cli`).
When building on D-Flow FM simulations, D-FAST Morphological Impact reads the results directly from the netCDF map-files.
These files may contain multiple time steps; the final time steps will be used for the analysis.


### report file

D-FAST Morphological Impact will write a report of the analysis.
This report file is a simple text file consistent with the earlier reports written by WAQMORF.
The length and content of the report vary depending on the availability of the simulation result files.


### spatial output file

The WAQMORF program wrote the spatial output in SIMONA BOX-file format which could be visualize when combined with the curvilinear grid of the original simulation.
D-FAST Morphological Impact still generates such files when run in legacy mode based on WAQUA results (see the `cli` section).

D-FAST Morphological Impact generates one UGRID netCDF file containing the spatial results of the analysis.
The mesh information is copied from the D-Flow FM map file and the three data fields (erosion and sedimentation patterns for mean, minimum, and maximum impact) follow standardized conventions for data stored at cell centres (`face`-values) on an unstructured mesh.
As a result the data may be visualized using a number of visualization tools such as QUICKPLOT and QGIS.


## Listing of Modules

D-FAST Morphological Impact Python module is subdivided into 6 files:

* `cmd.py` main file to start the module in any mode
* `batch.py` for the batch mode
* `cli.py` for the interactive command line interface (equivalent to WAQMORF)
* `gui.py` for the graphical user interface
* `io.py` for all file handling: reading of input and configuration files as well as writing of results files.
* `kernel.py` for all scientific steps of the algorithm

Each file is addressed separately in the following subsections.

### main function and command line interface `cmd.py`

This file implements the main routine and the parsing of the command line arguments.
Depending on the command line arguments it will run in one of three modes:

1. Legacy mode mimicking the existing WAQMORF program (`cli`).
It uses the same input and output files (report file and SIMONA BOX-files), but uses the new implementation of the algorithm and various configuration files.
2. Batch mode using input file (`batch`).
It takes the analysis configuration file as input, obtains the relevant data from the old SIMONA files or the new D-Flow FM result files and writes output files (report file and SIMONA BOX-file or netCDF map-file depending on the selected input format).
3. Graphical user interface (`gui`).
It allows the user to interactively specify the parameters needed for the analysis. The settings can be saved for later batch processing or a batch analysis can be started immediately.

The following command line options are supported

| short | long             | description                                       |
|-------|:-----------------|:--------------------------------------------------|
| -h    | --help           | show help text and exit                           |
| -r    | --rivers         | name of river configuration file                  |
| -l    | --language       | language selection: `NL` or `UK` (default: `UK`)  |
| -m    | --mode           | run mode `cli`, `batch` or `gui`                  |
| -i    | --config         | name of analysis configuration file               |
|       | --reduced_output | write reduced SIMONA BOX files (legacy mode only) |

This file contains one routine:

* `parse_arguments` parses the command line arguments and decide on batch mode or legacy interactive mode

and the main code that triggers the parsing of the command line arguments, loads the language file, and starts the software in the selected mode.

### batch mode `batch.py`

This file executes the analysis in batch mode based on a specified analysis configuration file.
This run mode is triggered by calling the program using the command line argument `--mode batch`.
It supports both new and old simulation result files.

* `batch_mode` reads the configuration file and triggers the core batch mode analysis
* `batch_mode_core` carry out the analysis and report the results
* `countQ` count the number of discharges for which simulations results need to be provided
* `batch_get_discharges` extract the discharges to be simulated from the configuration file
* `get_filenames` extract the simulation result file names
* `analyse_and_report` perform analysis and report results
* `analyse_and_report_waqua` perform analysis based on SIMONA result files and report results
* `analyse_and_report_dflowfm` perform analysis based on D-Flow Flexible Mesh result files and report results
* `get_values_waqua1` extract one data column from SIMONA result file
* `get_values_waqua3` extract three data columns from SIMONA result file
* `get_values_fm` extract results from a D-Flow Flexible Mesh result file
* `write_report` write the report file
* `config_to_absolute_paths` convert all file names in an analysis configuration to absolute paths
* `load_configuration_file` load a configuration file and adjust file names to absolute paths
* `config_to_relative_paths` convert all file names in an analysis configuration to relative paths
* `save_configuration_file` adjust file names to relative paths and save the configuration file
* `stagename` returns the dictionary key for one of the three discharge levels

### interactive command line interface `cli.py`

This file implements the legacy WAQMORF mode of running as an interactive command line program which may be used as batch mode by redirecting standard in; in this mode only result files exported from SIMONA can be used.
This run mode is triggered by calling the program using the command line argument `--mode cli`.

* `interactive_mode` implements the overall interactive loop
* `interactive_mode_opening` displays the opening texts of the program
* `interactive_get_location` implements the interactive selection of the branch/reach location
* `interactive_get_discharges` implements the interactive selection of the discharges

* `write_report_nodata` writes the report in case simulation results are not available
* `interactive_check_discharge` to interactively verify whether simulation results are available for the requested discharges Q1, Q2 and Q3 and if not query for which alternative discharges then
* `interactive_get_bool`, `interactive_get_int`, `interactive_get_float` and `interactive_get_item` support functions to get boolean, integer, floating point input or branch/reach index from user interaction (legacy mode)

### graphical user interface `gui.py`

This file implements the graphical user interface version of D-FAST Morphological Impact.
It can be used to generate and edit the analysis configuration files used for evaluating a single measure.
This run mode is triggered by calling the program using the command line argument `--mode gui` or by not specifying a `--mode` argument since this is the default run mode.
It supports both new and old simulation result files.

![Example of the main dialog](main_dialog.png "Example of the main dialog")

This module is subdivided into the following routines:

* `gui_text` obtains a gui text from the global dictionary of dialog texts
* `create_dialog` to create the graphical user interface
* `activate_dialog` to hand over control to the user interface
* `updated_mode` react to a switch between `WAQUA export` and `D-Flow FM map` modes
* `updated_branch` react to a change in branch selection
* `updated_reach` react to a change in reach selection
* `update_qvalues` update the discharge values in the dialog and indicate the impacted length
* `close_dialog` support function to close the dialog and end the program
* `menu_load_configuration` callback function to ask for an analysis configuration file and trigger loading of that file
* `load_configuration` function to actually load an analysis configuration file and update the user interface
* `menu_save_configuration` callback function to ask for a file name and trigger saving the configuration under that name
* `get_configuration` function to actually extract a configuration from the user interface
* `run_analysis` callback function to run the analysis, generate report and result file (implemented via call to `batch_mode`)
* `menu_about_self` and `menu_about_qt` callback functions to show About boxes
* `main` main routine creating the user interface, optionally load a configuration, and hand over control to the dialog

* `openFileLayout` support function to create a dialog entries of a text field with a browse for file option for all simulation result files options
* `selectFile` support function to select a D-Flow FM result file
* `showMessage` support function to show a message dialog
* `showError` support function to show an error dialog

### general input/output `io.py`

The `io.py` file contains all generic file handling routines for reading configuration files, processing netCDF input and output files, and functions to support legacy input and output formats.

* `load_program_texts` fills a global dictionary of dialog texts by reading the dialog text configuration file
* `log_text` obtains one text from the global dictionary of dialog texts and writes it to screen or file
* `get_filename` obtains a file name from the global dictionary of dialog texts
* `get_text` obtain one text from the global dictionary of dialog texts

* `read_rivers` reads the rivers configuration file
* `collect_values1` support function for collecting branch/reach data for a parameter with one value, e.g. `PRHigh`
* `collect_values2` support function for collecting branch/reach data for a parameter with two values, e.g. `QFit`
* `collect_values4` support function for collecting branch/reach data for a parameter with four values, e.g. `QLevels`
* `write_config` support function to write a nicely formatted analysis configuration file

* `read_fm_map` for reading data fields from the D-Flow FM map-file
* `get_mesh_and_facedim_names` for obtaining the name of the 2D mesh and the name of the corresponding face dimension
* `copy_ugrid` for copying UGRID mesh information from the D-Flow FM map-file to the spatial output file
* `copy_var` support function for copying an individual netCDF variable from netCDF file to another
* `ugrid_add` for adding a single cell centred variable to a netCDF file containing UGRID mesh data

* `read_waqua_xyz` for reading the xyz-files containing data exported from the WAQUA model (legacy function)
* `write_simona_box` for writing a SIMONA BOX-file (legacy function)

* `absolute_path` converts a relative path into an absolute path given a reference path
* `relative_path` converts an absolute path into a path relative to a given reference path

### core algorithm `kernel.py`

The `dfastmi.py` file contains all routines for that perform the mathematical processing steps of the algorithm.
This module also contains the main version number.

* `char_discharges` for determining the characteristic discharges Q1, Q2 and Q3
* `char_times` for computing the associated time and weight factors
* `estimate_sedimentation_length` for computing the characteristic length scale of the impact
* `dzq_from_du_and_h` for computing the spatial pattern of dzq based on the change in velocity magnitude and local water depth
* `main_computation` for computing the minimum, mean and maximum impact patterns of the measure on the bed levels after one year


# Software Maintenance

Currently we are at the stage of prototyping, but the end goal of the project is to deliver a formal maintained product.
This means that we will be following a set of best practices for software maintenance to assure the quality of the product.

## Coding Guidelines

This program has been implemented following the Python PEP 8 style guide using Python 3.8.
The code has been documented using standard Python docstrings and type hinting.
For the static type checker _mypy_ is used.

    pip install mypy
    mypy dfastbe

Variables associated with NumPy, netCDF4 and PyQt5 are not yet properly type checked.

    mypy dfastmi
    dfastmi\kernel.py:35: error: Skipping analyzing 'numpy': found module but no type hints or library stubs
    dfastmi\io.py:32: error: Skipping analyzing 'numpy': found module but no type hints or library stubs
    dfastmi\io.py:33: error: Skipping analyzing 'netCDF4': found module but no type hints or library stubs
    dfastmi\batch.py:36: error: Skipping analyzing 'numpy': found module but no type hints or library stubs
    dfastmi\batch.py:36: note: See https://mypy.readthedocs.io/en/latest/running_mypy.html#missing-imports
    dfastmi\gui.py:33: error: Skipping analyzing 'PyQt5': found module but no type hints or library stubs
    dfastmi\gui.py:34: error: Skipping analyzing 'PyQt5.QtGui': found module but no type hints or library stubs
    dfastmi\gui.py:491: error: Cannot assign to a method
    dfastmi\gui.py:491: error: Incompatible types in assignment (expression has type "Type[str]", variable has type "Callable[[str], str]")
    dfastmi\cli.py:35: error: Skipping analyzing 'numpy': found module but no type hints or library stubs
    dfastmi\cmd.py:35: error: Skipping analyzing 'numpy': found module but no type hints or library stubs
    Found 10 errors in 6 files (checked 8 source files)

The final two errors report (`dfastmi\\gui.py:491`) are caused by a statement to switch the configparser to case sensitive mode while creating the data structure to be saved to file; most likely the data type is not properly set in the configparser definition.
The code works conforms to the configparser documentation and works properly as is.

A consistent coding style is enforced by means of the _Black Code Formatter_.

    pip install black
    black dfastmi

## Version Control

GitHub is used for software version control.
The repository is located at https://github.com/Deltares/D-FAST_Morphological_Impact.
Since D-FAST Morphological Impact builds on WAQMORF, the initial release of the new Python product is labeled as version 2.0.0.

## Automated Building and Testing of Code

Automated TeamCity projects will be set up for testing the Python code, for building (and optionally signing of) binaries, and testing of the binaries.
In this way the formal release process can be easily aligned with the other products.
This is ongoing work; the test and build steps are currently run locally

    ================================================= test session starts ==================================================
    platform win32 -- Python 3.8.2, pytest-6.1.2, py-1.9.0, pluggy-0.13.1
    rootdir: D:\checkouts\D-FAST\D-FAST_Morphological_Impact
    collected 65 items
    
    tests\test_batch.py ...                                                                                           [  4%]
    tests\test_cli.py ..                                                                                              [  7%]
    tests\test_io.py ........................................                                                         [ 69%]
    tests\test_kernel.py ....................                                                                         [100%]
    
    ================================================== 65 passed in 1.43s ==================================================

The results of the software is verified by means of

1. Unit testing at the level of functions, such as reading and writing of files, and basic testing of the algorithms.
All functions included in `io.py` and `kernel.py` are covered by unit tests.
These tests are carried out by means of the `pytest` framework.
1. Regression tests have been set up to verify that the results of the command line interactive mode (with redirected standard in input for files coming from WAQUA) and the batch mode (with configuration file input for files coming from either WAQUA or D-Flow FM) remain unchanged under further code developments.

For the regression tests four sets of input files have been selected:

1. One set of legacy input files coming from WAQUA.
Running D-FAST Morphological Impact on those converted files gives identical results in the same file format as WAQMORF.
1. Those WAQUA results have been converted to a set of D-Flow FM like netCDF files.
Running D-FAST Morphological Impact on those converted files gives identical numerical results but stored in the new netCDF file format.
1. For the same case a set of D-Flow FM simulations was carried out using the same curvilinear mesh as was used in WAQUA.
Since the D-Flow FM results differ from those obtained from WAQUA, the results of D-FAST Morphological Impact are also slightly different.
However, the geometry of this set uses basically the same geometry as the first two sets.
1. Finally, also a set of D-Flow FM simulations using a new unstructured mesh was carried for the same case.
In this case both the geometry and simulation results differ, the D-FAST Morphological Impact are hence also slightly different.

## Automated Generation of Documentation

The documentation has been written in a combination of LaTeX and markdown files which are maintained in the GitHub repository alongside the source code.
The PDF version of the user manual and this technical reference manual are generated automatically as part of the daily cycle of building all manuals on the Deltares TeamCity server.