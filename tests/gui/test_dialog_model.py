from unittest.mock import MagicMock
from configparser import ConfigParser

from mock import patch
from dfastmi.gui.dialog_model import DialogModel, GeneralConfig
from dfastmi.io.Branch import Branch
from dfastmi.io.AReach import AReach
from dfastmi.io.RiversObject import RiversObject
from dfastmi.io.ConfigFileOperations import ConfigFileOperations, check_configuration
import pytest

@pytest.fixture
def mock_config_parser():
    return MagicMock(ConfigParser)

@pytest.fixture
def mock_config_file_operations():
    return MagicMock(ConfigFileOperations)

@pytest.fixture
def mock_branch():
    return MagicMock(Branch)

@pytest.fixture
def mock_reach():
    return MagicMock(AReach)

@pytest.fixture
def mock_rivers_object():
    return MagicMock(RiversObject)

@pytest.fixture
def mock_general_config_object():
    # Custom values for GeneralConfig attributes
    custom_values = {
        "Version": "3.0",
        "Branch": "Custom Branch",
        "Reach": "Custom Reach",
        "Qthreshold": 0.5,
        "Ucrit": 0.6,
        "OutputDir": "/path/to/output",
        "Plotting": True,
        "SavePlots": True,
        "FigureDir": "/path/to/figures",
        "ClosePlots": False
    }

    # Creating an instance of GeneralConfig with custom values
    custom_config = GeneralConfig(**custom_values)

    # Creating a MagicMock object for the model_dump method
    mock_model_dump = MagicMock(return_value=custom_config.model_dump())
    return mock_model_dump

@pytest.fixture
def dialog_model(mock_rivers_object, mock_config_parser):
    return DialogModel(mock_rivers_object, mock_config_parser)

@pytest.fixture
def mock_batch_mode_core():
    with patch("dfastmi.batch.core.batch_mode_core") as mock_batch_mode_core:
        # Set the return value of batch_mode_core to True (success)
        mock_batch_mode_core.return_value = True
        yield mock_batch_mode_core

def test_run_analysis_success(mock_batch_mode_core):
    # Create an instance of DialogModel
    model = DialogModel(rivers_configuration=None)

    # Call the run_analysis method
    result = model.run_analysis()

    # Check that batch_mode_core was called
    mock_batch_mode_core.assert_called_once()

    # Check that the return value of run_analysis is True (success)
    assert result is True

def test_run_analysis_failure(mock_batch_mode_core):
    # Set the return value of batch_mode_core to False (failure)
    mock_batch_mode_core.return_value = False

    # Create an instance of DialogModel
    model = DialogModel(rivers_configuration=None)

    # Call the run_analysis method
    result = model.run_analysis()

    # Check that batch_mode_core was called
    mock_batch_mode_core.assert_called_once()

    # Check that the return value of run_analysis is False (failure)
    assert result is False

def test_run_analysis_exception(mock_batch_mode_core):
    # Set the return value of batch_mode_core to False (failure)
    mock_batch_mode_core.side_effect=Exception("mocked")

    # Create an instance of DialogModel
    model = DialogModel(rivers_configuration=None)

    # Call the run_analysis method
    result = model.run_analysis()

    # Check that batch_mode_core was called
    mock_batch_mode_core.assert_called_once()

    # Check that the return value of run_analysis is False (failure)
    assert result is False

def test_create_configuration(dialog_model):
    dialog_model.create_configuration()
    assert dialog_model.config is not None
    assert 'General' in dialog_model.config    

def test_create_custom_configuration(dialog_model, mock_general_config_object):
    GeneralConfig.model_dump = mock_general_config_object
    dialog_model.create_configuration()    
    assert dialog_model.config is not None    
    assert 'General' in dialog_model.config    
    assert dialog_model.section is not None
    assert dialog_model.branch_name == "Custom Branch"
    assert dialog_model.reach_name == "Custom Reach"
    assert dialog_model.qthreshold == 0.5
    assert dialog_model.ucritical == 0.6
    assert dialog_model.output_dir == "/path/to/output"
    assert dialog_model.plotting
    assert dialog_model.save_plots
    assert dialog_model.figure_dir == "/path/to/figures"
    assert not dialog_model.close_plots

def test_load_configuration_init(mock_rivers_object, mocker):
    filename = "test.cfg"
    config = ConfigParser()
    config["General"] = {}
    mock_load_config = mocker.patch.object(ConfigFileOperations, 'load_configuration_file', return_value=config)
    model = DialogModel(mock_rivers_object, filename)
    mock_load_config.assert_called_once_with(filename)
    assert model.config is not None

def test_load_configuration(dialog_model, mocker):
    filename = "test.cfg"
    config = ConfigParser()
    config["General"] = {}
    mock_load_config = mocker.patch.object(ConfigFileOperations, 'load_configuration_file', return_value=config)
    assert dialog_model.load_configuration(filename)
    mock_load_config.assert_called_once_with(filename)
    assert dialog_model.config is not None

def test_load_configuration_except(dialog_model, mocker):
    filename = "test.cfg"
    config = ConfigParser()
    config["General"] = {}
    mocker.patch.object(ConfigFileOperations, 'load_configuration_file', side_effect=Exception('mocked error'))
    assert not dialog_model.load_configuration(filename)

def test_load_configuration_except_true(dialog_model, mocker):
    filename = "dfastmi.cfg"
    config = ConfigParser()
    config["General"] = {}
    mocker.patch.object(ConfigFileOperations, 'load_configuration_file', side_effect=Exception('mocked error'))
    assert dialog_model.load_configuration(filename)
    
# def test_branch_name_property(dialog_model, mock_config_parser):
#     mock_config_parser.__getitem__.return_value = "TestBranch"
#     assert dialog_model.branch_name == "TestBranch"