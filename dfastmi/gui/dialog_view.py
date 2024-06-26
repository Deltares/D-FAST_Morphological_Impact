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
import sys
import traceback
from functools import partial
from pathlib import Path
from typing import Iterator, Optional, Tuple

import PyQt5.QtCore
import PyQt5.QtGui
from PyQt5.QtGui import QDoubleValidator, QFontDatabase, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import dfastmi.kernel.core
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.gui.dialog_utils import (
    FileExistValidator,
    FolderExistsValidator,
    ValidatingLineEdit,
    get_available_font,
    gui_text,
)
from dfastmi.gui.dialog_view_model import DialogViewModel
from dfastmi.gui.qt_tools import clear_layout_item
from dfastmi.io.RiversObject import RiversObject
from dfastmi.kernel.typehints import FilenameDict
from dfastmi.resources import DFAST_LOGO

# View
reference_label = "reference"
with_measure_label = "with_measure"


class DialogView:
    """
    D-FAST Morphological Impact GUI View

    This class represents the graphical user interface (GUI) view for the D-FAST Morphological Impact (DFMI) software.
    It provides methods to create and manage the GUI components, handle user interactions, and update the GUI based on
    changes in the underlying data model.

    Attributes:
        _app (QApplication): The PyQt application instance.
        _win (QMainWindow): The main window of the GUI.
        _layout (QBoxLayout): The layout of the central widget.
        _case_description (QLineEdit): Contains the case description.
        _branch (QComboBox): The combo box for selecting the river branch.
        _reach (QComboBox): The combo box for selecting the river reach.
        _qloc (QLabel): The label for displaying the discharge location.
        _qthr (QLineEdit): The line edit for specifying the discharge threshold.
        _ucrit (QLineEdit): The line edit for specifying the critical velocity.
        _ucrit_label (QLabel): The label for displaying minimum for specifying the critical velocity.
        _slength (QLabel): The label for displaying the impacted length.
        _general_widget (QWidget): The widget containing general settings.
        _grid_layout (QGridLayout): The grid layout for displaying conditions.
        _output_dir (QLineEdit): The line edit for specifying the output directory.
        _make_plots_edit (QCheckBox): The check box for toggling plotting.
        _save_plots_edit (QCheckBox): The check box for toggling saving plots.
        _figure_dir_edit (QLineEdit): The line edit for specifying the output figure directory.
        _close_plots_edit (QCheckBox): The check box for toggling closing plots.
    """

    _app: QApplication = None
    _win: QMainWindow = None
    _layout: QBoxLayout = None
    _case_description: QLineEdit = None
    _branch: QComboBox = None
    _reach: QComboBox = None
    _qloc: QLabel = None
    _qthr: QLineEdit = None
    _ucrit: QLineEdit = None
    _ucrit_label: QLabel = None
    _slength: QLabel = None

    _general_widget: QWidget = None
    _grid_layout: QGridLayout = None
    _output_dir: QLineEdit = None
    _make_plots_edit: QCheckBox = None
    _save_plots: QLabel = None
    _save_plots_edit: QCheckBox = None
    _figure_dir: QLabel = None
    _figure_dir_edit: QLineEdit = None

    _close_plots: QLabel = None
    _close_plots_edit: QCheckBox = None

    def __init__(self, view_model: DialogViewModel):
        """
        Initialize the DialogView.

        Args:
            view_model (DialogViewModel): The view model for the dialog.
        """
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
        self._view_model.ucritical_changed.connect(self._update_ucritical)
        self._view_model.qthreshold_changed.connect(self._update_qthreshold)
        self._view_model.slength_changed.connect(self._update_sedimentation_length)
        self._view_model.make_plot_changed.connect(
            self._update_enabled_of_make_plot_dependent_view_items
        )
        self._view_model.save_plot_changed.connect(
            self._update_enabled_of_save_plot_dependent_view_items
        )
        self._view_model.figure_dir_changed.connect(self._update_figure_directory_input)
        self._view_model.output_dir_changed.connect(self._update_output_directory_input)

        self._view_model.reference_files_changed.connect(
            self._update_condition_file_field
        )
        self._view_model.measure_files_changed.connect(
            self._update_condition_file_field
        )

        self._view_model.analysis_exception.connect(self._show_error)
        self._update_qvalues_table()

    def _update_branch(self, data):
        """
        Update the GUI components when the branch changes.

        Args:
            data: The data for the branch.
        """
        # Update case name
        self._case_description.setText(self._view_model.model.case_description)

        # Update branch and reach selection
        self._branch.setCurrentText(data)
        self._reach.clear()
        for r in self._view_model.current_branch.reaches:
            self._reach.addItem(r.name)
        # Update labels and text fields
        self._qloc.setText(self._view_model.current_branch.qlocation)
        self._output_dir.setText(self._view_model.model.output_dir)
        self._make_plots_edit.setChecked(self._view_model.model.plotting)
        self._save_plots_edit.setChecked(self._view_model.model.save_plots)
        self._close_plots_edit.setChecked(self._view_model.model.close_plots)

    def _update_reach(self, data):
        """
        Update the GUI components when the reach changes.

        Args:
            data: The data for the reach.
        """
        # Update reach label
        self._reach.setCurrentText(data)

    def _update_sedimentation_length(self, slength: str):
        """
        Update the GUI components when the sedimentation length changes.

        Args:
            slength: The sedimentation length.
        """
        # Update the sedimentation length in the GUI
        self._slength.setText(slength)

    def _update_ucritical(self, ucrit: float, default: float):
        """
        Update the GUI components when the critical (minimum) velocity [m/s] for sediment transport changes.

        Args:
            ucrit: The critical (minimum) velocity [m/s] for sediment transport.
            default: The default critical (minimum) velocity [m/s] for sediment transport.
        """
        # Update the threshold discharge in the GUI
        self._ucrit.setText(str(ucrit))
        self._ucrit_label.setText(
            gui_text("ucrit", placeholder_dictionary={"default": str(default)})
        )

    def _update_qthreshold(self, data: float):
        """
        Update the GUI components when the discharge threshold changes.

        Args:
            data: The dischage threshold.
        """
        # Update the threshold discharge in the GUI
        self._qthr.setText(str(data))

        # Update labels and text fields
        self._update_qvalues_table()

    def _update_condition_file_field(
        self, field_postfix: str, condition_discharge: float, file_location: str
    ):
        """
        Update the condition file field.

        Args:
            field_postfix (str): The postfix for the field.
            condition_discharge: The condition discharge.
            file_location (str): The file location.
        """
        prefix = str(condition_discharge) + "_"
        key = prefix + field_postfix
        input_textbox = self._general_widget.findChild(ValidatingLineEdit, key)
        if input_textbox:
            input_textbox.setText(file_location)

    def _update_qvalues_table(self):
        """Update the Q values table."""
        self._clear_conditions()
        for discharge in self._view_model.current_reach.hydro_q:
            prefix = str(discharge) + "_"
            qval = str(discharge) + " m3/s"
            self._add_condition_line(prefix, discharge, qval)

    def _clear_conditions(self):
        """Remove the discharge condition rows from the table."""
        if self._grid_layout:
            for row_index, column_index in self._get_discharge_conditions_grid_cells():
                grid_cell = self._grid_layout.itemAtPosition(row_index, column_index)
                clear_layout_item(grid_cell)

    def _get_discharge_conditions_grid_cells(self) -> Iterator[Tuple[int, int]]:
        start_row_index = 2
        for row_index in range(start_row_index, self._grid_layout.rowCount()):
            for column_index in range(self._grid_layout.columnCount()):
                yield row_index, column_index

    def _create_qt_application(self) -> None:
        """
        Construct the QT application where the dialog will run in.

        Arguments
        ---------
        None
        """

        self._app = QApplication(sys.argv)
        self._app.setStyle("fusion")

    def _create_dialog(self) -> None:
        """
        Construct the D-FAST Morphological Impact user interface.

        Arguments
        ---------
        None
        """
        self._win = QMainWindow()
        self._win.setGeometry(200, 200, 800, 300)
        self._win.setWindowTitle("D-FAST Morphological Impact")
        self._win.setWindowIcon(DialogView._get_dfast_icon())

    def _create_menus(self) -> None:
        """
        Add the menus to the menubar.

        Arguments
        ---------
        None
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
        """
        Create and set the central widget for the main window.

        This method initializes a QWidget as the central widget, sets up a QBoxLayout for its layout, and then sets
        this central widget in the QMainWindow.

        Returns:
            None
        """
        central_widget = QWidget(self._win)
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

        self._create_case_input(layout)
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
        self._create_output_directory_input(layout)

        # plotting
        self._create_make_plots_input_checkbox(layout)
        self._create_save_plots_input_checkbox(layout)
        self._create_output_figure_plots_directory_input(layout)
        self._create_close_plots_input_checkbox(layout)

        self._layout.addWidget(self._general_widget)

    def _create_close_plots_input_checkbox(self, layout: QBoxLayout) -> None:
        """
        Create input checkbox for closing plots.

        Args:
            layout (QBoxLayout): Layout to add the checkbox.

        Returns:
            None
        """
        self._close_plots = QLabel(gui_text("closePlots"), self._win)
        self._close_plots.setEnabled(self._view_model.make_plot)
        self._close_plots_edit = QCheckBox(self._win)
        self._close_plots_edit.setToolTip(gui_text("closePlots_tooltip"))
        self._close_plots_edit.setEnabled(self._view_model.make_plot)
        self._close_plots_edit.setChecked(self._view_model.model.close_plots)
        self._close_plots_edit.stateChanged.connect(self._updated_close_plots)
        layout.addRow(self._close_plots, self._close_plots_edit)

    def _create_output_figure_plots_directory_input(self, layout: QBoxLayout) -> None:
        """
        Create input for output figure directory.

        Args:
            layout (QBoxLayout): Layout to add the directory input.

        Returns:
            None
        """
        self._figure_dir = QLabel(gui_text("figureDir"), self._win)
        self._figure_dir.setEnabled(self._view_model.save_plot)
        self._figure_dir_edit = ValidatingLineEdit(FolderExistsValidator(), self._win)
        self._figure_dir_edit.setPlaceholderText("Enter file path")
        self._figure_dir_edit.setEnabled(self._view_model.save_plot)
        self._figure_dir_edit.textChanged.connect(
            partial(self._updated_file_or_folder_validation, self._figure_dir_edit)
        )
        self._figure_dir_edit.setText(self._view_model.figure_dir)
        self._figure_dir_edit.editingFinished.connect(
            partial(
                self._update_view_model,
                view_model_variable="figure_dir",
                value=lambda: self._figure_dir_edit.text(),
                invalid=lambda: self._figure_dir_edit.invalid,
            )
        )
        layout.addRow(
            self._figure_dir,
            self._open_folder_layout(
                self._figure_dir_edit, "figure_dir_edit", self._view_model.save_plot
            ),
        )

    def _create_save_plots_input_checkbox(self, layout: QBoxLayout) -> None:
        """
        Create input checkbox for saving plots.

        Args:
            layout (QBoxLayout): Layout to add the checkbox.

        Returns:
            None
        """
        self._save_plots = QLabel(gui_text("savePlots"), self._win)
        self._save_plots.setEnabled(self._view_model.make_plot)
        self._save_plots_edit = QCheckBox(self._win)
        self._save_plots_edit.setToolTip(gui_text("savePlots_tooltip"))
        self._save_plots_edit.setChecked(self._view_model.save_plot)
        self._save_plots_edit.stateChanged.connect(self._updated_save_plotting)
        self._save_plots_edit.setEnabled(self._view_model.make_plot)
        layout.addRow(self._save_plots, self._save_plots_edit)

    def _create_make_plots_input_checkbox(self, layout: QBoxLayout) -> None:
        """
        Create input checkbox for making plots.

        Args:
            layout (QBoxLayout): Layout to add the checkbox.

        Returns:
            None
        """
        make_plots = QLabel(gui_text("makePlots"), self._win)
        self._make_plots_edit = QCheckBox(self._win)
        self._make_plots_edit.setToolTip(gui_text("makePlots_tooltip"))
        self._make_plots_edit.setChecked(self._view_model.model.plotting)
        self._make_plots_edit.stateChanged.connect(self._updated_plotting)
        layout.addRow(make_plots, self._make_plots_edit)

    def _create_output_directory_input(self, layout: QBoxLayout) -> None:
        """
        Create input for output directory.

        Args:
            layout (QBoxLayout): Layout to add the directory input.

        Returns:
            None
        """
        self._output_dir = ValidatingLineEdit(FolderExistsValidator(), self._win)
        self._output_dir.setPlaceholderText("Enter file path")
        self._output_dir.textChanged.connect(
            partial(self._updated_file_or_folder_validation, line_edit=self._output_dir)
        )
        self._output_dir.setText(self._view_model.output_dir)
        self._output_dir.editingFinished.connect(
            partial(
                self._update_view_model,
                view_model_variable="output_dir",
                value=lambda: self._output_dir.text(),
                invalid=lambda: self._output_dir.invalid,
            )
        )
        layout.addRow(
            gui_text("outputDir"),
            self._open_folder_layout(self._output_dir, "output_dir", True),
        )

    def _update_view_model(self, view_model_variable: str, value, invalid) -> None:
        """
        Update view model.

        Args:
            view_model_variable (str): Variable in view model to update.
            value: Value to set.
            invalid: Function returning whether the value is invalid.

        Returns:
            None
        """
        if not invalid() or len(value()) == 0:
            setattr(self._view_model, view_model_variable, value())

    def _updated_condition_file(self, line_edit) -> None:
        """
        Simulation file name has been updated in the GUI.
        Store it in the model, and check whether it's valid.

        Args:
            line_edit: Line edit to validate.

        Returns:
            None
        """
        self._updated_file_or_folder_validation(line_edit)
        self._set_file_in_condition_table(line_edit.objectName(), line_edit.text())

    def _updated_file_or_folder_validation(self, line_edit) -> None:
        """
        Update file or folder validation.

        Args:
            line_edit: Line edit to validate.

        Returns:
            None
        """
        state = line_edit.validator.validate(line_edit.text(), 0)[0]
        line_edit.setInvalid(state != PyQt5.QtGui.QValidator.Acceptable)

    def _create_conditions_group_input(self, layout: QBoxLayout) -> None:
        """
        Create input group for conditions.

        Args:
            layout (QBoxLayout): Layout to add the input group.

        Returns:
            None
        """
        group_box = QGroupBox(gui_text("condition_group_name"), self._win)
        group_box.setStyleSheet(
            """
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
        """
        )
        # Add widgets to the group box

        # Create a grid layout
        self._grid_layout = QGridLayout(group_box)
        self._grid_layout.setObjectName("discharge_conditions_grid")

        # Add widgets to the form layout
        discharge_column_label = QLabel(gui_text("qval"), self._win)
        reference_column__label = QLabel(gui_text("reference"), self._win)
        measure_column_label = QLabel(gui_text("measure"), self._win)

        # Add widgets to the form layout with labels
        self._grid_layout.addWidget(discharge_column_label, 1, 0)
        self._grid_layout.addWidget(reference_column__label, 1, 1)
        self._grid_layout.addWidget(measure_column_label, 1, 2)

        # Add group box to the main layout
        layout.addRow(group_box)

    def _show_impacted_length(self, layout: QBoxLayout) -> None:
        """
        Show the impacted length.

        Args:
            layout (QBoxLayout): Layout to add the impacted length label.

        Returns:
            None
        """
        self._slength = QLabel(self._win)
        self._slength.setToolTip(gui_text("length_tooltip"))
        self._slength.setText(self._view_model.slength)
        layout.addRow(gui_text("length"), self._slength)

    def _create_ucritical_input(
        self, layout: QBoxLayout, double_validator: QDoubleValidator
    ) -> None:
        """
        Create input field for critical velocity.

        Args:
            layout (QBoxLayout): Layout to add the critical velocity input field.
            double_validator (QDoubleValidator): Validator for double values.

        Returns:
            None
        """
        self._ucrit = QLineEdit(self._win)
        self._ucrit.setValidator(double_validator)
        self._ucrit.setToolTip(gui_text("ucrit_tooltip"))
        self._ucrit.editingFinished.connect(self._updated_ucritical)
        self._ucrit.setText(str(self._view_model.ucritical))
        self._ucrit_label = QLabel(
            gui_text(
                "ucrit",
                placeholder_dictionary={
                    "default": self._view_model.current_reach.ucritical
                },
            ),
            self._win,
        )
        layout.addRow(self._ucrit_label, self._ucrit)

    def _create_qthreshhold_input(
        self, layout: QBoxLayout, double_validator: QDoubleValidator
    ) -> None:
        """
        Create input field for discharge threshold.

        Args:
            layout (QBoxLayout): Layout to add the discharge threshold input field.
            double_validator (QDoubleValidator): Validator for double values.

        Returns:
            None
        """
        self._qthr = QLineEdit(self._win)
        self._qthr.setValidator(double_validator)
        self._qthr.editingFinished.connect(self._updated_qthreshold)
        self._qthr.setToolTip(gui_text("qthr_tooltip"))
        qthrtxt = QLabel(gui_text("qthr"), self._win)
        self._qthr.setText(str(self._view_model.model.qthreshold))
        layout.addRow(qthrtxt, self._qthr)

    def _show_discharge_location(self, layout: QBoxLayout) -> None:
        """
        Show the discharge location.

        Args:
            layout (QBoxLayout): Layout to add the discharge location label.

        Returns:
            None
        """
        self._qloc = QLabel("", self._win)
        self._qloc.setToolTip(gui_text("qloc"))
        self._qloc.setText(self._view_model.current_branch.qlocation)
        layout.addRow(gui_text("qloc"), self._qloc)

    def _create_reach_input(self, layout: QBoxLayout) -> None:
        """
        Create input field for river reach selection.

        Args:
            layout (QBoxLayout): Layout to add the river reach selection input field.

        Returns:
            None
        """
        self._reach = QComboBox(self._win)
        self._reach.currentTextChanged.connect(self._view_model.updated_reach)
        self._reach.setToolTip(gui_text("reach_tooltip"))
        for r in self._view_model.current_branch.reaches:
            self._reach.addItem(r.name)
        self._reach.setCurrentText(self._view_model.current_reach.name)
        # Set the reach font
        preferred_font = "Lucida Console"
        fallback_font = "Courier New"
        font = get_available_font(
            self._app.font(), preferred_font, fallback_font, QFontDatabase()
        )
        self._reach.setFont(font)

        layout.addRow(gui_text("reach"), self._reach)

    def _create_branch_input(self, layout: QFormLayout) -> None:
        """
        Create input field for river branch selection.

        Args:
            layout (QFormLayout): Layout to add the river branch selection input field.

        Returns:
            None
        """
        self._branch = QComboBox(self._win)
        self._branch.currentTextChanged.connect(self._view_model.updated_branch)
        self._branch.setToolTip(gui_text("branch_tooltip"))
        for b in self._view_model.model.rivers.branches:
            self._branch.addItem(b.name)
        self._branch.setCurrentText(self._view_model.current_branch.name)
        layout.addRow(gui_text("branch"), self._branch)

    def _create_case_input(self, layout: QBoxLayout) -> None:
        """
        Create input field for case description.

        Args:
            layout (QBoxLayout): Layout to add the case description input field.

        Returns:
            None
        """
        self._case_description = QLineEdit(self._win)
        self._case_description.setText(self._view_model.model.case_description)
        self._case_description.editingFinished.connect(self._updated_case_description)
        self._case_description.setToolTip(gui_text("case_description_tooltip"))
        case_description_label = QLabel(gui_text("case_description"), self._win)
        layout.addRow(case_description_label, self._case_description)

    def _updated_case_description(self) -> None:
        """Update case description."""
        self._view_model.model.case_description = self._case_description.text()

    def _updated_qthreshold(self) -> None:
        """
        Update discharge threshold.

        Returns:
            None
        """
        if self._qthr.hasAcceptableInput():
            self._view_model.qthreshold = float(self._qthr.text())

    def _updated_ucritical(self) -> None:
        """
        Update critical velocity.

        Returns:
            None
        """
        if self._ucrit.hasAcceptableInput():
            self._view_model.ucritical = float(self._ucrit.text())

    def _add_condition_line(
        self, prefix: str, discharge: float, discharge_name: str
    ) -> None:
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
        ---------
        Returns:
            None
        """
        enabled = self._view_model.model.qthreshold < discharge

        # get the reference file
        q1_reference = self._create_condition_validating_line_edit(
            prefix,
            discharge,
            enabled,
            self._view_model.reference_files,
            reference_label,
            "Enter reference file path",
        )

        # get the file with measure
        q1_with_measure = self._create_condition_validating_line_edit(
            prefix,
            discharge,
            enabled,
            self._view_model.measure_files,
            with_measure_label,
            "Enter with measure file path",
        )

        discharge_value_label = QLabel(discharge_name, self._win)
        discharge_value_label.setEnabled(enabled)
        row_count = self._grid_layout.rowCount()
        self._grid_layout.addWidget(discharge_value_label, row_count, 0)
        self._grid_layout.addWidget(
            self._open_file_layout(q1_reference, prefix + reference_label, enabled),
            row_count,
            1,
        )
        self._grid_layout.addWidget(
            self._open_file_layout(
                q1_with_measure, prefix + with_measure_label, enabled
            ),
            row_count,
            2,
        )

    def _create_condition_validating_line_edit(
        self,
        prefix: str,
        discharge: float,
        enabled: bool,
        files: FilenameDict,
        label_suffix: str,
        placeholder_text: str,
    ):
        line_edit = ValidatingLineEdit(FileExistValidator(), self._win)
        line_edit.setObjectName(prefix + label_suffix)

        line_edit.setPlaceholderText(placeholder_text)
        line_edit.setEnabled(enabled)
        line_edit.textChanged.connect(partial(self._updated_condition_file, line_edit))

        file_path = files.get(discharge, None)
        if file_path:
            line_edit.setText(file_path)

        return line_edit

    def _create_button_bar(self) -> None:
        """
        Create button bar with run and close buttons.

        Returns:
            None
        """
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
        """
        Run analysis when the 'Run' button is clicked.

        Returns:
            None
        """
        if self._view_model.check_configuration():
            try:
                success = self._view_model.run_analysis()
            except:
                self._show_error(
                    "A run-time exception occurred. Press 'Show Details...' for the full stack trace.",
                    traceback.format_exc(),
                )
                return

            if success:
                self._show_message(
                    gui_text(
                        "end_of_analysis",
                        placeholder_dictionary={"report": self._view_model.report},
                    )
                )
            else:
                self._show_error(
                    gui_text(
                        "error_during_analysis",
                        placeholder_dictionary={"report": self._view_model.report},
                    )
                )
        else:
            self._show_error(
                gui_text(
                    "analysis_config_incomplete",
                )
            )

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
            self._show_error(
                gui_text(
                    "file_not_found",
                    prefix="",
                    placeholder_dictionary={"name": filename},
                )
            )

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

        logo_size = int(msg.heightMM() * 0.9)
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
        os.startfile(self._view_model.manual_filename)

    def _open_file_layout(self, my_widget, key: str, enabled: bool):
        """
        Add an open line to the dialog.

        Arguments
        ---------
        my_widget
            Line edit widget to display the file name.
        key : str
            Base name of the Widgets on this file.
        enabled : bool
            If the widgets should be enabled.
        """
        parent = QWidget(self._win)
        gridly = QGridLayout(parent)
        gridly.setContentsMargins(0, 0, 0, 0)
        gridly.addWidget(my_widget, 0, 0)

        progloc = str(Path(__file__).parent.parent.absolute())
        open_file = QPushButton(
            PyQt5.QtGui.QIcon(str(Path(progloc).joinpath("open.png"))), "", self._win
        )
        open_file.clicked.connect(partial(self._select_file, key))
        open_file.setObjectName(key + "_button")
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

    def _open_folder_layout(self, my_widget, key: str, enabled: bool):
        """
        Add an open line to the dialog.

        Arguments
        ---------
        my_widget
            Line edit widget to display the folder name.
        key : str
            Base name of the Widgets on this folder.
        enabled : bool
            If the widgets should be enabled.
        """
        parent = QWidget(self._win)
        gridly = QGridLayout(parent)
        gridly.setContentsMargins(0, 0, 0, 0)
        gridly.addWidget(my_widget, 0, 0)

        progloc = str(Path(__file__).parent.parent.absolute())
        open_folder = QPushButton(
            PyQt5.QtGui.QIcon(str(Path(progloc).joinpath("open.png"))), "", self._win
        )
        open_folder.clicked.connect(partial(self._select_folder, key))
        open_folder.setObjectName(key + "_button")
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
        folder = QFileDialog.getExistingDirectory(caption=gui_text("select_directory"))

        if key == "figure_dir_edit":
            self._view_model.figure_dir = folder
        elif key == "output_dir":
            self._view_model.output_dir = folder

    def _set_file_in_condition_table(self, key: str, file: str) -> None:
        """
        Set file path in the condition table.

        Args:
            key (str): The key to identify the input text box in the condition table.
            file (str): The file path to be set.

        Returns:
            None
        """
        input_textbox: Optional[QLineEdit] = self._general_widget.findChild(
            QLineEdit, key
        )
        if input_textbox and input_textbox.hasAcceptableInput():
            input_textbox.setText(file)

            if "_" + reference_label in key:
                key_without_suffix = float(key.replace("_" + reference_label, ""))
                self._view_model.reference_files[key_without_suffix] = file

            if "_" + with_measure_label in key:
                key_without_suffix = float(key.replace("_" + with_measure_label, ""))
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

    def _show_error(self, message: str, detailed_message: Optional[str] = None) -> None:
        """
        Display an error message box with specified string.

        Arguments
        ---------
        message : str
            Text to be displayed in the message box.
        detailed_message : Option[str]
            Text to be displayed when the user clicks the Details button.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        if detailed_message:
            msg.setDetailedText(detailed_message)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _updated_plotting(self) -> None:
        """
        Update the plotting flags.

        Arguments
        ---------
        None
        """
        if self._view_model.make_plot != self._make_plots_edit.isChecked():
            self._view_model.make_plot = self._make_plots_edit.isChecked()

    def _update_enabled_of_make_plot_dependent_view_items(self, value: bool):
        self._save_plots.setEnabled(value)
        self._save_plots_edit.setEnabled(value)
        self._close_plots.setEnabled(value)
        self._close_plots_edit.setEnabled(value)

    def _update_enabled_of_save_plot_dependent_view_items(self, value: bool):
        self._figure_dir.setEnabled(value)
        self._figure_dir_edit.setEnabled(value)
        figure_dir_button = self._general_widget.findChild(
            QPushButton, "figure_dir_edit_button"
        )
        figure_dir_button.setEnabled(value)

    def _update_output_directory_input(self, value: str):
        self._output_dir.setText(value)

    def _update_figure_directory_input(self, value: str):
        self._figure_dir_edit.setText(value)

    def _updated_save_plotting(self) -> None:
        """Update the plotting flags."""

        save_plot_gui = self._save_plots_edit.isChecked() and self._view_model.make_plot

        if self._view_model.save_plot != save_plot_gui:
            self._view_model.save_plot = save_plot_gui

    def _updated_close_plots(self) -> None:
        """Update the close plot flag."""
        if self._view_model.model.close_plots != self._close_plots_edit.isChecked():
            self._view_model.model.close_plots = self._close_plots_edit.isChecked()

    @staticmethod
    def _get_dfast_icon() -> QIcon:
        """
        Get the D-FAST icon.

        Returns:
            QIcon: The D-FAST icon.
        """
        return QIcon(str(DFAST_LOGO))


# Entry point
def main(rivers_configuration: RiversObject, config_file: Optional[str] = None) -> None:
    """
    Entry point for the D-FAST Morphological Impact GUI.

    Args:
        rivers_configuration (RiversObject): The rivers configuration object.
        config_file (Optional[str], optional): The configuration file path. Defaults to None.
    """
    # Create Model instance
    model = DialogModel(rivers_configuration)

    # Create ViewModel instance with the Model
    view_model = DialogViewModel(model)
    view_model.load_configuration(config_file)

    # Create View instance with the ViewModel
    view = DialogView(view_model)

    # Initialize the user interface and run the program
    view.activate_dialog()
