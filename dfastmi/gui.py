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


def gui_text(key, prefix = "gui_", dict = {}):
    cstr = dfastmi.io.program_texts(prefix + key)
    str = cstr[0].format(**dict)
    return str


def create_dialog():
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
    qmin = QtWidgets.QLineEdit(win)
    qmin.setValidator(PyQt5.QtGui.QDoubleValidator())
    qmin.editingFinished.connect(updated_qmin_or_qbf)
    qmin.setToolTip(gui_text("qmin_tooltip"))
    dialog["qmin"] = qmin
    layout.addRow(gui_text("qmin"), qmin)

    # bankvullend vanaf qbank?
    qbf = QtWidgets.QLineEdit(win)
    qbf.setValidator(PyQt5.QtGui.QDoubleValidator())
    qbf.editingFinished.connect(updated_qmin_or_qbf)
    qbf.setToolTip(gui_text("qbf_tooltip"))
    dialog["qbf"] = qbf
    layout.addRow(gui_text("qbf"), qbf)

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


def activate_dialog(dialog):
    app = dialog["application"]
    win = dialog["window"]
    win.show()
    sys.exit(app.exec_())


def updated_mode(imode):
    # enable file selection if imode == 1 (D-Flow FM map)
    DFlowFM = imode==1
    for q in range(3):
        for f in range(2):
            qstr = "q{}file{}".format(q+1, f+1)
            dialog[qstr].setEnabled(DFlowFM)
            dialog[qstr + "_txt"].setEnabled(DFlowFM)
            dialog[qstr + "_openfile"].setEnabled(DFlowFM)


def updated_branch(ibranch):
    reach = dialog["reach"]
    reach.clear()
    reach.addItems(rivers["reaches"][ibranch])

    dialog["qloc"].setText(rivers["qlocations"][ibranch])


def updated_reach(ireach):
    ibranch = dialog["branch"].currentIndex()
    dialog["qmin"].setText(str(rivers["qmin"][ibranch][ireach]))
    dialog["qbf"].setText(str(rivers["qbankfull"][ibranch][ireach]))
    dialog["ucrit"].setText(str(rivers["ucritical"][ibranch][ireach]))
    update_qvalues()


def updated_qmin_or_qbf():
    update_qvalues()


def update_qvalues():
    ibranch = dialog["branch"].currentIndex()
    ireach = dialog["reach"].currentIndex()

    try:
        qmin = float(dialog["qmin"].text())
    except:
        showError(gui_text("error_qmin"))
        dialog["qmin"].setFocus()

    try:
        qbf = float(dialog["qbf"].text())
    except:
        showError(gui_text("error_qbf"))
        dialog["qbf"].setFocus()

    try:
        qlevels = rivers["qlevels"][ibranch][ireach]
        dq = rivers["dq"][ibranch][ireach]
        Q = dfastmi.kernel.char_discharges(qlevels, dq, qmin, qbf)

        qfit = rivers["qfit"][ibranch][ireach]
        qstagnant = rivers["qstagnant"][ibranch][ireach]
        celerity_hg = rivers["proprate_high"][ibranch][ireach]
        celerity_lw = rivers["proprate_low"][ibranch][ireach]
        nwidth = rivers["normal_width"][ibranch][ireach]
        tstag, T, rsigma = dfastmi.kernel.char_times(
            qfit, qstagnant, Q, celerity_hg, celerity_lw, nwidth
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


def openFileLayout(win, myWidget, key):
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


def selectFile(key):
    fil = QtWidgets.QFileDialog.getOpenFileName(
        caption=gui_text("select_map_file"), filter="D-Flow FM Map Files (*map.nc)"
    )
    if fil[0] != "":
        dialog[key].setText(fil[0])


def close_dialog():
    dialog["window"].close()


def load_configuration(filename = None):
    if filename is None:
        fil = QtWidgets.QFileDialog.getOpenFileName(
            caption = gui_text("select_cfg_file"), filter = "Config Files (*.cfg)"
        )
        filename = fil[0]
    if filename == "":
        return

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
    dialog["qmin"].setText(
        section.get("Qmin", str(rivers["qmin"][ibranch][ireach]))
    )
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
    load_configuration()


def showMessage(message):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def showError(message):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def get_configuration():
    config = configparser.ConfigParser()
    config.optionxform = str
    config.add_section("General")
    config["General"]["Version"] = "1.0"
    config["General"]["Branch"] = dialog["branch"].currentText()
    config["General"]["Reach"] = dialog["reach"].currentText()
    config["General"]["Mode"] = dialog["mode"].currentText()
    config["General"]["Qmin"] = dialog["qmin"].text()
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


def menu_save_configuration(checked):
    fil = QtWidgets.QFileDialog.getSaveFileName(
        caption=gui_text("save_cfg_as"), filter="Config Files (*.cfg)"
    )
    filename = fil[0]
    if filename == "":
        return

    config = get_configuration()
    dfastmi.cli.save_configuration_file(filename, config)


def run_analysis():
    config = get_configuration()
    failed = dfastmi.cli.batch_mode_core(rivers, False, config)
    if failed:
        showError(gui_text("error_during_analysis", dict={"report": dfastmi.cli.getfilename("report.out")}))
    else:
        showMessage(gui_text("end_of_analysis", dict={"report": dfastmi.cli.getfilename("report.out")}))


def menu_about_self():
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText("D-FAST Morphological Impact " + dfastmi.__version__)
    msg.setInformativeText("Copyright (c) 2020 Deltares.")
    msg.setDetailedText(gui_text("license"))
    msg.setWindowTitle(gui_text("about"))
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def menu_about_qt():
    QtWidgets.QApplication.aboutQt()


def main(rivers_configuration, config):
    global rivers
    global dialog
    
    rivers = rivers_configuration
    dialog = create_dialog()
    dialog["branch"].addItems(rivers["branches"])
    dialog["reach"].addItems(rivers["reaches"][0])
    
    if not config is None:
        load_configuration(config)
    
    activate_dialog(dialog)
