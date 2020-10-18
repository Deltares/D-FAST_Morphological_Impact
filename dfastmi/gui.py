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
import dfastmi.io
import dfastmi.kernel
import pathlib
import sys
import os
import configparser
from functools import partial


def gui_text(key):
    cstr = dfastmi.io.program_texts("gui_" + key)
    return cstr[0]

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
    item.triggered.connect(load_configuration)
    item = menu.addAction(gui_text("Save"))
    item.triggered.connect(save_configuration)
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

    q1 = QtWidgets.QLabel(win)
    q1.setToolTip(gui_text("q1_tooltip"))
    dialog["q1"] = q1
    layout.addRow(gui_text("q1"), q1)
    q1file1 = QtWidgets.QLineEdit(win)
    dialog["q1file1"] = q1file1
    layout.addRow(gui_text("q1_reference"), openFileLayout(win, q1file1, "q1file1"))
    q1file2 = QtWidgets.QLineEdit(win)
    dialog["q1file2"] = q1file2
    layout.addRow(gui_text("q1_measure"), openFileLayout(win, q1file2, "q1file2"))

    q2 = QtWidgets.QLabel(win)
    q2.setToolTip(gui_text("q2_tooltip"))
    dialog["q2"] = q2
    layout.addRow(gui_text("q2"), q2)
    q2file1 = QtWidgets.QLineEdit(win)
    dialog["q2file1"] = q2file1
    layout.addRow(gui_text("q2_reference"), openFileLayout(win, q2file1, "q2file1"))
    q2file2 = QtWidgets.QLineEdit(win)
    dialog["q2file2"] = q2file2
    layout.addRow(gui_text("q2_measure"), openFileLayout(win, q2file2, "q2file2"))

    q3 = QtWidgets.QLabel(win)
    q3.setToolTip(gui_text("q3_tooltip"))
    dialog["q3"] = q3
    layout.addRow(gui_text("q3"), q3)
    q3file1 = QtWidgets.QLineEdit(win)
    dialog["q3file1"] = q3file1
    layout.addRow(gui_text("q3_reference"), openFileLayout(win, q3file1, "q3file1"))
    q3file2 = QtWidgets.QLineEdit(win)
    dialog["q3file2"] = q3file2
    layout.addRow(gui_text("q3_measure"), openFileLayout(win, q3file2, "q3file2"))

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
        Q1, Q2, Q3 = dfastmi.kernel.char_discharges(qlevels, dq, qmin, qbf)

        qfit = rivers["qfit"][ibranch][ireach]
        qstagnant = rivers["qstagnant"][ibranch][ireach]
        celerity_hg = rivers["proprate_high"][ibranch][ireach]
        celerity_lw = rivers["proprate_low"][ibranch][ireach]
        nwidth = rivers["normal_width"][ibranch][ireach]
        tstag, t1, t2, t3, rsigma1, rsigma2, rsigma3 = dfastmi.kernel.char_times(
            qfit, qstagnant, Q1, Q2, Q3, celerity_hg, celerity_lw, nwidth
        )
        nlength = dfastmi.kernel.estimate_sedimentation_length(
            rsigma1, rsigma2, rsigma3, nwidth
        )
        dialog["nlength"].setText(str(nlength))
    except:
        Q1 = None
        Q2 = None
        Q3 = None
        dialog["nlength"].setText("---")

    for iq, Q in {"q1": Q1, "q2": Q2, "q3": Q3}.items():
        dialog[iq].setText(str(Q))
        dialog[iq + "file1"].setEnabled(not Q is None)
        dialog[iq + "file2"].setEnabled(not Q is None)


def openFileLayout(win, myWidget, key):
    parent = QtWidgets.QWidget()
    gridly = QtWidgets.QGridLayout(parent)
    gridly.setContentsMargins(0, 0, 0, 0)
    gridly.addWidget(myWidget, 0, 0)

    progloc = str(pathlib.Path(__file__).parent.absolute())
    openFile = QtWidgets.QPushButton(PyQt5.QtGui.QIcon(progloc + os.path.sep + "open.png"), "", win)
    openFile.clicked.connect(partial(selectFile, key))
    gridly.addWidget(openFile, 0, 2)

    return parent


def selectFile(key):
    fil = QtWidgets.QFileDialog.getOpenFileName(
        caption=gui_text("select_map_file"), filter="D-Flow FM Map Files (*map.nc)"
    )
    if fil[0] != "":
        dialog[key].setText(fil[0])


def run_analysis():
    showError(gui_text("not_yet_implemented"))


def close_dialog():
    dialog["window"].close()


def load_configuration(filename = None):
    if filename is None:
        fil = QtWidgets.QFileDialog.getOpenFileName(
            caption=gui_text("select_cfg_file"), filter="Config Files (*.cfg)"
        )
        filename = fil[0]
    if filename == "":
        return

    config = configparser.ConfigParser()
    with open(filename, "r") as configfile:
        config.read_file(configfile)
    try:
        version = config["General"]["Version"]
    except:
        showError("No version information in the file!")
        return
    if version == "1.0":
        section = config["General"]
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
        for iQ in ["Q1", "Q2", "Q3"]:
            iq = iQ.lower()
            if config.has_section(iQ):
                section = config[iQ]
                dialog[iq + "file1"].setText(section.get("Reference", ""))
                dialog[iq + "file2"].setText(section.get("WithMeasure", ""))
            else:
                dialog[iq + "file1"].setText("")
                dialog[iq + "file2"].setText("")
        update_qvalues()
    else:
        showError("Unsupported version number {} in the file!".format(version))


def showError(message):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def save_configuration():
    fil = QtWidgets.QFileDialog.getSaveFileName(
        caption=gui_text("save_cfg_as"), filter="Config Files (*.cfg)"
    )
    filename = fil[0]
    if filename == "":
        return

    config = configparser.ConfigParser()
    config.optionxform = str
    config.add_section("General")
    config["General"]["Version"] = "1.0"
    config["General"]["Branch"] = dialog["branch"].currentText()
    config["General"]["Reach"] = dialog["reach"].currentText()
    config["General"]["Qmin"] = dialog["qmin"].text()
    config["General"]["Qbankfull"] = dialog["qbf"].text()
    config["General"]["Ucrit"] = dialog["ucrit"].text()
    config.add_section("Q1")
    config["Q1"]["Reference"] = dialog["q1file1"].text()
    config["Q1"]["WithMeasure"] = dialog["q1file2"].text()
    config.add_section("Q2")
    config["Q2"]["Reference"] = dialog["q2file1"].text()
    config["Q2"]["WithMeasure"] = dialog["q2file2"].text()
    config.add_section("Q3")
    config["Q3"]["Reference"] = dialog["q3file1"].text()
    config["Q3"]["WithMeasure"] = dialog["q3file2"].text()
    dfastmi.io.write_config(filename, config)


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

def main(config):
    global rivers
    global dialog
    dialog = create_dialog()
    progloc = str(pathlib.Path(__file__).parent.absolute())
    rivers = dfastmi.io.read_rivers(progloc + os.path.sep + "rivers.ini")
    dialog["branch"].addItems(rivers["branches"])
    dialog["reach"].addItems(rivers["reaches"][0])
    if not config is None:
        load_configuration(config)
    activate_dialog(dialog)
