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
import dfastmi.cli
import dfastmi.io
import dfastmi.kernel
import pathlib
import sys
import os
import configparser
from functools import partial

DialogObject = Dict[str, PyQt5.QtCore.QObject]

rivers: RiversObject
dialog: DialogObject

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
    cstr = dfastmi.io.program_texts(prefix + key)
    str = cstr[0].format(**dict)
    return str


def create_dialog() -> DialogObject:
    """
    Construct the D-FAST Morphological Impact user interface.
    
    Arguments
    ---------
    None
    
    Returns
    -------
    dialog: DialogObject
        A dictionary giving access to the QtWidgets by name.
    """
    global rivers
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
    item = menu.addAction(gui_text("Version"))
    item.triggered.connect(menu_about_self)
    item = menu.addAction(gui_text("AboutQt"))
    item.triggered.connect(menu_about_qt)

    centralWidget = QtWidgets.QWidget()
    layout = QtWidgets.QFormLayout(centralWidget)
    win.setCentralWidget(centralWidget)

    mode = QtWidgets.QComboBox(win)
    mode.addItems(["WAQUA export","D-Flow FM map"])
    mode.setCurrentIndex(1)
    mode.currentIndexChanged.connect(updated_mode)
    mode.setToolTip(gui_text("mode_tooltip"))
    dialog["mode"] = mode
    layout.addRow(gui_text("mode"), mode)
    
    branch = QtWidgets.QComboBox(win)
    branch.currentIndexChanged.connect(updated_branch)
    branch.setToolTip(gui_text("branch_tooltip"))
    dialog["branch"] = branch
    layout.addRow(gui_text("branch"), branch)

    reach = QtWidgets.QComboBox(win)
    reach.currentIndexChanged.connect(updated_reach)
    reach.setToolTip(gui_text("reach_tooltip"))
    dialog["reach"] = reach
    layout.addRow(gui_text("reach"), reach)

    qloc = QtWidgets.QLabel("", win)
    qloc.setToolTip(gui_text("qloc"))
    dialog["qloc"] = qloc
    layout.addRow(gui_text("qloc"), qloc)

    # stroomvoerend bij getrokken stuwen?
    # stroomvoerend vanaf qmin?
    qmin = QtWidgets.QCheckBox("", win)
    qmin.setToolTip(gui_text("qmin1_tooltip"))
    qmin.setChecked(True)
    qmin.stateChanged.connect(update_qvalues)
    qmintxt = QtWidgets.QLabel(gui_text("qmin1"), win)
    dialog["qmin"] = qmin
    dialog["qmin_txt"] = qmintxt
    layout.addRow(qmintxt, qmin)

    qthr = QtWidgets.QLineEdit(win)
    qthr.setValidator(PyQt5.QtGui.QDoubleValidator())
    qthr.editingFinished.connect(update_qvalues)
    qthr.setToolTip(gui_text("qthr_tooltip"))
    qthrtxt = QtWidgets.QLabel(gui_text("qthr"), win)
    dialog["qthr"] = qthr
    dialog["qthr_txt"] = qthrtxt
    layout.addRow(qthrtxt, qthr)

    # bankvullend vanaf qbank?
    qbf = QtWidgets.QLineEdit(win)
    qbf.setValidator(PyQt5.QtGui.QDoubleValidator())
    qbf.editingFinished.connect(update_qvalues)
    qbf.setToolTip(gui_text("qbf_tooltip"))
    qbftxt = QtWidgets.QLabel(gui_text("qbf"), win)
    dialog["qbf"] = qbf
    dialog["qbf_txt"] = qbftxt
    layout.addRow(qbftxt, qbf)

    for q in range(3):
        qstr = "q{}".format(q+1)

        q1 = QtWidgets.QLineEdit(win)
        q1.setValidator(PyQt5.QtGui.QDoubleValidator())
        q1.setToolTip(gui_text(qstr + "_tooltip"))
        q1txt = QtWidgets.QLabel(gui_text(qstr), win)
        dialog[qstr] = q1
        dialog[qstr + "_txt"] = q1txt
        layout.addRow(q1txt, q1)
        
        q1file1 = QtWidgets.QLineEdit(win)
        q1f1txt = QtWidgets.QLabel(gui_text(qstr + "_reference"), win)
        dialog[qstr + "file1"] = q1file1
        dialog[qstr + "file1_txt"] = q1f1txt
        layout.addRow(q1f1txt, openFileLayout(win, q1file1, qstr + "file1"))

        q1file2 = QtWidgets.QLineEdit(win)
        q1f2txt = QtWidgets.QLabel(gui_text(qstr + "_measure"), win)
        dialog[qstr + "file2"] = q1file2
        dialog[qstr + "file2_txt"] = q1f2txt
        layout.addRow(q1f2txt, openFileLayout(win, q1file2, qstr + "file2"))

    # default UCrit acceptable?
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

    run = QtWidgets.QPushButton(gui_text("action_run"), win)
    run.clicked.connect(run_analysis)
    done = QtWidgets.QPushButton(gui_text("action_close"), win)
    done.clicked.connect(close_dialog)
    rundone = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
    rundone.setContentsMargins(0, 0, 0, 0)
    rundone.addWidget(run)
    rundone.addWidget(done)
    layout.addRow("", rundone)

    return dialog


def activate_dialog(dialog: DialogObject) -> None:
    """
    Activate the user interface and run the program.
    
    Arguments
    ---------
    dialog : DialogObject
        A dictionary giving access to the QtWidgets by name.
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
    DFlowFM = imode==1
    for q in range(3):
        for f in range(2):
            qstr = "q{}file{}".format(q+1, f+1)
            dialog[qstr].setEnabled(DFlowFM)
            dialog[qstr + "_txt"].setEnabled(DFlowFM)
            dialog[qstr + "_openfile"].setEnabled(DFlowFM)


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
    
    dialog["qthr"].setText(str(rivers["qmin"][ibranch][ireach]))
    dialog["qbf"].setText(str(rivers["qbankfull"][ibranch][ireach]))
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

    q_location = rivers["qlocations"][ibranch]
    q_stagnant = rivers["qstagnant"][ibranch][ireach]
    q_min = rivers["qmin"][ibranch][ireach]
    q_fit = rivers["qfit"][ibranch][ireach]
    q_levels = rivers["qlevels"][ibranch][ireach]
    
    if q_stagnant > q_fit[0]:
        dialog["qmin"].setToolTip(gui_text("qmin1_tooltip"))
        dialog["qmin_txt"].setText(gui_text("qmin1"))
    else:
        dialog["qmin"].setToolTip(gui_text("qmin2_tooltip", dict={"border": q_location, "qmin": int(q_min)}))
        dialog["qmin_txt"].setText(gui_text("qmin2", dict={"qmin": int(q_min)}))
        
    qthrEnabled = not dialog["qmin"].isChecked()
    dialog["qthr"].setEnabled(qthrEnabled)
    dialog["qthr_txt"].setEnabled(qthrEnabled)
    if not qthrEnabled:
        dialog["qthr"].setText(str(q_levels[0]))

    if dialog["qthr"].isEnabled():
        try:
            q_threshold = float(dialog["qthr"].text())
        except:
            showError(gui_text("error_qthr"))
            dialog["qthr"].setFocus()
            return
    else:
        q_threshold = None
    
    if q_threshold is None or q_threshold < q_levels[1]:
        dialog["qbf"].setEnabled(True)
        dialog["qbf_txt"].setEnabled(True)
        
        try:
            q_bankfull = float(dialog["qbf"].text())
        except:
            showError(gui_text("error_qbf"))
            dialog["qbf"].setFocus()
            return
    else:
        dialog["qbf"].setEnabled(False)
        dialog["qbf_txt"].setEnabled(False)
        
        q_bankfull = 0

    try:
        dq = rivers["dq"][ibranch][ireach]
        Q = dfastmi.kernel.char_discharges(q_levels, dq, q_threshold, q_bankfull)

        celerity_hg = rivers["proprate_high"][ibranch][ireach]
        celerity_lw = rivers["proprate_low"][ibranch][ireach]
        nwidth = rivers["normal_width"][ibranch][ireach]
        tstag, T, rsigma = dfastmi.kernel.char_times(
            q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
        )
        nlength = dfastmi.kernel.estimate_sedimentation_length(
            rsigma, nwidth
        )
        dialog["nlength"].setText(str(nlength))
    except:
        Q = [None]*3
        dialog["nlength"].setText("---")

    DFlowFM = dialog["mode"].currentIndex() == 1
    for iq, q in {"q1": Q[0], "q2": Q[1], "q3": Q[2]}.items():
        dialog[iq].setText(str(q))
        dialog[iq].setEnabled(not q is None)
        if DFlowFM:
           dialog[iq + "file1"].setEnabled(not q is None)
           dialog[iq + "file2"].setEnabled(not q is None)


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
    openFile = QtWidgets.QPushButton(PyQt5.QtGui.QIcon(progloc + os.path.sep + "open.png"), "", win)
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


def close_dialog() -> None:
    """
    Close the dialog and program.
    
    Arguments
    ---------
    None
    """
    dialog["window"].close()


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
        config = dfastmi.cli.load_configuration_file(filename)
    except:
        showError(gui_text("file_not_found", prefix = "", dict = {"name": filename}))
        return

    section = config["General"]
    try:
        dialog["mode"].setCurrentText(section["Mode"])
    except:
        dialog["mode"].setCurrentIndex(1)
    dialog["branch"].setCurrentText(section["Branch"])
    ibranch = dialog["branch"].currentIndex()
    dialog["reach"].setCurrentText(section["Reach"])
    ireach = dialog["reach"].currentIndex()

    if section.get("Qthreshold") is None: 
        dialog["qmin"].setChecked(True)
        update_qvalues()
    else:
        dialog["qmin"].setChecked(False)
        dialog["qthr"].setText(section.get("Qthreshold"))

    dialog["qbf"].setText(
        section.get("Qbankfull", str(rivers["qbankfull"][ibranch][ireach]))
    )
    dialog["ucrit"].setText(
        section.get("Ucrit", str(rivers["ucritical"][ibranch][ireach]))
    )

    update_qvalues()
    for iQ in ["Q1", "Q2", "Q3"]:
        iq = iQ.lower()
        if config.has_section(iQ):
            section = config[iQ]
            # discharge
            dialog[iq].setText(section.get("Discharge", ""))
            dialog[iq + "file1"].setText(section.get("Reference", ""))
            dialog[iq + "file2"].setText(section.get("WithMeasure", ""))
        else:
            dialog[iq + "file1"].setText("")
            dialog[iq + "file2"].setText("")


def menu_load_configuration(checked):
    """
    Ask for a configuration file name and update GUI based on its content.
    
    Arguments
    ---------
    checked
        Dummy argument indicating whether menu item has been checked.
    """
    fil = QtWidgets.QFileDialog.getOpenFileName(
        caption = gui_text("select_cfg_file"), filter = "Config Files (*.cfg)"
    )
    filename = fil[0]
    if filename == "":
        return
    else:
        load_configuration(filename)


def showMessage(message: str):
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


def showError(message):
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


def get_configuration():
    """
    Extract a configuration from the GUI.
    
    Arguments
    ---------
    None
    
    Returns
    -------
    config
        Configuration TODO.
    """
    config = configparser.ConfigParser()
    config.optionxform = str
    config.add_section("General")
    config["General"]["Version"] = "1.0"
    config["General"]["Branch"] = dialog["branch"].currentText()
    config["General"]["Reach"] = dialog["reach"].currentText()
    config["General"]["Mode"] = dialog["mode"].currentText()
    if not dialog["qmin"].isChecked():
        config["General"]["Qthreshold"] = dialog["qthr"].text()
    if dialog["qbf"].isEnabled():
        config["General"]["Qbankfull"] = dialog["qbf"].text()
    config["General"]["Ucrit"] = dialog["ucrit"].text()
    
    DFlowFM = dialog["mode"].currentIndex() == 1
    for q in range(3):
        qstr = "q{}".format(q + 1)
        qval = dialog[qstr].text()
        if not qval == "None":
            QSTR = qstr.upper()
            config.add_section(QSTR)
            config[QSTR]["Discharge"] = qval
            if DFlowFM:
                config[QSTR]["Reference"]   = dialog[qstr + "file1"].text()
                config[QSTR]["WithMeasure"] = dialog[qstr + "file2"].text()

    return config


def menu_save_configuration(checked) -> None:
    """
    Ask for a configuration file name and save GUI selection to that file.
    
    Arguments
    ---------
    checked
        Dummy argument indicating whether menu item has been checked.
    """
    fil = QtWidgets.QFileDialog.getSaveFileName(
        caption=gui_text("save_cfg_as"), filter="Config Files (*.cfg)"
    )
    filename = fil[0]
    if filename == "":
        return

    config = get_configuration()
    dfastmi.cli.save_configuration_file(filename, config)


def run_analysis() -> None:
    """
    Run the D-FAST Morphological Impact analysis based on settings in the GUI.
    
    Arguments
    ---------
    None
    """
    config = get_configuration()
    failed = dfastmi.cli.batch_mode_core(rivers, False, config)
    if failed:
        showError(gui_text("error_during_analysis", dict={"report": dfastmi.cli.getfilename("report.out")}))
    else:
        showMessage(gui_text("end_of_analysis", dict={"report": dfastmi.cli.getfilename("report.out")}))


def menu_about_self() -> None:
    """
    Show the about dialog for D-FAST Morpholoiglcal Impact.
    
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
    dialog = create_dialog()
    dialog["branch"].addItems(rivers["branches"])
    dialog["reach"].addItems(rivers["reaches"][0])
    
    if not config is None:
        load_configuration(config)
    
    activate_dialog(dialog)
