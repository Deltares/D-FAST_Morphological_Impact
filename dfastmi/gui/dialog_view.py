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
from pathlib import Path
import subprocess
from functools import partial
import sys
from typing import Optional

import PyQt5.QtCore
import PyQt5.QtGui
from dfastmi.gui.dialog_utils import FileExistValidator, FolderExistsValidator, ValidatingLineEdit, get_available_font, gui_text
from dfastmi.gui.dialog_view_model import DialogViewModel
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.RiversObject import RiversObject
from dfastmi.resources import DFAST_LOGO
import dfastmi.kernel.core
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QBoxLayout, 
    QMenuBar, 
    QComboBox,
    QLabel,
    QWidget, 
    QGridLayout, 
    QCheckBox,
    QVBoxLayout, 
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QFileDialog,
    QMessageBox
)
# View

class DialogView():
    _app : QApplication = None
    _win : QMainWindow = None
    _layout : QBoxLayout = None
    _menubar : QMenuBar = None
    _branch : QComboBox = None
    _reach : QComboBox = None
    _qloc : QLabel = None
    _qthr : QLineEdit = None
    _ucrit : QLineEdit = None
    _slength : QLabel = None

    _general_widget : QWidget = None
    _grid_layout : QGridLayout = None
    _output_dir : QLineEdit = None
    _make_plots_edit : QCheckBox = None
    _save_plots : QLabel = None
    _save_plots_edit : QCheckBox = None
    _figure_dir : QLabel = None
    _figure_dir_edit : QLineEdit = None

    _close_plots : QLabel = None
    _close_plots_edit : QCheckBox = None

    def __init__(self, view_model: DialogViewModel):
        self._view_model = view_model

        # Initialize GUI components
        self._create_qt_application()
        self._create_dialog()
        self._create_menus()
        self._create_central_widget()
        self._create_general_widgets()
        self._create_button_bar()
        # Connect the view model's data_changed signal to update_ui slot
        self._view_model.branch_changed.connect(self._update_branch)
        self._view_model.reach_changed.connect(self._update_reach)
        self._update_qvalues_table()

    def _update_branch(self, data):
        self._branch.setCurrentText(data)
        self._reach.clear()
        for r in self._view_model.current_branch.reaches:
            self._reach.addItem(r.name)
        self._qloc.setText(self._view_model.current_branch.qlocation)
        self._qthr.setText(str(self._view_model.model.qthreshold))
        self._ucrit.setText(str(self._view_model.model.ucritical))
        self._slength.setText(self._view_model.slength)
        self._reach.setCurrentText(self._view_model.current_reach.name)
        self._update_qvalues_table()
        self._output_dir.setText(self._view_model.model.output_dir)
        self._make_plots_edit.setChecked(self._view_model.model.plotting)
        self._save_plots_edit.setChecked(self._view_model.model.save_plots)
        self._close_plots_edit.setChecked(self._view_model.model.close_plots)
        self._update_condition_files()
    
    def _update_reach(self, data):
        self._reach.setCurrentText(data)
        self._slength.setText(self._view_model.slength)
    
    def _update_condition_files(self):
        for condition_discharge, reference_file in self._view_model.reference_files.items():
            self._update_condition_file_field("reference", condition_discharge, reference_file)

        for condition_discharge, measure_file in self._view_model.measure_files.items():
            self._update_condition_file_field("with_measure", condition_discharge, measure_file)            

    def _update_condition_file_field(self, field_postfix: str, condition_discharge, reference_file):
        prefix = str(condition_discharge)+"_"
        key = prefix + field_postfix
        input_textbox = self._general_widget.findChild(ValidatingLineEdit, key)
        if input_textbox:
            input_textbox.setText(reference_file)
            state = input_textbox.validator.validate(input_textbox.text(), 0)[0]
            input_textbox.setInvalid(state != PyQt5.QtGui.QValidator.Acceptable)
    
    def _update_qvalues_table(self):
        self._clear_conditions()
        for discharge in self._view_model.current_reach.hydro_q:
            prefix = str(discharge) + "_"
            qval = str(discharge) + " m3/s"
            self._add_condition_line(prefix, discharge, qval)

    def _clear_conditions(self):
        if self._grid_layout:
            for row in range(self._grid_layout.rowCount()):
                if row > 1:        
                    for col in range(self._grid_layout.columnCount()):
                        # Remove widgets from the specified row
                        item = self._grid_layout.itemAtPosition(row, col)
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
            
    def _create_qt_application(self) -> None:
        """
        Construct the QT application where the dialog will run in.

        Arguments
        ---------
        None
        """
        
        self._app = QApplication(sys.argv)
        self._app.setStyle("fusion")
        
        # Set the application-wide font
        preferred_font = "Lucida Console" #"Consolas"
        fallback_font = "Courier New"
        font = get_available_font(self._app.font(), preferred_font, fallback_font)
        self._app.setFont(font)

    def _create_dialog(self) -> None:
        """
        Construct the D-FAST Morphological Impact user interface.

        Arguments
        ---------
        None
        """
        self._win = QMainWindow()
        self._win.setGeometry(200, 200, 600, 300)
        self._win.setWindowTitle("D-FAST Morphological Impact")
        self._win.setWindowIcon(DialogView._get_dfast_icon())
    
    def _create_menus(self) -> None:
        # Logic to create menus
        """
        Add the menus to the menubar.

        Arguments
        ---------
        menubar : PyQt5.QMenuBar
            Menubar to which menus should be added.
        """
        menubar = self._win.menuBar()
        
        menu = menubar.addMenu(gui_text("File"))
        item = menu.addAction(gui_text("Load"))
        item.triggered.connect(self._menu_load_configuration)
        item = menu.addAction(gui_text("Save"))
        item.triggered.connect(self._menu_save_configuration)
        menu.addSeparator()
        item = menu.addAction(gui_text("Close"))
        item.triggered.connect(self._close_dialog)

        menu = menubar.addMenu(gui_text("Help"))
        item = menu.addAction(gui_text("Manual"))
        item.triggered.connect(self._menu_open_manual)
        menu.addSeparator()
        item = menu.addAction(gui_text("Version"))
        item.triggered.connect(self._menu_about_self)
        item = menu.addAction(gui_text("AboutQt"))
        item.triggered.connect(self._menu_about_qt)

    def _create_central_widget(self) -> None:
        # Logic to create and set the central widget
        central_widget = QWidget()
        self._layout = QBoxLayout(2, central_widget)
        self._win.setCentralWidget(central_widget)        
    
    def _create_general_widgets(self) -> None:
        """
        Create the general settings with widgets.

        Arguments
        ---------
        None
        """
        self._general_widget = QWidget(self._win)
        layout = QFormLayout(self._general_widget)
        
        self._create_branch_input(layout)        
        self._create_reach_input(layout)

        # show the discharge location
        self._show_discharge_location(layout)

        double_validator = PyQt5.QtGui.QDoubleValidator()
        double_validator.setLocale(PyQt5.QtCore.QLocale(PyQt5.QtCore.QLocale.C))
        
        # get minimum flow-carrying discharge
        self._create_qthreshhold_input(layout, double_validator)

        # get critical flow velocity
        self._create_ucritical_input(layout, double_validator)

        # show the impact length
        self._show_impacted_length(layout)

        # Create conditions group
        self._create_conditions_group_input(layout)

        # get the output directory
        self._creat_output_directory_input(layout)

        # plotting
        self._create_make_plots_input_checkbox(layout)
        self._create_save_plots_input_checkbox(layout)
        self._create_output_figure_plots_directory_input(layout)        
        self._create_close_plots_input_checkbox(layout)
        
        self._layout.addWidget(self._general_widget)

    def _create_close_plots_input_checkbox(self, layout):
        self._close_plots = QLabel(gui_text("closePlots"), self._win)
        self._close_plots.setEnabled(False)
        self._close_plots_edit = QCheckBox(self._win)
        self._close_plots_edit.setToolTip(gui_text("closePlots_tooltip"))
        self._close_plots_edit.setEnabled(False)
        self._close_plots_edit.stateChanged.connect(self._update_plotting)
        layout.addRow(self._close_plots, self._close_plots_edit)

    def _create_output_figure_plots_directory_input(self, layout):
        self._figure_dir = QLabel(gui_text("figureDir"), self._win)
        self._figure_dir.setEnabled(False)
        self._figure_dir_edit = ValidatingLineEdit(FolderExistsValidator(),self._win)
        self._figure_dir_edit.setEnabled(False)
        self._figure_dir_edit.textChanged.connect(partial(self._update_file_or_folder_validation, self._figure_dir_edit))
        self._figure_dir_edit.editingFinished.connect(partial(self._update_view_model, view_model_variable="figure_dir", value=lambda : self._figure_dir_edit.text(), invalid=lambda: self._figure_dir_edit.invalid))
        layout.addRow(self._figure_dir, self._open_folder_layout(self._win, self._figure_dir_edit, "figure_dir_edit", False))

    def _create_save_plots_input_checkbox(self, layout):
        self._save_plots = QLabel(gui_text("savePlots"), self._win)
        self._save_plots.setEnabled(False)
        self._save_plots_edit = QCheckBox(self._win)
        self._save_plots_edit.setToolTip(gui_text("savePlots_tooltip"))
        self._save_plots_edit.stateChanged.connect(self._update_plotting)
        self._save_plots_edit.setEnabled(False)
        layout.addRow(self._save_plots, self._save_plots_edit)

    def _create_make_plots_input_checkbox(self, layout):
        make_plots = QLabel(gui_text("makePlots"), self._win)
        self._make_plots_edit = QCheckBox(self._win)
        self._make_plots_edit.setToolTip(gui_text("makePlots_tooltip"))
        self._make_plots_edit.stateChanged.connect(self._update_plotting)
        layout.addRow(make_plots, self._make_plots_edit)

    def _creat_output_directory_input(self, layout):
        self._output_dir = ValidatingLineEdit(FolderExistsValidator(), self._win)
        self._output_dir.setPlaceholderText("Enter file path")
        self._output_dir.textChanged.connect(partial(self._update_file_or_folder_validation, line_edit=self._output_dir))
        self._output_dir.editingFinished.connect(partial(self._update_view_model, view_model_variable="output_dir", value=lambda : self._output_dir.text(), invalid=lambda: self._output_dir.invalid))
        layout.addRow(gui_text("outputDir"), self._open_folder_layout(self._win, self._output_dir, "output_dir", True))
    
    def _update_view_model(self, view_model_variable, value, invalid):
        if not invalid():
            setattr(self._view_model, view_model_variable, value())
    
    def _update_file_or_folder_validation(self,line_edit):
        state=line_edit.validator.validate(line_edit.text(), 0)[0]
        line_edit.setInvalid(state != PyQt5.QtGui.QValidator.Acceptable)

    def _create_conditions_group_input(self, layout):
        group_box = QGroupBox(gui_text("condition_group_name"))
        group_box_layout = QVBoxLayout(group_box)
        group_box.setStyleSheet("""
            QGroupBox {
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Position the title at the top-center */
                padding: 0 3px; /* Add some padding */
            }
        """)
        # Add widgets to the group box
        
        # Create a grid layout
        self._grid_layout = QGridLayout()
        self._grid_layout.setObjectName("discharge_conditions_grid")
        
        self._grid_layout.addWidget(QLabel(gui_text("qloc")), 0, 0)
        # Create a new instance of the widget
        copied_qloc = QLabel()

        # Set properties of the copied widget to match the original widget
        copied_qloc.setText(self._qloc.text())
        self._grid_layout.addWidget(copied_qloc, 0, 1)
        
        
        # Add widgets to the form layout
        discharge_label = QLabel(gui_text("qval"))
        reference_label = QLabel(gui_text("reference"))
        measure_label = QLabel(gui_text("measure"))
        
        # Add widgets to the form layout with labels
        self._grid_layout.addWidget(discharge_label, 1, 0)
        self._grid_layout.addWidget(reference_label, 1, 1)
        self._grid_layout.addWidget(measure_label, 1, 2)

        group_box_layout.addLayout(self._grid_layout)

        # Add group box to the main layout
        layout.addRow(group_box)

    def _show_impacted_length(self, layout):
        self._slength = QLabel(self._win)
        self._slength.setToolTip(gui_text("length_tooltip"))
        self._slength.setText(self._view_model.slength)
        layout.addRow(gui_text("length"), self._slength)

    def _create_ucritical_input(self, layout, double_validator):
        self._ucrit = QLineEdit(self._win)
        self._ucrit.setValidator(double_validator)
        self._ucrit.setToolTip(gui_text("ucrit_tooltip"))
        self._ucrit.editingFinished.connect(self._update_ucritical)
        self._ucrit.setText(str(self._view_model.model.ucritical))
        layout.addRow(gui_text("ucrit"), self._ucrit)

    def _create_qthreshhold_input(self, layout, double_validator : PyQt5.QtGui.QDoubleValidator):
        self._qthr = QLineEdit(self._win)
        self._qthr.setValidator(double_validator)
        self._qthr.editingFinished.connect(self._update_qthreshold)        
        self._qthr.setToolTip(gui_text("qthr_tooltip"))
        qthrtxt = QLabel(gui_text("qthr"), self._win)
        self._qthr.setText(str(self._view_model.model.qthreshold))
        layout.addRow(qthrtxt, self._qthr)        

    def _show_discharge_location(self, layout):
        self._qloc = QLabel("", self._win)
        self._qloc.setToolTip(gui_text("qloc"))
        self._qloc.setText(self._view_model.current_branch.qlocation)
        layout.addRow(gui_text("qloc"), self._qloc)

    def _create_reach_input(self, layout):
        # get the reach
        self._reach = QComboBox(self._win)
        self._reach.currentTextChanged.connect(self._view_model.updated_reach)
        self._reach.setToolTip(gui_text("reach_tooltip"))
        for r in self._view_model.current_branch.reaches:
            self._reach.addItem(r.name)
        self._reach.setCurrentText(self._view_model.current_reach.name)
        layout.addRow(gui_text("reach"), self._reach)
    
    def _create_branch_input(self, layout:QFormLayout):
        # get the branch
        self._branch = QComboBox(self._win)
        self._branch.currentTextChanged.connect(self._view_model.updated_branch)
        self._branch.setToolTip(gui_text("branch_tooltip"))
        for b in self._view_model.model.rivers.branches:
            self._branch.addItem(b.name)
        self._branch.setCurrentText(self._view_model.current_branch.name)
        layout.addRow(gui_text("branch"), self._branch)

    def _update_qthreshold(self):
        if self._qthr.hasAcceptableInput():
            self._view_model.model.qthreshold = float(self._qthr.text())
            self._update_qvalues_table()
            self._update_condition_files()
        else: 
            self._show_message("Please input valid values for qthreshold")

    def _update_ucritical(self):
        if self._ucrit.hasAcceptableInput():
            self._view_model.model.ucritical = float(self._ucrit.text())
            self._update_qvalues_table()
            self._update_condition_files()
        else: 
            self._show_message("Please input valid values for ucritical")    
    
    def _add_condition_line(self, prefix: str, discharge : float, discharge_name:str) -> None:
        """
        Create the table line for one flow conditions.

        Arguments
        ---------
        prefix : str
            Prefix for all dialog dictionary entries of this table line.
        discharge : float
            Discharge [m3/s]
        discharge_name : str
            Discharge value with unit [m3/s]
        """
        enabled = self._view_model.model.qthreshold < discharge

        # get the reference file
        q1_reference = ValidatingLineEdit(FileExistValidator(),self._win)
        q1_reference.setPlaceholderText("Enter reference file path")
        q1_reference.setEnabled(enabled)
        q1_reference.textChanged.connect(partial(self._update_file_or_folder_validation, q1_reference))
        q1_reference.setObjectName(prefix+"reference")

        # get the file with measure
        q1_with_measure = ValidatingLineEdit(FileExistValidator(),self._win)
        q1_with_measure.setPlaceholderText("Enter with measure file path")
        q1_with_measure.setEnabled(enabled)
        q1_with_measure.textChanged.connect(partial(self._update_file_or_folder_validation, q1_with_measure))
        q1_with_measure.setObjectName(prefix+"with_measure")
        
        discharge_value_label = QLabel(discharge_name)
        discharge_value_label.setEnabled(enabled)
        row_count = self._grid_layout.rowCount()
        self._grid_layout.addWidget(discharge_value_label, row_count, 0)
        self._grid_layout.addWidget(self._open_file_layout(self._win, q1_reference, prefix+"reference", enabled), row_count, 1)
        self._grid_layout.addWidget(self._open_file_layout(self._win, q1_with_measure, prefix+"with_measure", enabled), row_count, 2)
        
    def _create_button_bar(self) -> None:
        # Logic to create button bar
        button_bar = QWidget(self._win)
        button_bar_layout = QBoxLayout(QBoxLayout.LeftToRight, button_bar)
        button_bar_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(button_bar)

        run = QPushButton(gui_text("action_run"), self._win)
        run.clicked.connect(self._run_analysis)
        button_bar_layout.addWidget(run)

        done = QPushButton(gui_text("action_close"), self._win)
        done.clicked.connect(self._close_dialog)
        button_bar_layout.addWidget(done)
    
    def _run_analysis(self) -> None:
        if self._view_model.check_configuration():
            success = self._view_model.run_analysis()
            
            if success:
                self._show_message(gui_text("end_of_analysis", placeholder_dictionary={"report": self._view_model.report},))                
            else:
                self._show_error(gui_text("error_during_analysis", placeholder_dictionary={"report": self._view_model.report},))
        else:
            self._show_error(gui_text("analysis_config_incomplete",))

    def _close_dialog(self) -> None:
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
    
    def _menu_load_configuration(self) -> None:
        """
        Ask for a configuration file name and update GUI based on its content.

        Arguments
        ---------
        None
        """
        fil = QFileDialog.getOpenFileName(
            caption=gui_text("select_cfg_file"), filter="Config Files (*.cfg)"
        )
        filename = fil[0]
        if filename != "" and not self._view_model.load_configuration(filename):
            self._show_error(gui_text("file_not_found", prefix="", placeholder_dictionary={"name": filename}))

    def _menu_save_configuration(self) -> None:
        """
        Ask for a configuration file name and save GUI selection to that file.

        Arguments
        ---------
        None
        """
        fil = QFileDialog.getSaveFileName(
            caption=gui_text("save_cfg_as"), filter="Config Files (*.cfg)"
        )
        filename = fil[0]
        if filename != "":
            self._view_model.save_configuration(filename)

    def _menu_about_self(self) -> None:
        """
        Show the about dialog for D-FAST Morphological Impact.

        Arguments
        ---------
        None
        """
        msg = QMessageBox()
        msg.setText("D-FAST Morphological Impact " + dfastmi.__version__)
        msg.setInformativeText("Copyright (c) 2024 Deltares.")
        msg.setDetailedText(gui_text("license"))
        msg.setWindowTitle(gui_text("about"))
        msg.setStandardButtons(QMessageBox.Ok)
        
        logo_size = msg.heightMM() * 0.9
        pixmap = PyQt5.QtGui.QPixmap(str(DFAST_LOGO))
        msg.setIconPixmap(pixmap.scaled(logo_size, logo_size))
        msg.setWindowIcon(DialogView._get_dfast_icon())
        msg.exec_()

    def _menu_about_qt(self) -> None:
        """
        Show the about dialog for Qt.

        Arguments
        ---------
        None
        """
        QApplication.aboutQt()

    def _menu_open_manual(self):
        """
        Open the user manual.

        Arguments
        ---------
        None
        """        
        subprocess.Popen(self._view_model.manual_filename, shell=True)
    
    def _open_file_layout(self, win, my_widget, key: str, enabled: bool):
        """
        Add an open line to the dialog.

        Arguments
        ---------
        win
            Main window of the dialog.
        my_widget
            Line edit widget to display the file name.
        key : str
            Base name of the Widgets on this file.
        enabled : bool
            If the widgets should be enabled.
        """
        parent = QWidget()
        gridly = QGridLayout(parent)
        gridly.setContentsMargins(0, 0, 0, 0)
        gridly.addWidget(my_widget, 0, 0)

        progloc = str(Path(__file__).parent.parent.absolute())
        open_file = QPushButton(
            PyQt5.QtGui.QIcon(str(Path(progloc).joinpath("open.png"))), "", win
        )
        open_file.clicked.connect(partial(self._select_file, key))
        open_file.setObjectName(key+"_button")
        open_file.setEnabled(enabled)
        gridly.addWidget(open_file, 0, 2)

        return parent

    def _select_file(self, key: str) -> None:
        """
        Select a D-Flow FM Map file and show in the GUI.

        Arguments
        ---------
        key : str
            Name of the field for which to select the file.
        """
        fil = QFileDialog.getOpenFileName(
            caption=gui_text("select_map_file"), filter="D-Flow FM Map Files (*map.nc)"
        )
        if fil[0] != "":
            self._set_file_in_condition_table(key, fil[0])
    
    def _open_folder_layout(self, win, my_widget, key: str, enabled: bool):
        """
        Add an open line to the dialog.

        Arguments
        ---------
        win
            Main window of the dialog.
        my_widget
            Line edit widget to display the folder name.
        key : str
            Base name of the Widgets on this folder.
        enabled : bool
            If the widgets should be enabled.
        """
        parent = QWidget()
        gridly = QGridLayout(parent)
        gridly.setContentsMargins(0, 0, 0, 0)
        gridly.addWidget(my_widget, 0, 0)

        progloc = str(Path(__file__).parent.parent.absolute())
        open_folder = QPushButton(
            PyQt5.QtGui.QIcon(str(Path(progloc).joinpath("open.png"))), "", win
        )
        open_folder.clicked.connect(partial(self._select_folder, key))
        open_folder.setObjectName(key+"_button")
        open_folder.setEnabled(enabled)
        gridly.addWidget(open_folder, 0, 2)

        return parent

    def _select_folder(self, key: str) -> None:
        """
        Select a folder and show in the GUI.

        Arguments
        ---------
        key : str
            Name of the field for which to select the file.
        """
        folder = QFileDialog.getExistingDirectory(
            caption=gui_text("select_directory")
        )
        
        if key == "figure_dir_edit":
            self._figure_dir_edit.setText(folder)
            self._view_model.model.figure_dir = folder
        elif key == "output_dir":
            self._output_dir.setText(folder)
            self._view_model.model.output_dir = folder
        
    def _set_file_in_condition_table(self, key: str, file:str):
        input_textbox = self._general_widget.findChild(QLineEdit, key)
        if input_textbox and input_textbox.hasAcceptableInput():
            input_textbox.setText(file)
            
            if "_reference" in key:
                key_without_suffix = key.replace("_reference", "")
                self._view_model.reference_files[key_without_suffix] = file
            
            if "_with_measure" in key:
                key_without_suffix = key.replace("_with_measure", "")
                self._view_model.measure_files[key_without_suffix] = file
            


    def _show_message(self, message: str) -> None:
        """
        Display an information message box with specified string.

        Arguments
        ---------
        message : str
            Text to be displayed in the message box.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _show_error(self, message: str) -> None:
        """
        Display an error message box with specified string.

        Arguments
        ---------
        message : str
            Text to be displayed in the message box.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _update_plotting(self) -> None:
        """
        Update the plotting flags.
        
        Arguments
        ---------
        None
        """
        self._view_model.model.plotting = self._make_plots_edit.isChecked()

        self._save_plots.setEnabled(self._view_model.model.plotting)
        self._save_plots_edit.setEnabled(self._view_model.model.plotting)

        self._view_model.model.save_plots = self._save_plots_edit.isChecked() and self._view_model.model.plotting

        self._figure_dir.setEnabled(self._view_model.model.save_plots)
        self._figure_dir_edit.setEnabled(self._view_model.model.save_plots)
        figure_dir_button = self._general_widget.findChild(QPushButton, "figure_dir_edit_button")
        figure_dir_button.setEnabled(self._view_model.model.save_plots)

        self._view_model.model.close_plots = self._close_plots_edit.isChecked()
        self._close_plots.setEnabled(self._view_model.model.plotting)
        self._close_plots_edit.setEnabled(self._view_model.model.plotting)

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
