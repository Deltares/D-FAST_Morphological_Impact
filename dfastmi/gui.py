# -*- coding: utf-8 -*-
"""
Copyright (C) 2020 Stichting Deltares.

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

from typing import Dict, Any, Optional
from dfastmi.io import RiversObject

from PyQt5 import QtWidgets
import PyQt5.QtGui
import dfastmi.batch
import dfastmi.io
import dfastmi.kernel
import pathlib
import sys
import os
import configparser
import subprocess
from functools import partial

rivers: RiversObject
dialog: Dict[str, PyQt5.QtCore.QObject]


def gui_text(key: str, prefix: str = "gui_", dict: Dict[str, Any] = {}):
    """
    Query the global dictionary of texts for a single string in the GUI.

    This routine concatenates the prefix and the key to query the global
    dictionary of texts. It selects the first line of the text obtained and
    expands and placeholders in the string using the optional dictionary
    provided.

    Arguments
    ---------
    key : str
        The key string used to query the dictionary (extended with prefix).
    prefix : str
        The prefix used in combination with the key (default "gui_").
    dict : Dict[str, Any]
        A dictionary used for placeholder expansions (default empty).

    Returns
    -------
        The first line of the text in the dictionary expanded with the keys.
    """
    cstr = dfastmi.io.get_text(prefix + key)
    str = cstr[0].format(**dict)
    return str


def create_dialog() -> None:
    """
    Construct the D-FAST Morphological Impact user interface.

    Arguments
    ---------
    None
    """
    global dialog
    dialog = {}

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("fusion")
    dialog["application"] = app

    win = QtWidgets.QMainWindow()
    win.setGeometry(200, 200, 600, 300)
    win.setWindowTitle("D-FAST Morphological Impact")
    dialog["window"] = win

    menubar = win.menuBar()
    create_menus(menubar)

    central_widget = QtWidgets.QWidget()
    layout = QtWidgets.QBoxLayout(2, central_widget)
    win.setCentralWidget(central_widget)

    tabs = QtWidgets.QTabWidget(win)
    dialog["tabs"] = tabs
    layout.addWidget(tabs)

    button_bar = QtWidgets.QWidget(win)
    button_bar_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, button_bar)
    button_bar_layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(button_bar)

    run = QtWidgets.QPushButton(gui_text("action_run"), win)
    run.clicked.connect(run_analysis)
    button_bar_layout.addWidget(run)

    done = QtWidgets.QPushButton(gui_text("action_close"), win)
    done.clicked.connect(close_dialog)
    button_bar_layout.addWidget(done)
    
    add_general_tab(tabs, win)
    

def create_menus(menubar: PyQt5.QtWidgets.QMenuBar) -> None:
    """
    Add the menus to the menubar.

    Arguments
    ---------
    menubar : PyQt5.QtWidgets.QMenuBar
        Menubar to which menus should be added.
    """
    menu = menubar.addMenu(gui_text("File"))
    item = menu.addAction(gui_text("Load"))
    item.triggered.connect(menu_load_configuration)
    item = menu.addAction(gui_text("Save"))
    item.triggered.connect(menu_save_configuration)
    menu.addSeparator()
    item = menu.addAction(gui_text("Close"))
    item.triggered.connect(close_dialog)

    menu = menubar.addMenu(gui_text("Help"))
    item = menu.addAction(gui_text("Manual"))
    item.triggered.connect(menu_open_manual)
    menu.addSeparator()
    item = menu.addAction(gui_text("Version"))
    item.triggered.connect(menu_about_self)
    item = menu.addAction(gui_text("AboutQt"))
    item.triggered.connect(menu_about_qt)


def add_general_tab(
    tabs: PyQt5.QtWidgets.QTabWidget, win: PyQt5.QtWidgets.QMainWindow
) -> None:
    """
    Create the tab for the general settings.

    Arguments
    ---------
    tabs : PyQt5.QtWidgets.QTabWidget
        Tabs object to which the tab should be added.
    win : PyQt5.QtWidgets.QMainWindow
        Windows in which the tab item is located.
    """
    general_widget = QtWidgets.QWidget()
    layout = QtWidgets.QFormLayout(general_widget)
    tabs.addTab(general_widget, "General")

    # get the branch
    branch = QtWidgets.QComboBox(win)
    branch.currentIndexChanged.connect(updated_branch)
    branch.setToolTip(gui_text("branch_tooltip"))
    dialog["branch"] = branch
    layout.addRow(gui_text("branch"), branch)

    # get the reach
    reach = QtWidgets.QComboBox(win)
    reach.currentIndexChanged.connect(updated_reach)
    reach.setToolTip(gui_text("reach_tooltip"))
    dialog["reach"] = reach
    layout.addRow(gui_text("reach"), reach)

    # show the discharge location
    qloc = QtWidgets.QLabel("", win)
    qloc.setToolTip(gui_text("qloc"))
    dialog["qloc"] = qloc
    layout.addRow(gui_text("qloc"), qloc)

    # get minimum flow-carrying discharge
    qthr = QtWidgets.QLineEdit(win)
    qthr.setValidator(PyQt5.QtGui.QDoubleValidator())
    qthr.editingFinished.connect(update_qvalues)
    qthr.setToolTip(gui_text("qthr_tooltip"))
    qthrtxt = QtWidgets.QLabel(gui_text("qthr"), win)
    dialog["qthr"] = qthr
    layout.addRow(qthrtxt, qthr)

    # get critical flow velocity
    ucrit = QtWidgets.QLineEdit(win)
    ucrit.setValidator(PyQt5.QtGui.QDoubleValidator())
    ucrit.setToolTip(gui_text("ucrit_tooltip"))
    dialog["ucrit"] = ucrit
    layout.addRow(gui_text("ucrit"), ucrit)

    # show the impact length
    slength = QtWidgets.QLabel(win)
    slength.setToolTip(gui_text("length_tooltip"))
    dialog["slength"] = slength
    layout.addRow(gui_text("length"), slength)

    # get the output directory
    output_dir = QtWidgets.QLineEdit(win)
    dialog["outputDir"] = output_dir
    layout.addRow(gui_text("outputDir"), openFileLayout(win, output_dir, "outputDir"))

    # plotting
    make_plots = QtWidgets.QLabel(gui_text("makePlots"), win)
    make_plots_edit = QtWidgets.QCheckBox(win)
    make_plots_edit.setToolTip(gui_text("makePlots_tooltip"))
    make_plots_edit.stateChanged.connect(update_plotting)
    dialog["makePlots"] = make_plots
    dialog["makePlotsEdit"] = make_plots_edit
    layout.addRow(make_plots, make_plots_edit)

    save_plots = QtWidgets.QLabel(gui_text("savePlots"), win)
    save_plots.setEnabled(False)
    save_plots_edit = QtWidgets.QCheckBox(win)
    save_plots_edit.setToolTip(gui_text("savePlots_tooltip"))
    save_plots_edit.stateChanged.connect(update_plotting)
    save_plots_edit.setEnabled(False)
    dialog["savePlots"] = save_plots
    dialog["savePlotsEdit"] = save_plots_edit
    layout.addRow(save_plots, save_plots_edit)

    figure_dir = QtWidgets.QLabel(gui_text("figureDir"), win)
    figure_dir.setEnabled(False)
    figure_dir_edit = QtWidgets.QLineEdit(win)
    figure_dir_edit.setEnabled(False)
    dialog["figureDir"] = figure_dir
    dialog["figureDirEdit"] = figure_dir_edit
    layout.addRow(figure_dir, openFileLayout(win, figure_dir_edit, "figureDirEdit"))
    dialog["figureDirEditFile"].setEnabled(False)

    close_plots = QtWidgets.QLabel(gui_text("closePlots"), win)
    close_plots.setEnabled(False)
    close_plots_edit = QtWidgets.QCheckBox(win)
    close_plots_edit.setToolTip(gui_text("closePlots_tooltip"))
    close_plots_edit.setEnabled(False)
    dialog["closePlots"] = close_plots
    dialog["closePlotsEdit"] = close_plots_edit
    layout.addRow(close_plots, close_plots_edit)


def add_condition_tab(
    prefix: str,
) -> None:
    """
    Create the tab for one flow conditions.

    Arguments
    ---------
    prefix : str
        Prefix for all dialog dictionary entries of this tab.
    q : float
        Discharge [m3/s]
    """
    general_widget = QtWidgets.QWidget()
    layout = QtWidgets.QFormLayout(general_widget)
    dialog["tabs"].addTab(general_widget, prefix+"tab")
    win = dialog["window"]

    # show the discharge location
    qloc = QtWidgets.QLabel("", win)
    qloc.setToolTip(gui_text("qloc"))
    dialog[prefix+"qloc"] = qloc
    layout.addRow(gui_text("qloc"), qloc)

    # show the discharge value
    qval = QtWidgets.QLabel("", win)
    qval.setToolTip(gui_text("qval"))
    dialog[prefix+"qval"] = qval
    layout.addRow(gui_text("qval"), qval)

    # get the reference file
    q1file1 = QtWidgets.QLineEdit(win)
    dialog[prefix+"file1"] = q1file1
    layout.addRow(gui_text("reference"), openFileLayout(win, q1file1, prefix+"file1"))

    # get the file with measure
    q1file2 = QtWidgets.QLineEdit(win)
    dialog[prefix+"file2"] = q1file2
    layout.addRow(gui_text("measure"), openFileLayout(win, q1file2, prefix+"file2"))


def activate_dialog() -> None:
    """
    Activate the user interface and run the program.

    Arguments
    ---------
    None
    """
    app = dialog["application"]
    win = dialog["window"]
    win.show()
    sys.exit(app.exec_())


def updated_branch(ibranch: int) -> None:
    """
    Adjust the GUI for updated branch selection.

    Arguments
    ---------
    ibranch : int
        Newly selected branch number.
    """
    reach = dialog["reach"]
    reach.clear()
    reach.addItems(rivers["reaches"][ibranch])

    dialog["qloc"].setText(rivers["qlocations"][ibranch])


def updated_reach(ireach: int) -> None:
    """
    Adjust the GUI for updated reach selection.

    Arguments
    ---------
    ireach : int
        Newly selected reach number.
    """
    ibranch = dialog["branch"].currentIndex()

    q_stagnant = rivers["qstagnant"][ibranch][ireach]
    dialog["qthr"].setText(str(q_stagnant))
    dialog["ucrit"].setText(str(rivers["ucritical"][ibranch][ireach]))
    update_qvalues()


def update_qvalues() -> None:
    """
    Adjust the GUI for updated characteristic discharges.

    Arguments
    ---------
    None
    """
    ibranch = dialog["branch"].currentIndex()
    ireach = dialog["reach"].currentIndex()
    if ireach < 0:
        return

    hydro_q = rivers["hydro_q"][ibranch][ireach]
    tabs = dialog["tabs"]
    for j in range(tabs.count()-2,-1,-1):
        if j >= len(hydro_q):
            tabs.removeTab(1+j)
        else:
            prefix = str(j)+"_"
            qval = str(hydro_q[j])
            dialog[prefix+"qloc"].setText(rivers["qlocations"][ibranch])
            dialog[prefix+"qval"].setText(qval)
            tabs.setTabText(1+j,qval+" m3/s")
    
    if len(hydro_q) > tabs.count()-1:
        for j in range(tabs.count()-1, len(hydro_q)):
            prefix = str(j)+"_"
            add_condition_tab(prefix)
            qval = str(hydro_q[j])	
            dialog[prefix+"qloc"].setText(rivers["qlocations"][ibranch])
            dialog[prefix+"qval"].setText(qval)
            tabs.setTabText(1+j,qval+" m3/s")
            
    try:
        nwidth = rivers["normal_width"][ibranch][ireach]
        q_threshold = float(dialog["qthr"].text())
        [_, _, time_mi, _, _, _, celerity] = dfastmi.batch.get_levels_v2(rivers, ibranch, ireach, q_threshold, nwidth)
        slength = dfastmi.kernel.estimate_sedimentation_length2(time_mi, celerity)
        dialog["slength"].setText("{:.0f}".format(slength))
    except:
        dialog["slength"].setText("---")


def update_plotting() -> None:
    """
    Update the plotting flags.
    
    Arguments
    ---------
    None
    """
    plot_flag = dialog["makePlotsEdit"].isChecked()
    dialog["savePlots"].setEnabled(plot_flag)
    dialog["savePlotsEdit"].setEnabled(plot_flag)

    save_flag = dialog["savePlotsEdit"].isChecked() and plot_flag

    dialog["figureDir"].setEnabled(save_flag)
    dialog["figureDirEdit"].setEnabled(save_flag)
    dialog["figureDirEditFile"].setEnabled(save_flag)

    dialog["closePlots"].setEnabled(plot_flag)
    dialog["closePlotsEdit"].setEnabled(plot_flag)


def close_dialog() -> None:
    """
    Close the dialog and program.

    Arguments
    ---------
    None
    """
    dialog["window"].close()


def menu_load_configuration() -> None:
    """
    Ask for a configuration file name and update GUI based on its content.

    Arguments
    ---------
    None
    """
    fil = QtWidgets.QFileDialog.getOpenFileName(
        caption=gui_text("select_cfg_file"), filter="Config Files (*.cfg)"
    )
    filename = fil[0]
    if filename != "":
        load_configuration(filename)


def load_configuration(filename: str) -> None:
    """
    Open a configuration file and update the GUI accordingly.

    This routines opens the specified configuration file and updates the GUI
    to reflect it contents.

    Arguments
    ---------
    filename : str
        Name of the configuration file to be opened.
    """
    try:
        config = dfastmi.batch.load_configuration_file(filename)
    except:
        if filename != "dfastmi.cfg":
            showError(gui_text("file_not_found", prefix="", dict={"name": filename}))
        return

    section = config["General"]
    dialog["branch"].setCurrentText(section["Branch"])
    ibranch = dialog["branch"].currentIndex()
    dialog["reach"].setCurrentText(section["Reach"])
    ireach = dialog["reach"].currentIndex()

    dialog["qthr"].setText(
        section.get("Qthreshold", str(rivers["qstagnant"][ibranch][ireach]))
    )

    dialog["ucrit"].setText(
        section.get("Ucrit", str(rivers["ucritical"][ibranch][ireach]))
    )
    
    dialog["outputDir"].setText(
        section.get("OutputDir", "output")
    )
    dialog["makePlotsEdit"].setChecked(
        str_to_bool(section.get("Plotting", "false"))
    )
    dialog["savePlotsEdit"].setChecked(
        str_to_bool(section.get("SavePlots", "false"))
    )
    dialog["figureDirEdit"].setText(
        section.get("FigureDir", "figure")
    )
    dialog["closePlotsEdit"].setChecked(
        str_to_bool(section.get("ClosePlots", "false"))
    )
    update_qvalues()
    
    hydro_q = rivers["hydro_q"][ibranch][ireach]
    for i in range(len(hydro_q)):
        prefix = str(i)+"_"
        cond = "C{}".format(i+1)
        if cond in config.keys():
            cond_section = config[cond]
            file1 = cond_section.get("Reference", "")
            file2 = cond_section.get("WithMeasure", "")
        else:
            file1 = ""
            file2 = ""
        dialog[prefix+"file1"].setText(file1)
        dialog[prefix+"file2"].setText(file2)


def str_to_bool(x: str) -> bool:
    """
    Convert a string to a boolean.

    Arguments
    ---------
    x : str
        String to be interpreted.
    """
    val = x.lower() in ['true', '1', 't', 'y', 'yes']
    return val


def menu_save_configuration() -> None:
    """
    Ask for a configuration file name and save GUI selection to that file.

    Arguments
    ---------
    None
    """
    fil = QtWidgets.QFileDialog.getSaveFileName(
        caption=gui_text("save_cfg_as"), filter="Config Files (*.cfg)"
    )
    filename = fil[0]
    if filename != "":
        config = get_configuration()
        dfastmi.batch.save_configuration_file(filename, config)


def get_configuration() -> configparser.ConfigParser:
    """
    Extract a configuration from the GUI.

    Arguments
    ---------
    None

    Returns
    -------
    config : Optional[configparser.ConfigParser]
        Configuration for the D-FAST Morphological Impact analysis.
    """
    config = configparser.ConfigParser()
    config.optionxform = str
    config.add_section("General")
    config["General"]["Version"] = "2.0"
    config["General"]["Branch"] = dialog["branch"].currentText()
    config["General"]["Reach"] = dialog["reach"].currentText()
    config["General"]["Qthreshold"] = dialog["qthr"].text()
    config["General"]["Ucrit"] = dialog["ucrit"].text()
    config["General"]["OutputDir"] = dialog["outputDir"].text()
    config["General"]["Plotting"] = str(dialog["makePlotsEdit"].isChecked())
    config["General"]["SavePlots"] = str(dialog["savePlotsEdit"].isChecked())
    config["General"]["FigureDir"] = dialog["figureDirEdit"].text()
    config["General"]["ClosePlots"] = str(dialog["closePlotsEdit"].isChecked())

    # loop over conditions cond = "C1", "C2", ...
    ibranch = dialog["branch"].currentIndex()
    ireach = dialog["reach"].currentIndex()
    hydro_q = rivers["hydro_q"][ibranch][ireach]
    for i in range(len(hydro_q)):
        cond = "C{}".format(i+1)
        config.add_section(cond)
        prefix = str(i)+"_"
        config[cond]["Discharge"] = dialog[prefix+"qval"].text()
        config[cond]["Reference"] = dialog[prefix+"file1"].text()
        config[cond]["WithMeasure"] = dialog[prefix+"file2"].text()
    
    return config


def run_analysis() -> None:
    """
    Run the D-FAST Morphological Impact analysis based on settings in the GUI.

    Arguments
    ---------
    None
    """
    config = get_configuration()
    if dfastmi.batch.check_configuration(rivers, config):
        try:
            success = dfastmi.batch.batch_mode_core(rivers, False, config)
        except:
            success = False
        report = dfastmi.io.get_filename("report.out")
        if success:
            showMessage(gui_text("end_of_analysis", dict={"report": report},))
        else:
            showError(gui_text("error_during_analysis", dict={"report": report},))
    else:
        showError(gui_text("analysis_config_incomplete",))


def menu_about_self() -> None:
    """
    Show the about dialog for D-FAST Morphological Impact.

    Arguments
    ---------
    None
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText("D-FAST Morphological Impact " + dfastmi.__version__)
    msg.setInformativeText("Copyright (c) 2020 Deltares.")
    msg.setDetailedText(gui_text("license"))
    msg.setWindowTitle(gui_text("about"))
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def menu_about_qt() -> None:
    """
    Show the about dialog for Qt.

    Arguments
    ---------
    None
    """
    QtWidgets.QApplication.aboutQt()


def menu_open_manual():
    """
    Open the user manual.

    Arguments
    ---------
    None
    """
    progloc = dfastmi.io.get_progloc()
    filename = progloc + os.path.sep + "dfastmi_usermanual.pdf"
    subprocess.Popen(filename, shell=True)


def main(rivers_configuration: RiversObject, config: Optional[str] = None) -> None:
    """
    Start the program for selected river system and optional configuration.

    Arguments
    ---------
    rivers_configuration : RiversObject
        A dictionary containing the river data.
    config : Optional[str]
        Optional name of configuration file.
    """
    global rivers
    global dialog

    rivers = rivers_configuration
    create_dialog()
    dialog["branch"].addItems(rivers["branches"])

    if not config is None:
        load_configuration(config)

    activate_dialog()


def openFileLayout(win, myWidget, key: str):
    """
    Add an open line to the dialog.

    Arguments
    ---------
    win
        Main window of the dialog.
    myWidget
        Line edit widget to display the file name.
    key : str
        Base name of the Widgets on this file.
    """
    parent = QtWidgets.QWidget()
    gridly = QtWidgets.QGridLayout(parent)
    gridly.setContentsMargins(0, 0, 0, 0)
    gridly.addWidget(myWidget, 0, 0)

    progloc = str(pathlib.Path(__file__).parent.absolute())
    openFile = QtWidgets.QPushButton(
        PyQt5.QtGui.QIcon(progloc + os.path.sep + "open.png"), "", win
    )
    openFile.clicked.connect(partial(selectFile, key))
    dialog[key + "File"] = openFile
    gridly.addWidget(openFile, 0, 2)

    return parent


def selectFile(key: str) -> None:
    """
    Select a D-Flow FM Map file and show in the GUI.

    Arguments
    ---------
    key : str
        Name of the field for which to select the file.
    """
    fil = QtWidgets.QFileDialog.getOpenFileName(
        caption=gui_text("select_map_file"), filter="D-Flow FM Map Files (*map.nc)"
    )
    if fil[0] != "":
        dialog[key].setText(fil[0])


def showMessage(message: str) -> None:
    """
    Display an information message box with specified string.

    Arguments
    ---------
    message : str
        Text to be displayed in the message box.
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle("Information")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def showError(message: str) -> None:
    """
    Display an error message box with specified string.

    Arguments
    ---------
    message : str
        Text to be displayed in the message box.
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()
