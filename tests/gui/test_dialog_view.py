import os
import pytest
from PyQt5.QtWidgets import QApplication, QPushButton, QMessageBox, QFileDialog
from unittest.mock import MagicMock
import dfastmi
from dfastmi.batch.DFastUtils import get_progloc
from dfastmi.gui.dialog_model import DialogModel
from dfastmi.gui.dialog_view import DialogView
from dfastmi.gui.dialog_view_model import DialogViewModel
from dfastmi.io.RiversObject import RiversObject

@pytest.fixture(scope="module")
def dialog_view():
    # Initialize model, view model, and view
    rivers_configuration = RiversObject("tests/c01 - GendtseWaardNevengeul/rivers_Q4000_v2.ini")  # You need to provide proper initialization parameters here
    model = DialogModel(rivers_configuration)
    view_model = DialogViewModel(model)
    view = DialogView(view_model)

    yield view

    # Clean up resources
    del view
    del view_model
    del model
    del rivers_configuration
def test_constructor(dialog_view):
    view = dialog_view

    # Test if the constructor initializes view components with the correct initial state
    assert view._output_dir.text() == view._view_model.output_dir
    assert view._figure_dir_edit.text() == view._view_model.figure_dir
    assert view._make_plots_edit.isChecked() == view._view_model.plotting
    assert view._save_plots_edit.isChecked() == view._view_model.save_plots
    assert view._close_plots_edit.isChecked() == view._view_model.close_plots

class Test_dialog_inputs:    
    def test_output_dir_update(self, dialog_view):
        view = dialog_view

        # Test updating the output directory
        initial_value = view._output_dir.text()

        # Test valid directory path
        valid_dir = os.path.join(os.getcwd(), "output")
        view._output_dir.setText(valid_dir)
        view._output_dir.editingFinished.emit()

        assert view._output_dir.text() == valid_dir
        assert view._view_model.output_dir == valid_dir

        # Test invalid directory path
        invalid_dir = "invalid_path"
        view._output_dir.setText(invalid_dir)
        view._output_dir.editingFinished.emit()
        assert view._output_dir.text() == invalid_dir  # Input should change
        assert view._view_model.output_dir != invalid_dir  # Model should not update with invalid path

        # Test edge case: empty directory path
        empty_dir = ""
        view._output_dir.setText(empty_dir)
        view._output_dir.editingFinished.emit()
        assert view._output_dir.text() == empty_dir  # Input should change
        assert view._view_model.output_dir == empty_dir  # Model should update with empty path

    def test_figure_dir_update(self, dialog_view):
        view = dialog_view

        # Test updating the figure directory
        initial_value = view._figure_dir_edit.text()

        # Test valid directory path
        valid_dir = os.path.join(os.getcwd(), "output")
        view._figure_dir_edit.setText(valid_dir)
        view._figure_dir_edit.editingFinished.emit()
        assert view._figure_dir_edit.text() == valid_dir
        assert view._view_model.figure_dir == valid_dir

        # Test invalid directory path
        invalid_dir = "invalid_path"
        view._figure_dir_edit.setText(invalid_dir)
        view._figure_dir_edit.editingFinished.emit()
        assert view._figure_dir_edit.text() == invalid_dir  # Input should change
        assert view._view_model.figure_dir != invalid_dir  # Model should not update with invalid path

        # Test edge case: empty directory path
        empty_dir = ""
        view._figure_dir_edit.setText(empty_dir)
        view._figure_dir_edit.editingFinished.emit()
        assert view._figure_dir_edit.text() == empty_dir  # Input should change
        assert view._view_model.figure_dir == empty_dir  # Model should update with empty path
    
    def test_qthreshold_update(self, dialog_view, mocker):
        # Test updating the qthreshold QLineEdit
        initial_value = dialog_view._qthr.text()
        

        # Test valid input
        new_value = "10.0"
        dialog_view._qthr.setText(new_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() == new_value

        # Test invalid input
        mocker.patch.object(dialog_view, "_showMessage")
        invalid_value = "abc"
        dialog_view._qthr.setText(invalid_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() == invalid_value                
        assert dialog_view._view_model.qthreshold == float(new_value)  # Input should not change
        dialog_view._showMessage.assert_called_once_with("Please input valid values for qthreshold")

        # Test edge case: empty input
        mocker.patch.object(dialog_view, "_showMessage")
        empty_value = ""
        dialog_view._qthr.setText(empty_value)
        dialog_view._qthr.editingFinished.emit()
        assert dialog_view._qthr.text() == empty_value  
        assert dialog_view._view_model.qthreshold == float(new_value)  # Input should not change
        dialog_view._showMessage.assert_called_once_with("Please input valid values for qthreshold")
        

    def test_ucritical_update(self, dialog_view, mocker):
        # Test updating the ucritical QLineEdit
        initial_value = dialog_view._ucrit.text()

        # Test valid input
        new_value = "5.0"
        dialog_view._ucrit.setText(new_value)
        dialog_view._ucrit.editingFinished.emit()        
        assert dialog_view._ucrit.text() == new_value

        # Test invalid input
        mocker.patch.object(dialog_view, "_showMessage")
        invalid_value = "xyz"
        dialog_view._ucrit.setText(invalid_value)
        dialog_view._ucrit.editingFinished.emit()
        assert dialog_view._ucrit.text() == invalid_value
        assert dialog_view._view_model.ucritical == float(new_value)
        dialog_view._showMessage.assert_called_once_with("Please input valid values for ucritical")

        # Test edge case: empty input
        mocker.patch.object(dialog_view, "_showMessage")
        empty_value = ""
        dialog_view._ucrit.setText(empty_value)
        dialog_view._ucrit.editingFinished.emit()
        assert dialog_view._ucrit.text() == empty_value
        assert dialog_view._view_model.ucritical == float(new_value)
        dialog_view._showMessage.assert_called_once_with("Please input valid values for ucritical")


    def test_branch_and_reach_selection(self, dialog_view):
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

class Test_update_plotting():
    def test_update_plotting_make_plots(self, dialog_view):
        view = dialog_view

        # Test updating the plotting settings
        initial_value = view._make_plots_edit.isChecked()

        # Test enabling plotting
        view._make_plots_edit.setChecked(True)
        assert view._make_plots_edit.isChecked() == True
        assert view._save_plots.isEnabled() == True
        assert view._save_plots_edit.isEnabled() == True
        assert view._figure_dir.isEnabled() == False
        assert view._figure_dir_edit.isEnabled() == False
        figure_dir_button = view._general_widget.findChild(QPushButton, "figure_dir_edit_button")
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

    def test_update_plotting_make_plots_is_true_save_plot(self, dialog_view):
        view = dialog_view

        # Test updating the plotting settings
        view._make_plots_edit.setChecked(True)
        initial_value = view._save_plots_edit.isChecked()

        # Test enabling save plotting        
        view._save_plots_edit.setChecked(True)
        assert view._save_plots.isEnabled() == True
        assert view._save_plots_edit.isEnabled() == True
        assert view._save_plots_edit.isChecked() == True

        assert view._figure_dir.isEnabled() == True
        assert view._figure_dir_edit.isEnabled() == True
        figure_dir_button = view._general_widget.findChild(QPushButton, "figure_dir_edit_button")
        assert figure_dir_button.isEnabled() == True
        
        # Test disabling plotting
        view._save_plots_edit.setChecked(False)
        assert view._save_plots_edit.isEnabled() == True
        assert view._figure_dir_edit.isEnabled() == False
        assert figure_dir_button.isEnabled() == False
        assert view._close_plots_edit.isEnabled() == True

class Test_popup:    
    def test_showError(self, dialog_view, monkeypatch):
        error_message = "This is an error message"
        with monkeypatch.context() as m:
            m.setattr(QMessageBox, 'exec_', MagicMock())        
            m.setattr(QMessageBox, 'setText', MagicMock())
            m.setattr(QMessageBox, 'setWindowTitle', MagicMock()) 
            dialog_view._showError(error_message)
            QMessageBox.setWindowTitle.assert_called_once_with("Error")
            QMessageBox.setText.assert_called_once_with(error_message)
            QMessageBox.exec_.assert_called_once()

    def test_showMessage(self, dialog_view, monkeypatch):
        message = "This is a message"
        with monkeypatch.context() as m:
            m.setattr(QMessageBox, 'exec_', MagicMock())        
            m.setattr(QMessageBox, 'setText', MagicMock())        
            m.setattr(QMessageBox, 'setWindowTitle', MagicMock())        
            dialog_view._showMessage(message)
            QMessageBox.setWindowTitle.assert_called_once_with("Information")
            QMessageBox.setText.assert_called_once_with(message)
            QMessageBox.exec_.assert_called_once()
    
    def test_menu_about_self(self, dialog_view, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(QMessageBox, 'exec_', MagicMock())        
            m.setattr(QMessageBox, 'setText', MagicMock())        
            m.setattr(QMessageBox, 'setWindowTitle', MagicMock())        
            dialog_view._menu_about_self()
            QMessageBox.setWindowTitle.assert_called_once_with(dialog_view._view_model.gui_text("about"))
            QMessageBox.setText.assert_called_once_with("D-FAST Morphological Impact " + dfastmi.__version__)
            QMessageBox.exec_.assert_called_once()

    def test_menu_open_manual(self, dialog_view, monkeypatch):
        # Mock subprocess.Popen
        mock_popen = MagicMock()
        monkeypatch.setattr("subprocess.Popen", mock_popen)
        
        dialog_view._menu_open_manual()

        # Assert that subprocess.Popen was called with the expected arguments
        mock_popen.assert_called_once_with(dialog_view._view_model.manual_filename, shell=True)

class Test_selectFolder:
    def test_selectFolder_output_dir_edit(self, dialog_view, monkeypatch):
        # Create a mock QFileDialog.getExistingDirectory function
        mock_getExistingDirectory = MagicMock(return_value="/path/to/folder")
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", mock_getExistingDirectory)

        # Call the method with the desired key
        dialog_view._selectFolder("output_dir")

        # Assert that the appropriate setText and view_model attribute assignment calls were made
        assert dialog_view._output_dir.text() == "/path/to/folder"
        assert dialog_view._view_model.output_dir == "/path/to/folder"

    def test_selectFolder_figure_dir_edit(self, dialog_view, monkeypatch):
        # Create a mock QFileDialog.getExistingDirectory function
        mock_getExistingDirectory = MagicMock(return_value="/path/to/folder")
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", mock_getExistingDirectory)

        # Call the method with the desired key
        dialog_view._selectFolder("figure_dir_edit")

        # Assert that the appropriate setText and view_model attribute assignment calls were made
        assert dialog_view._figure_dir_edit.text() == "/path/to/folder"
        assert dialog_view._view_model.figure_dir == "/path/to/folder"
    # Perform additional assertions if needed
