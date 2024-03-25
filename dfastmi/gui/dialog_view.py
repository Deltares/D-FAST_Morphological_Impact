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
import os
from pathlib import Path
import subprocess
from functools import partial
import sys
from typing import Optional

from PyQt5 import QtWidgets
import PyQt5.QtGui
from PyQt5.QtGui import QIcon
from dfastmi.gui.dialog_view_model import DialogViewModel
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.RiversObject import RiversObject
from dfastmi.resources import DFAST_LOGO
import dfastmi.kernel.core

# View
class DialogView:
    _app : QtWidgets.QApplication = None
    _win : QtWidgets.QMainWindow = None
    _tabs : QtWidgets.QBoxLayout = None
    _layout : QtWidgets.QBoxLayout = None
    _menubar : QtWidgets.QMenuBar = None
    branch : QtWidgets.QComboBox = None
    reach : QtWidgets.QComboBox = None
    qloc : QtWidgets.QLabel = None
    qthr : QtWidgets.QLineEdit = None
    ucrit : QtWidgets.QLineEdit = None
    slength : QtWidgets.QLabel = None

    general_widget : QtWidgets.QWidget = None
    grid_layout : QtWidgets.QGridLayout = None
    output_dir : QtWidgets.QLineEdit = None
    make_plots_edit : QtWidgets.QCheckBox = None
    save_plots : QtWidgets.QLabel = None
    save_plots_edit : QtWidgets.QCheckBox = None
    figure_dir : QtWidgets.QLabel = None
    figure_dir_edit : QtWidgets.QLineEdit = None

    close_plots : QtWidgets.QLabel = None
    close_plots_edit : QtWidgets.QCheckBox = None

    def __init__(self, view_model: DialogViewModel):
        self.view_model = view_model
        
        # Initialize GUI components
        self.create_qt_application()
        self.create_dialog()
        self.create_menus()
        self.create_central_widget()
        self.create_tabs()
        self.create_button_bar()
        # Connect the view model's data_changed signal to update_ui slot
        self.view_model.branch_changed.connect(self.update_branch)
        self.view_model.reach_changed.connect(self.update_reach)
        self.update_qvalues_tabs()

    def update_branch(self, data):
        self.branch.setCurrentText(data)
        self.reach.clear()
        for r in self.view_model.current_branch.reaches:
            self.reach.addItem(r.name)
        self.qloc.setText(self.view_model.current_branch.qlocation)
        self.qthr.setText(str(self.view_model.qthreshold))
        self.ucrit.setText(str(self.view_model.ucritical))
        self.slength.setText(self.view_model.slength)
        self.reach.setCurrentText(self.view_model.current_reach.name)
        self.update_qvalues_tabs()
        self.output_dir.setText(self.view_model.output_dir)
        self.make_plots_edit.setChecked(self.view_model.plotting)
        self.save_plots_edit.setChecked(self.view_model.save_plots)
        self.close_plots_edit.setChecked(self.view_model.close_plots)
        self.update_condition_files()
    
    def update_reach(self, data):
        self.reach.setCurrentText(data)
        self.slength.setText(self.view_model.slength)
    
    def update_condition_files(self):
        for condition_discharge, reference_file in self.view_model.reference_files.items():
            prefix = str(condition_discharge)+"_"
            key = prefix +"file1"
            input_textbox = self.general_widget.findChild(QtWidgets.QLineEdit, key)
            if input_textbox:
                input_textbox.setText(reference_file)
        
        for condition_discharge, measure_file in self.view_model.measure_files.items():        
            prefix = str(condition_discharge)+"_"
            key = prefix +"file2"
            input_textbox = self.general_widget.findChild(QtWidgets.QLineEdit, key)
            if input_textbox:
                input_textbox.setText(measure_file)
    
    def update_qvalues_tabs(self):
        self._clear_conditions()
        for discharge in self.view_model.current_reach.hydro_q:
            prefix = str(discharge) + "_"
            qval = str(discharge) + " m3/s"
            self.add_condition_line(prefix, discharge, qval)

    def _clear_conditions(self):
        for row in range(self.grid_layout.rowCount()):
            if row > 1:        
                for col in range(self.grid_layout.columnCount()):
                    # Remove widgets from the specified row
                    item = self.grid_layout.itemAtPosition(row, col)
                    if item:
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                        else:
                            layout = item.layout()
                            if layout:
                                while layout.count():
                                    layout_item = layout.takeAt(0)
                                    if layout_item:
                                        layout_widget = layout_item.widget()
                                        if layout_widget:
                                            layout_widget.setParent(None)
                                            layout_widget.deleteLater()
        
    def create_qt_application(self) -> None:
        """
        Construct the QT application where the dialog will run in.

        Arguments
        ---------
        None
        """
        
        self._app = QtWidgets.QApplication(sys.argv)
        self._app.setStyle("fusion")

    def create_dialog(self) -> None:
        """
        Construct the D-FAST Morphological Impact user interface.

        Arguments
        ---------
        None
        """
        self._win = QtWidgets.QMainWindow()
        self._win.setGeometry(200, 200, 600, 300)
        self._win.setWindowTitle("D-FAST Morphological Impact")
        self._win.setWindowIcon(DialogView._get_dfast_icon())
    
    def create_menus(self) -> None:
        # Logic to create menus
        """
        Add the menus to the menubar.

        Arguments
        ---------
        menubar : PyQt5.QtWidgets.QMenuBar
            Menubar to which menus should be added.
        """
        menubar = self._win.menuBar()
        
        menu = menubar.addMenu(self.view_model.gui_text("File"))
        item = menu.addAction(self.view_model.gui_text("Load"))
        item.triggered.connect(self.menu_load_configuration)
        item = menu.addAction(self.view_model.gui_text("Save"))
        item.triggered.connect(self.menu_save_configuration)
        menu.addSeparator()
        item = menu.addAction(self.view_model.gui_text("Close"))
        item.triggered.connect(self.close_dialog)

        menu = menubar.addMenu(self.view_model.gui_text("Help"))
        item = menu.addAction(self.view_model.gui_text("Manual"))
        item.triggered.connect(self.menu_open_manual)
        menu.addSeparator()
        item = menu.addAction(self.view_model.gui_text("Version"))
        item.triggered.connect(self.menu_about_self)
        item = menu.addAction(self.view_model.gui_text("AboutQt"))
        item.triggered.connect(self.menu_about_qt)

    def create_central_widget(self) -> None:
        # Logic to create and set the central widget
        central_widget = QtWidgets.QWidget()
        self._layout = QtWidgets.QBoxLayout(2, central_widget)
        self._win.setCentralWidget(central_widget)        
    
    def create_tabs(self) -> None:
        # Logic to create tabs
        self._tabs = QtWidgets.QTabWidget(self._win)
        self._layout.addWidget(self._tabs)
        self.add_general_tab(self._tabs, self._win)
    
    def add_general_tab(self, tabs: PyQt5.QtWidgets.QTabWidget, win: PyQt5.QtWidgets.QMainWindow) -> None:
        """
        Create the tab for the general settings.

        Arguments
        ---------
        tabs : PyQt5.QtWidgets.QTabWidget
            Tabs object to which the tab should be added.
        win : PyQt5.QtWidgets.QMainWindow
            Windows in which the tab item is located.
        """
        self.general_widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(self.general_widget)
        tabs.addTab(self.general_widget, "General")

        # get the branch
        self.branch = QtWidgets.QComboBox(win)
        self.branch.currentTextChanged.connect(self.view_model.updated_branch)
        self.branch.setToolTip(self.view_model.gui_text("branch_tooltip"))
        for b in self.view_model.model.rivers.branches:
            self.branch.addItem(b.name)
        self.branch.setCurrentText(self.view_model.current_branch.name)
        layout.addRow(self.view_model.gui_text("branch"), self.branch)

        # get the reach
        self.reach = QtWidgets.QComboBox(win)
        self.reach.currentTextChanged.connect(self.view_model.updated_reach)
        self.reach.setToolTip(self.view_model.gui_text("reach_tooltip"))
        for r in self.view_model.current_branch.reaches:
            self.reach.addItem(r.name)
        self.reach.setCurrentText(self.view_model.current_reach.name)
        layout.addRow(self.view_model.gui_text("reach"), self.reach)

        # show the discharge location
        self.qloc = QtWidgets.QLabel("", win)
        self.qloc.setToolTip(self.view_model.gui_text("qloc"))
        self.qloc.setText(self.view_model.current_branch.qlocation)
        layout.addRow(self.view_model.gui_text("qloc"), self.qloc)

        # get minimum flow-carrying discharge
        self.qthr = QtWidgets.QLineEdit(win)
        self.qthr.setValidator(PyQt5.QtGui.QDoubleValidator())
        self.qthr.editingFinished.connect(self.update_qthreshold)
        print("Signal connected:", self.qthr.signalsBlocked())
        self.qthr.setToolTip(self.view_model.gui_text("qthr_tooltip"))
        qthrtxt = QtWidgets.QLabel(self.view_model.gui_text("qthr"), win)
        self.qthr.setText(str(self.view_model.qthreshold))
        layout.addRow(qthrtxt, self.qthr)

        # get critical flow velocity
        self.ucrit = QtWidgets.QLineEdit(win)
        self.ucrit.setValidator(PyQt5.QtGui.QDoubleValidator())
        self.ucrit.setToolTip(self.view_model.gui_text("ucrit_tooltip"))
        self.ucrit.editingFinished.connect(self.update_ucritical)
        self.ucrit.setText(str(self.view_model.ucritical))
        layout.addRow(self.view_model.gui_text("ucrit"), self.ucrit)

        # show the impact length
        self.slength = QtWidgets.QLabel(win)
        self.slength.setToolTip(self.view_model.gui_text("length_tooltip"))
        self.slength.setText(self.view_model.slength)
        layout.addRow(self.view_model.gui_text("length"), self.slength)

        # show the conditions group

         # Create a group box
        group_box = QtWidgets.QGroupBox("Output of Reference Simulations")
        group_box_layout = QtWidgets.QVBoxLayout(group_box)

        # Add widgets to the group box
        
        # Create a grid layout
        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setObjectName("discharge_conditions_grid")
        #self.grid_layout.setSpacing(10)  # Set spacing between widgets


        self.grid_layout.addWidget(QtWidgets.QLabel(self.view_model.gui_text("qloc")), 0, 0)
        self.grid_layout.addWidget(self.qloc, 0, 1)
        
        
        # Add widgets to the form layout
        discharge_label = QtWidgets.QLabel("Discharge")        
        reference_label = QtWidgets.QLabel(self.view_model.gui_text("reference"))
        reference_label.setContentsMargins(5, 0, 0, 0)
        measure_label = QtWidgets.QLabel(self.view_model.gui_text("measure"))
        measure_label.setContentsMargins(5, 0, 0, 0)
        

        # Add widgets to the form layout with labels
        self.grid_layout.addWidget(discharge_label, 1, 0)
        self.grid_layout.addWidget(reference_label, 1, 1)
        self.grid_layout.addWidget(measure_label, 1, 2)

        group_box_layout.addLayout(self.grid_layout)

        # Add group box to the main layout
        layout.addRow(group_box)        

        # get the output directory
        self.output_dir = QtWidgets.QLineEdit(win)
        self.output_dir.editingFinished.connect(self.output_dir_text_changed)
        layout.addRow(self.view_model.gui_text("outputDir"), self.openFileLayout(win, self.output_dir, "output_dir", True))

        # plotting
        make_plots = QtWidgets.QLabel(self.view_model.gui_text("makePlots"), win)
        self.make_plots_edit = QtWidgets.QCheckBox(win)
        self.make_plots_edit.setToolTip(self.view_model.gui_text("makePlots_tooltip"))
        self.make_plots_edit.stateChanged.connect(self.update_plotting)
        layout.addRow(make_plots, self.make_plots_edit)

        self.save_plots = QtWidgets.QLabel(self.view_model.gui_text("savePlots"), win)
        self.save_plots.setEnabled(False)
        self.save_plots_edit = QtWidgets.QCheckBox(win)
        self.save_plots_edit.setToolTip(self.view_model.gui_text("savePlots_tooltip"))
        self.save_plots_edit.stateChanged.connect(self.update_plotting)
        self.save_plots_edit.setEnabled(False)
        layout.addRow(self.save_plots, self.save_plots_edit)

        self.figure_dir = QtWidgets.QLabel(self.view_model.gui_text("figureDir"), win)
        self.figure_dir.setEnabled(False)
        self.figure_dir_edit = QtWidgets.QLineEdit(win)
        self.figure_dir_edit.setEnabled(False)
        self.figure_dir_edit.editingFinished.connect(self.figure_dir_text_changed)
        layout.addRow(self.figure_dir, self.openFileLayout(win, self.figure_dir_edit, "figure_dir_edit", True))
        
        self.close_plots = QtWidgets.QLabel(self.view_model.gui_text("closePlots"), win)
        self.close_plots.setEnabled(False)
        self.close_plots_edit = QtWidgets.QCheckBox(win)
        self.close_plots_edit.setToolTip(self.view_model.gui_text("closePlots_tooltip"))
        self.close_plots_edit.setEnabled(False)
        self.close_plots_edit.stateChanged.connect(self.update_plotting)
        layout.addRow(self.close_plots, self.close_plots_edit)

    def update_qthreshold(self):
        if self.qthr.hasAcceptableInput():
            self.view_model.qthreshold = float(self.qthr.text())
            self.update_qvalues_tabs()
        else: 
            self.showMessage("Please input valid values for qthreshold")

    
    def update_ucritical(self):
        if self.ucrit.hasAcceptableInput():
            self.view_model.ucritical = float(self.ucrit.text())
            self.update_qvalues_tabs()
        else: 
            self.showMessage("Please input valid values for ucritical")
    
    
    def output_dir_text_changed(self):
        text = self.output_dir.text()
        if text != self.view_model.output_dir:
            self.view_model.output_dir = text
     
    
    def figure_dir_text_changed(self):
        text = self.figure_dir_edit.text()
        if text != self.view_model.figure_dir:
            self.view_model.figure_dir = text

    def add_condition_line(self, prefix: str, discharge : float, discharge_name:str) -> None:
        """
        Create the tab for one flow conditions.

        Arguments
        ---------
        prefix : str
            Prefix for all dialog dictionary entries of this tab.
        q : float
            Discharge [m3/s]
        """
        enabled = self.view_model.qthreshold < discharge

        # get the reference file
        q1file1 = QtWidgets.QLineEdit(self._win)
        q1file1.setEnabled(enabled)
        q1file1.setObjectName(prefix+"file1")

        # get the file with measure
        q1file2 = QtWidgets.QLineEdit(self._win)
        q1file2.setEnabled(enabled)
        q1file2.setObjectName(prefix+"file2")
        
        discharge_value_label = QtWidgets.QLabel(discharge_name)
        discharge_value_label.setEnabled(enabled)
        row_count = self.grid_layout.rowCount()
        self.grid_layout.addWidget(discharge_value_label, row_count, 0)
        self.grid_layout.addWidget(self.openFileLayout(self._win, q1file1, prefix+"file1", enabled), row_count, 1)
        self.grid_layout.addWidget(self.openFileLayout(self._win, q1file2, prefix+"file2", enabled), row_count, 2)
        
    def create_button_bar(self) -> None:
        # Logic to create button bar
        button_bar = QtWidgets.QWidget(self._win)
        button_bar_layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, button_bar)
        button_bar_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(button_bar)

        run = QtWidgets.QPushButton(self.view_model.gui_text("action_run"), self._win)
        run.clicked.connect(self.run_analysis)
        button_bar_layout.addWidget(run)

        done = QtWidgets.QPushButton(self.view_model.gui_text("action_close"), self._win)
        done.clicked.connect(self.close_dialog)
        button_bar_layout.addWidget(done)
    
    def run_analysis(self) -> None:
        if self.view_model.check_configuration():
            success = self.view_model.run_analysis()
            
            if success:
                self.showMessage(self.view_model.gui_text("end_of_analysis", dict={"report": self.view_model.report},))                
            else:
                self.showError(self.view_model.gui_text("error_during_analysis", dict={"report": self.view_model.report},))
        else:
            self.showError(self.view_model.gui_text("analysis_config_incomplete",))

    def close_dialog(self) -> None:
        """
        Close the dialog and program.

        Arguments
        ---------
        None
        """
        self._win.close()
    
    def activate_dialog(self) -> None:
        """
        Activate the user interface and run the program.

        Arguments
        ---------
        None
        """
        self._win.show()
        sys.exit(self._app.exec_())


    
    def menu_load_configuration(self) -> None:
        """
        Ask for a configuration file name and update GUI based on its content.

        Arguments
        ---------
        None
        """
        fil = QtWidgets.QFileDialog.getOpenFileName(
            caption=self.view_model.gui_text("select_cfg_file"), filter="Config Files (*.cfg)"
        )
        filename = fil[0]
        if filename != "":
            if not self.view_model.load_configuration(filename):
                self.showError(self.view_model.gui_text("file_not_found", prefix="", dict={"name": filename}))

    def menu_save_configuration(self) -> None:
        """
        Ask for a configuration file name and save GUI selection to that file.

        Arguments
        ---------
        None
        """
        fil = QtWidgets.QFileDialog.getSaveFileName(
            caption=self.view_model.gui_text("save_cfg_as"), filter="Config Files (*.cfg)"
        )
        filename = fil[0]
        if filename != "":
            self.view_model.save_configuration(filename)


    def menu_about_self(self) -> None:
        """
        Show the about dialog for D-FAST Morphological Impact.

        Arguments
        ---------
        None
        """
        msg = QtWidgets.QMessageBox()
        msg.setText("D-FAST Morphological Impact " + dfastmi.__version__)
        msg.setInformativeText("Copyright (c) 2024 Deltares.")
        msg.setDetailedText(self.view_model.gui_text("license"))
        msg.setWindowTitle(self.view_model.gui_text("about"))
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        
        logo_size = msg.heightMM() * 0.9
        pixmap = PyQt5.QtGui.QPixmap(str(DFAST_LOGO))
        msg.setIconPixmap(pixmap.scaled(logo_size, logo_size))
        msg.setWindowIcon(DialogView._get_dfast_icon())
        
        msg.exec_()


    def menu_about_qt(self) -> None:
        """
        Show the about dialog for Qt.

        Arguments
        ---------
        None
        """
        QtWidgets.QApplication.aboutQt()


    def menu_open_manual(self):
        """
        Open the user manual.

        Arguments
        ---------
        None
        """        
        subprocess.Popen(self.view_model.manual_filename, shell=True)
    
    def openFileLayout(self, win, myWidget, key: str, enabled: bool):
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

        progloc = str(Path(__file__).parent.parent.absolute())
        openFile = QtWidgets.QPushButton(
            PyQt5.QtGui.QIcon(progloc + os.path.sep + "open.png"), "", win
        )
        openFile.clicked.connect(partial(self.selectFile, key))
        openFile.setEnabled(enabled)
        gridly.addWidget(openFile, 0, 2)

        return parent


    def selectFile(self, key: str) -> None:
        """
        Select a D-Flow FM Map file and show in the GUI.

        Arguments
        ---------
        key : str
            Name of the field for which to select the file.
        """
        fil = QtWidgets.QFileDialog.getOpenFileName(
            caption=self.view_model.gui_text("select_map_file"), filter="D-Flow FM Map Files (*map.nc)"
        )
        if fil[0] != "":
            if key == "figure_dir_edit":
                self.figure_dir_edit.setText(fil[0])
                self.view_model.figure_dir = fil[0]
            elif key == "output_dir":
                self.output_dir.setText(fil[0])
                self.view_model.output_dir = fil[0]
            else:
                self.set_folder_in_tabs(key, fil[0])
    
    def set_folder_in_tabs(self, key: str, file:str):
        input_textbox = self.general_widget.findChild(QtWidgets.QLineEdit, key)
        if input_textbox:
            input_textbox.setText(file)

    def showMessage(self, message: str) -> None:
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


    def showError(self, message: str) -> None:
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

    def update_plotting(self) -> None:
        """
        Update the plotting flags.
        
        Arguments
        ---------
        None
        """
        self.view_model.plotting = self.make_plots_edit.isChecked()

        self.save_plots.setEnabled(self.view_model.plotting)
        self.save_plots_edit.setEnabled(self.view_model.plotting)

        self.view_model.save_plots = self.save_plots_edit.isChecked() and self.view_model.plotting

        self.figure_dir.setEnabled(self.view_model.save_plots)
        self.figure_dir_edit.setEnabled(self.view_model.save_plots)

        self.view_model.close_plots = self.close_plots_edit.isChecked()
        self.close_plots.setEnabled(self.view_model.plotting)
        self.close_plots_edit.setEnabled(self.view_model.plotting)

    @staticmethod
    def _get_dfast_icon() -> QIcon:
     return QIcon(str(DFAST_LOGO))

# Entry point
def main(rivers_configuration: RiversObject, config_file: Optional[str] = None) -> None:
    # Create Model instance
    model = DialogModel(rivers_configuration, config_file)

    # Create ViewModel instance with the Model
    view_model = DialogViewModel(model)

    # Create View instance with the ViewModel
    view = DialogView(view_model)
    
    # Initialize the user interface and run the program
    view.activate_dialog()

