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

    centralWidget = QtWidgets.QWidget()
    layout = QtWidgets.QFormLayout(centralWidget)
    win.setCentralWidget(centralWidget)

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
    nlength = QtWidgets.QLabel(win)
    nlength.setToolTip(gui_text("length_tooltip"))
    dialog["nlength"] = nlength
    layout.addRow(gui_text("length"), nlength)

    # choose the flow condition
    condition_list = QtWidgets.QComboBox(win)
    #condition_list.currentIndexChanged.connect(updated_flow_condition)
    #condition_list.setToolTip(gui_text("condition_list_tooltip"))
    dialog["condition_list"] = condition_list
    layout.addRow(gui_text("condition_list"), condition_list)

    # get the reference file
    q1file1 = QtWidgets.QLineEdit(win)
    dialog["file1"] = q1file1
    layout.addRow(gui_text("reference"), openFileLayout(win, q1file1, "file1"))

    # get the file with measure
    q1file2 = QtWidgets.QLineEdit(win)
    dialog["file2"] = q1file2
    layout.addRow(gui_text("measure"), openFileLayout(win, q1file2, "file2"))

    # get the output directory
    outputDir = QtWidgets.QLineEdit(win)
    dialog["outputDir"] = outputDir
    layout.addRow(gui_text("outputDir"), openFileLayout(win, outputDir, "outputDir"))

    # plotting
    makePlots = QtWidgets.QCheckBox(win)
    makePlots.setToolTip(gui_text("makePlots_tooltip"))
    dialog["makePlots"] = makePlots
    layout.addRow(gui_text("makePlots"), makePlots)

    savePlots = QtWidgets.QCheckBox(win)
    savePlots.setToolTip(gui_text("savePlots_tooltip"))
    dialog["savePlots"] = savePlots
    layout.addRow(gui_text("savePlots"), savePlots)

    figureDir = QtWidgets.QLineEdit(win)
    dialog["figureDir"] = figureDir
    layout.addRow(gui_text("figureDir"), openFileLayout(win, figureDir, "figureDir"))

    closePlots = QtWidgets.QCheckBox(win)
    closePlots.setToolTip(gui_text("closePlots_tooltip"))
    dialog["closePlots"] = closePlots
    layout.addRow(gui_text("closePlots"), closePlots)

    run = QtWidgets.QPushButton(gui_text("action_run"), win)
    run.clicked.connect(run_analysis)
    done = QtWidgets.QPushButton(gui_text("action_close"), win)
    done.clicked.connect(close_dialog)
    rundone = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
    rundone.setContentsMargins(0, 0, 0, 0)
    rundone.addWidget(run)
    rundone.addWidget(done)
    layout.addRow("", rundone)


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


def updated_mode(imode: int) -> None:
    """
    Adjust the GUI for updated run mode selection.

    When in WAQUA mode (imode = 0) the file names are predefined and the user
    doesn't have to specify anything. When in D-Flow FM mode (imode = 1) the
    user has to specify the names of the six D-Flow FM map files.

    Arguments
    ---------
    imode : int
        Specification of run mode (0 = WAQUA, 1 = D-Flow FM).
    """
    # enable file selection if imode == 1 (D-Flow FM map)
    DFlowFM = imode == 1
    for q in range(3):
        qstr = "q{}".format(q + 1)
        active = dialog[qstr].isEnabled()
        for f in range(2):
            qstr = "q{}file{}".format(q + 1, f + 1)
            dialog[qstr].setEnabled(DFlowFM and active)
            dialog[qstr + "_txt"].setEnabled(DFlowFM and active)
            dialog[qstr + "_openfile"].setEnabled(DFlowFM and active)


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
    q_threshold: Optional[float]

    ibranch = dialog["branch"].currentIndex()
    ireach = dialog["reach"].currentIndex()
    if ireach < 0:
        return

    q_location = rivers["qlocations"][ibranch]
    q_stagnant = rivers["qstagnant"][ibranch][ireach]
    q_fit = rivers["qfit"][ibranch][ireach]
    
    conditions = ["Q = 3000 [m3/s]", "Q = 4000 [m3/s]", "Q = 6000 [m3/s]"]
    
    condition_list = dialog["condition_list"]
    condition_list.clear()
    condition_list.addItems(conditions)

    try:
        q_threshold = float(dialog["qthr"].text())
    except:
        showError(gui_text("error_qthr"))
        dialog["qthr"].setFocus()
        return


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

    qthr_default = 0 # or qstagnant of branch/reach
    dialog["qthr"].setText(
        section.get("Qthreshold", qthr_default)
    )

    dialog["ucrit"].setText(
        section.get("Ucrit", str(rivers["ucritical"][ibranch][ireach]))
    )
    
    dialog["outputDir"].setText(
        section.get("OutputDir", "output")
    )
    dialog["makePlots"].setChecked(
        str_to_bool(section.get("Plotting", "false"))
    )
    dialog["savePlots"].setChecked(
        str_to_bool(section.get("SavePlots", "false"))
    )
    dialog["figureDir"].setText(
        section.get("FigureDir", "figure")
    )
    dialog["closePlots"].setChecked(
        str_to_bool(section.get("ClosePlots", "false"))
    )
    update_qvalues()
    # show the correct file names ...


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
        if config is not None:
            dfastmi.batch.save_configuration_file(filename, config)


def get_configuration() -> Optional[configparser.ConfigParser]:
    """
    Extract a configuration from the GUI.

    Arguments
    ---------
    None

    Returns
    -------
    config : configparser.ConfigParser
        Configuration for the D-FAST Morphological Impact analysis.
    """
    error = False

    config = configparser.ConfigParser()
    config.optionxform = str
    config.add_section("General")
    config["General"]["Version"] = "2.0"
    config["General"]["Branch"] = dialog["branch"].currentText()
    config["General"]["Reach"] = dialog["reach"].currentText()
    config["General"]["Qthreshold"] = dialog["qthr"].text()
    config["General"]["Ucrit"] = dialog["ucrit"].text()
    config["General"]["OutputDir"] = dialog["outputDir"].text()
    config["General"]["Plotting"] = str(dialog["makePlots"].isChecked())
    config["General"]["SavePlots"] = str(dialog["savePlots"].isChecked())
    config["General"]["FigureDir"] = dialog["figureDir"].text()
    config["General"]["ClosePlots"] = str(dialog["closePlots"].isChecked())

    # loop over conditions cond = "C1", "C2", ...
    #error = True
    config.add_section("C1")
    config["C1"]["TODO"] = "..."
    # get discharge and optional tide
    # config[cond]["Discharge"] = qstr
    # config[cond]["Reference"] = file1
    # config[cond]["WithMeasure"] = file2
    
    if error:
        showMessage(gui_text("analysis_config_incomplete",))
        return None
    else:
        return config


def run_analysis() -> None:
    """
    Run the D-FAST Morphological Impact analysis based on settings in the GUI.

    Arguments
    ---------
    None
    """
    config = get_configuration()
    if config is not None:
        try:
            success = dfastmi.batch.batch_mode_core(rivers, False, config)
        except:
            success = False
        report = dfastmi.io.get_filename("report.out")
        if success:
            showMessage(gui_text("end_of_analysis", dict={"report": report},))
        else:
            showError(gui_text("error_during_analysis", dict={"report": report},))


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
    #dialog["reach"].addItems(rivers["reaches"][0])

    if not config is None:
        load_configuration(config)

    activate_dialog()


def openFileLayout(win, myWidget, key: str):
    """
    Add an open line to the dialog. TODO

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
    dialog[key + "_openfile"] = openFile
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
