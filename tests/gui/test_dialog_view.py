from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QFileDialog, QLineEdit, QMessageBox, QPushButton

import dfastmi
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.gui.dialog_utils import gui_text
from dfastmi.gui.dialog_view import DialogView
from dfastmi.gui.dialog_view_model import DialogViewModel
from dfastmi.io.RiversObject import RiversObject


@pytest.fixture(scope="module")
def dialog_view():
    # Initialize model, view model, and view
    rivers_configuration = RiversObject(
        "tests/c01 - GendtseWaardNevengeul/rivers_Q4000_v2.ini"
    )  # You need to provide proper initialization parameters here
    model = DialogModel(rivers_configuration)
    model.case_description = "myCase"
    view_model = DialogViewModel(model)
    view = DialogView(view_model)

    yield view

    # Clean up resources
    del view
    del view_model
    del model
    del rivers_configuration


def test_constructor(dialog_view: DialogView):
    """
    given : Rivers configuration object
    when  : creating the dialog view
    then  : the view components should be initialized with the correct initial state
    """
    view = dialog_view

    # Test if the constructor initializes view components with the correct initial state
    assert view._output_dir.text() == view._view_model.model.output_dir
    assert view._figure_dir_edit.text() == view._view_model.model.figure_dir
    assert view._make_plots_edit.isChecked() == view._view_model.model.plotting
    assert view._save_plots_edit.isChecked() == view._view_model.model.save_plots
    assert view._close_plots_edit.isChecked() == view._view_model.model.close_plots


class Test_dialog_inputs:
    def test_output_dir_update(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : updating the output directory
        then  : the output directory should be updated correctly
        """
        view = dialog_view

        # Test updating the output directory
        initial_value = view._output_dir.text()
        assert initial_value == ""

        # Test valid directory path
        valid_dir = Path.cwd().joinpath("output")
        if not valid_dir.exists():
            valid_dir.mkdir()
        valid_dir = str(valid_dir)
        view._output_dir.setText(valid_dir)
        view._output_dir.editingFinished.emit()

        assert view._output_dir.text() == valid_dir
        assert view._view_model.output_dir == valid_dir

        # Test invalid directory path
        invalid_dir = "invalid_path"
        view._output_dir.setText(invalid_dir)
        view._output_dir.editingFinished.emit()
        assert view._output_dir.text() == invalid_dir  # Input should change
        assert (
            view._view_model.output_dir != invalid_dir
        )  # Model should not update with invalid path

        # Test edge case: empty directory path
        empty_dir = ""
        view._output_dir.setText(empty_dir)
        view._output_dir.editingFinished.emit()
        assert view._output_dir.text() == empty_dir  # Input should change
        assert (
            view._view_model.output_dir == empty_dir
        )  # Model should update with empty path

    def test_figure_dir_update(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : updating the figure directory
        then  : the figure directory should be updated correctly
        """
        view = dialog_view

        # Test updating the figure directory
        initial_value = view._figure_dir_edit.text()
        assert initial_value == ""

        # Test valid directory path
        valid_dir = Path.cwd().joinpath("output")
        if not valid_dir.exists():
            valid_dir.mkdir()
        valid_dir = str(valid_dir)
        view._figure_dir_edit.setText(valid_dir)
        view._figure_dir_edit.editingFinished.emit()
        assert view._figure_dir_edit.text() == valid_dir
        assert view._view_model.figure_dir == valid_dir

        # Test invalid directory path
        invalid_dir = "invalid_path"
        view._figure_dir_edit.setText(invalid_dir)
        view._figure_dir_edit.editingFinished.emit()
        assert view._figure_dir_edit.text() == invalid_dir  # Input should change
        assert (
            view._view_model.figure_dir != invalid_dir
        )  # Model should not update with invalid path

        # Test edge case: empty directory path
        empty_dir = ""
        view._figure_dir_edit.setText(empty_dir)
        view._figure_dir_edit.editingFinished.emit()
        assert view._figure_dir_edit.text() == empty_dir  # Input should change
        assert (
            view._view_model.figure_dir == empty_dir
        )  # Model should update with empty path

    def test_qthreshold_update(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : updating the qthreshold QLineEdit
        then  : the qthreshold value should be updated correctly
        """
        # Test updating the test_qthreshold_update QLineEdit
        initial_value = dialog_view._qthr.text()
        assert initial_value == "800.0"

        # Test valid input, but less than qstagnant
        new_value = "10.0"
        dialog_view._qthr.setText(new_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() != new_value
        assert dialog_view._qthr.text() == str(
            dialog_view._view_model.current_reach.qstagnant
        )

        # Test valid input
        new_value = "900.0"
        dialog_view._qthr.setText(new_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() == new_value

        # Test invalid input
        invalid_value = "abc"
        dialog_view._qthr.setText(invalid_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() == invalid_value
        assert dialog_view._view_model.model.qthreshold == float(
            new_value
        )  # Input should not change

        # Test edge case: empty input
        empty_value = ""
        dialog_view._qthr.setText(empty_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() == empty_value
        assert dialog_view._view_model.model.qthreshold == float(
            new_value
        )  # Input should not change

        # Reset to inital value
        dialog_view._qthr.setText(initial_value)
        dialog_view._qthr.editingFinished.emit()

    def test_ucritical_update(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : updating the ucritical QLineEdit
        then  : the ucritical value should be updated correctly
        """
        # Test updating the ucritical QLineEdit
        initial_value = dialog_view._ucrit.text()
        assert initial_value == "0.3"

        # Test valid input
        new_value = "5.0"
        dialog_view._ucrit.setText(new_value)
        dialog_view._ucrit.editingFinished.emit()
        assert dialog_view._ucrit.text() == new_value

        # Test invalid input
        invalid_value = "xyz"
        dialog_view._ucrit.setText(invalid_value)
        dialog_view._ucrit.editingFinished.emit()
        assert dialog_view._ucrit.text() == invalid_value
        assert dialog_view._view_model.model.ucritical == float(new_value)

        # Test edge case: empty input
        empty_value = ""
        dialog_view._ucrit.setText(empty_value)
        dialog_view._ucrit.editingFinished.emit()
        assert dialog_view._ucrit.text() == empty_value
        assert dialog_view._view_model.model.ucritical == float(new_value)

        # Reset to inital value
        dialog_view._ucrit.setText(initial_value)
        dialog_view._ucrit.editingFinished.emit()

    def test_branch_and_reach_selection(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : selecting branches and reaches
        then  : the selected branch and reach should be updated correctly
        """
        # Test branch and reach selection
        num_branches = dialog_view._branch.count()
        num_reaches = dialog_view._reach.count()

        # Test selecting each branch and reach
        for branch_index in range(num_branches):
            for reach_index in range(num_reaches):
                dialog_view._branch.setCurrentIndex(branch_index)
                dialog_view._reach.setCurrentIndex(reach_index)
                assert dialog_view._branch.currentIndex() == branch_index
                assert dialog_view._reach.currentIndex() == reach_index


class Test_update_plotting:
    def test_update_plotting_make_plots(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : updating the plotting settings for making plots
        then  : the plotting settings should be updated correctly
        """
        # Test updating the plotting settings
        view = dialog_view
        initial_value = view._make_plots_edit.isChecked()
        assert not initial_value

        # Test enabling plotting
        view._make_plots_edit.setChecked(True)
        assert view._make_plots_edit.isChecked() == True
        assert view._save_plots.isEnabled() == True
        assert view._save_plots_edit.isEnabled() == True
        assert view._figure_dir.isEnabled() == False
        assert view._figure_dir_edit.isEnabled() == False
        figure_dir_button = view._general_widget.findChild(
            QPushButton, "figure_dir_edit_button"
        )
        assert figure_dir_button.isEnabled() == False
        assert view._close_plots.isEnabled() == True
        assert view._close_plots_edit.isEnabled() == True

        # Test disabling plotting
        view._make_plots_edit.setChecked(False)
        assert view._make_plots_edit.isChecked() == False
        assert view._save_plots_edit.isEnabled() == False
        assert view._figure_dir_edit.isEnabled() == False
        assert figure_dir_button.isEnabled() == False
        assert view._close_plots_edit.isEnabled() == False

    def test_update_plotting_make_plots_is_true_save_plot(
        self, dialog_view: DialogView
    ):
        """
        given : dialog_view
        when  : updating the plotting settings for saving plots
        then  : the plotting settings should be updated correctly
        """
        view = dialog_view

        # Test updating the plotting settings
        view = dialog_view
        view._make_plots_edit.setChecked(True)
        initial_value = view._save_plots_edit.isChecked()
        assert not initial_value

        # Test enabling save plotting
        view._save_plots_edit.setChecked(True)
        assert view._save_plots.isEnabled() == True
        assert view._save_plots_edit.isEnabled() == True
        assert view._save_plots_edit.isChecked() == True

        assert view._figure_dir.isEnabled() == True
        assert view._figure_dir_edit.isEnabled() == True
        figure_dir_button = view._general_widget.findChild(
            QPushButton, "figure_dir_edit_button"
        )
        assert figure_dir_button.isEnabled() == True

        # Test disabling plotting
        view._save_plots_edit.setChecked(False)
        assert view._save_plots_edit.isEnabled() == True
        assert view._figure_dir_edit.isEnabled() == False
        assert figure_dir_button.isEnabled() == False
        assert view._close_plots_edit.isEnabled() == True


class Test_popup:
    def test_show_error(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : showing an error popup
        then  : the error message should be displayed correctly
        """
        error_message = "This is an error message"
        with monkeypatch.context() as m:
            m.setattr(QMessageBox, "exec_", MagicMock())
            m.setattr(QMessageBox, "setText", MagicMock())
            m.setattr(QMessageBox, "setWindowTitle", MagicMock())
            dialog_view._show_error(error_message)
            QMessageBox.setWindowTitle.assert_called_once_with("Error")
            QMessageBox.setText.assert_called_once_with(error_message)
            QMessageBox.exec_.assert_called_once()

    def test_show_message(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : showing a message popup
        then  : the message should be displayed correctly
        """
        message = "This is a message"
        with monkeypatch.context() as m:
            m.setattr(QMessageBox, "exec_", MagicMock())
            m.setattr(QMessageBox, "setText", MagicMock())
            m.setattr(QMessageBox, "setWindowTitle", MagicMock())
            dialog_view._show_message(message)
            QMessageBox.setWindowTitle.assert_called_once_with("Information")
            QMessageBox.setText.assert_called_once_with(message)
            QMessageBox.exec_.assert_called_once()

    def test_menu_about_self(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : opening the about menu
        then  : the about message should be displayed correctly
        """
        with monkeypatch.context() as m:
            m.setattr(QMessageBox, "exec_", MagicMock())
            m.setattr(QMessageBox, "setText", MagicMock())
            m.setattr(QMessageBox, "setWindowTitle", MagicMock())
            dialog_view._menu_about_self()
            QMessageBox.setWindowTitle.assert_called_once_with(gui_text("about"))
            QMessageBox.setText.assert_called_once_with(
                "D-FAST Morphological Impact " + dfastmi.__version__
            )
            QMessageBox.exec_.assert_called_once()

    def test_menu_open_manual(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : opening the user manual menu
        then  : the user manual should be opened correctly
        """
        # Mock os.startfile
        mock_startfile = MagicMock()
        monkeypatch.setattr("os.startfile", mock_startfile)

        dialog_view._menu_open_manual()

        # Assert that subprocess.Popen was called with the expected arguments
        mock_startfile.assert_called_once_with(dialog_view._view_model.manual_filename)


class Test_select:
    def test_selectFolder_output_dir_edit(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : selecting a folder for the output directory
        then  : the output directory should be updated correctly
        """
        # Create a mock QFileDialog.getExistingDirectory function
        mock_getExistingDirectory = MagicMock(return_value="/path/to/folder")
        monkeypatch.setattr(
            QFileDialog, "getExistingDirectory", mock_getExistingDirectory
        )

        # Call the method with the desired key
        dialog_view._select_folder("output_dir")

        # Assert that the appropriate setText and view_model attribute assignment calls were made
        assert dialog_view._output_dir.text() == "/path/to/folder"
        assert dialog_view._view_model.model.output_dir == "/path/to/folder"

    def test_selectFolder_figure_dir_edit(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : selecting a folder for the figure directory
        then  : the figure directory should be updated correctly
        """
        # Create a mock QFileDialog.getExistingDirectory function
        mock_getExistingDirectory = MagicMock(return_value="/path/to/folder")
        monkeypatch.setattr(
            QFileDialog, "getExistingDirectory", mock_getExistingDirectory
        )

        # Call the method with the desired key
        dialog_view._select_folder("figure_dir_edit")

        # Assert that the appropriate setText and view_model attribute assignment calls were made
        assert dialog_view._figure_dir_edit.text() == "/path/to/folder"
        assert dialog_view._view_model.model.figure_dir == "/path/to/folder"

    def test_selectFile_reference_edit(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : selecting a file for a reference edit
        then  : the reference file should be updated correctly
        """
        # Create a mock QFileDialog.getExistingDirectory function
        mock_getOpenFileName = MagicMock(return_value=["/path/to/file"])
        monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_getOpenFileName)

        # Call the method with the desired key
        key = "3000.0_reference"
        dialog_view._select_file(key)

        # Assert that the appropriate setText and view_model attribute assignment calls were made

        input_box = dialog_view._general_widget.findChild(QLineEdit, key)
        assert input_box.text() == "/path/to/file"
        assert dialog_view._view_model.reference_files["3000.0"] == "/path/to/file"

    def test_selectFile_with_measure_edit(self, dialog_view: DialogView, monkeypatch):
        """
        given : dialog_view
        when  : selecting a file for a measure edit
        then  : the measure file should be updated correctly
        """
        # Create a mock QFileDialog.getExistingDirectory function
        mock_getOpenFileName = MagicMock(return_value=["/path/to/file_with_measure"])
        monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_getOpenFileName)

        # Call the method with the desired key
        key = "4000.0_with_measure"
        dialog_view._select_file(key)

        # Assert that the appropriate setText and view_model attribute assignment calls were made

        input_box = dialog_view._general_widget.findChild(QLineEdit, key)
        assert input_box.text() == "/path/to/file_with_measure"
        assert (
            dialog_view._view_model.measure_files["4000.0"]
            == "/path/to/file_with_measure"
        )


class Test_view_model_updates:
    def test_update_branch(self, dialog_view: DialogView, mocker):
        """
        given : dialog_view
        when  : updating the branch
        then  : the branch and associated attributes should be updated correctly
        """
        # Call the method to be tested
        dialog_view._update_branch(
            "Bovenrijn & Waal"
        )  # Pass the branch name to simulate the update

        # Assertions
        assert dialog_view._case_description.text() == "myCase"
        assert dialog_view._branch.currentText() == "Bovenrijn & Waal"
        assert dialog_view._reach.count() == len(
            dialog_view._view_model.current_branch.reaches
        )
        assert (
            dialog_view._qloc.text() == dialog_view._view_model.current_branch.qlocation
        )
        assert dialog_view._qthr.text() == str(dialog_view._view_model.model.qthreshold)
        assert dialog_view._ucrit.text() == str(dialog_view._view_model.model.ucritical)
        assert dialog_view._slength.text() == dialog_view._view_model.slength
        assert (
            dialog_view._output_dir.text() == dialog_view._view_model.model.output_dir
        )
        assert (
            dialog_view._make_plots_edit.isChecked()
            == dialog_view._view_model.model.plotting
        )
        assert (
            dialog_view._save_plots_edit.isChecked()
            == dialog_view._view_model.model.save_plots
        )
        assert (
            dialog_view._close_plots_edit.isChecked()
            == dialog_view._view_model.model.close_plots
        )

    def test_update_reach(self, dialog_view: DialogView):
        """
        given : dialog_view
        when  : updating the reach
        then  : the reach and associated attributes should be updated correctly
        """
        # Call the method to be tested
        dialog_view._update_reach(
            "Boven-Waal                   km  868-886"
        )  # Pass the reach name to simulate the update

        # Assertions
        assert (
            dialog_view._reach.currentText()
            == "Boven-Waal                   km  868-886"
        )
        assert dialog_view._slength.text() == dialog_view._view_model.slength


def test_update_condition_files(dialog_view: DialogView):
    """
    given : dialog_view
    when  : updating condition files
    then  : the condition files should be updated correctly
    """
    # Mock the reference files and measure files
    reference_files = {3000.0: "reference_file_10.txt", 4000.0: "reference_file_20.txt"}
    measure_files = {3000.0: "measure_file_10.txt", 4000.0: "measure_file_20.txt"}

    # Set the mocked data
    dialog_view._view_model._reference_files = reference_files
    dialog_view._view_model._measure_files = measure_files

    # Trigger the method to be tested
    dialog_view._update_condition_files()

    # Assertions
    # Assuming your UI components are correctly updated, you can assert their properties
    # For example, assert that the QLineEdit objects representing the file paths have been updated
    assert (
        dialog_view._general_widget.findChild(QLineEdit, "3000.0_reference").text()
        == "reference_file_10.txt"
    )
    assert (
        dialog_view._general_widget.findChild(QLineEdit, "3000.0_with_measure").text()
        == "measure_file_10.txt"
    )
    assert (
        dialog_view._general_widget.findChild(QLineEdit, "4000.0_reference").text()
        == "reference_file_20.txt"
    )
    assert (
        dialog_view._general_widget.findChild(QLineEdit, "4000.0_with_measure").text()
        == "measure_file_20.txt"
    )
