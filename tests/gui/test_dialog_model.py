from configparser import ConfigParser
from typing import Dict
from unittest.mock import MagicMock

import pytest
from mock import patch
from packaging.version import Version

from dfastmi.config.ConfigFileOperations import (
    ConfigFileOperations,
    check_configuration,
)
from dfastmi.gui.dialog_model import DialogModel, GeneralConfig
from dfastmi.io.AReach import AReach
from dfastmi.io.Branch import Branch
from dfastmi.io.RiversObject import RiversObject


@pytest.fixture
def mock_config_parser() -> MagicMock:
    """
    Fixture for creating a MagicMock object of ConfigParser.

    given:  A requirement to mock the behavior of ConfigParser for testing purposes.
    when:   Creating a MagicMock object of ConfigParser.
    then:   The MagicMock object is returned for further use in tests.
    """
    return MagicMock(ConfigParser)


@pytest.fixture
def mock_config_file_operations() -> MagicMock:
    """Fixture for creating a MagicMock object of ConfigFileOperations."""
    return MagicMock(ConfigFileOperations)


@pytest.fixture
def mock_branch() -> MagicMock:
    """Fixture for creating a MagicMock object of Branch."""
    branch = MagicMock(Branch)
    branch.name = "MyBranch"
    return branch


@pytest.fixture
def mock_reach() -> MagicMock:
    """Fixture for creating a MagicMock object of AReach."""
    reach = MagicMock(AReach)
    reach.name = "MyReach"
    reach.hydro_q = (80.1, 80.2)
    return reach


@pytest.fixture
def mock_rivers_object() -> MagicMock:
    """Fixture for creating a MagicMock object of RiversObject."""
    rivers = MagicMock(RiversObject)
    rivers.version = Version("3.0")
    return rivers


@pytest.fixture
def mock_reference_files() -> Dict[float, str]:
    """Fixture for creating mock reference files."""
    return {"80.1": "reference1.txt", "80.2": "reference2.txt"}


@pytest.fixture
def mock_measure_files() -> Dict[float, str]:
    """Fixture for creating mock measurement files."""
    return {"80.1": "measure1.txt", "80.2": "measure2.txt"}


@pytest.fixture
def dialog_model(mock_rivers_object: MagicMock) -> DialogModel:
    """Fixture for creating a DialogModel instance."""
    return DialogModel(mock_rivers_object)


@pytest.fixture
def mock_batch_mode_core() -> MagicMock:
    """Fixture for mocking the batch_mode_core function."""
    with patch("dfastmi.batch.core.batch_mode_core") as mock_batch_mode_core:
        # Set the return value of batch_mode_core to True (success)
        mock_batch_mode_core.return_value = True
        yield mock_batch_mode_core


def test_run_analysis_success(mock_batch_mode_core: MagicMock) -> None:
    """
    Test case for successful analysis run.

    given: A DialogModel instance.
    when: Calling the run_analysis method.
    then: The batch_mode_core function is called and the return value of run_analysis is True (success).
    """
    # Create an instance of DialogModel
    model = DialogModel(rivers_configuration=None)

    # Call the run_analysis method
    result = model.run_analysis()

    # Check that batch_mode_core was called
    mock_batch_mode_core.assert_called_once()

    # Check that the return value of run_analysis is True (success)
    assert result is True


def test_run_analysis_failure(mock_batch_mode_core: MagicMock) -> None:
    """
    Test case for failed analysis run.

    given: A DialogModel instance.
    when: Calling the run_analysis method with batch_mode_core returning False.
    then: The batch_mode_core function is called and the return value of run_analysis is False (failure).
    """
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


class Test_create_configuration:
    @pytest.fixture
    def mock_general_config_object(self) -> MagicMock:
        """Fixture for creating a MagicMock object of GeneralConfig model."""
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
            "ClosePlots": False,
        }

        # Creating an instance of GeneralConfig with custom values
        custom_config = GeneralConfig(**custom_values)

        # Creating a MagicMock object for the model_dump method
        mock_model_dump = MagicMock(return_value=custom_config.model_dump())
        return mock_model_dump

    def test_create_configuration(self, dialog_model: DialogModel) -> None:
        """
        Test case for creating a configuration.

        given: A DialogModel instance.
        when: Calling the create_configuration method.
        then: The configuration is created and the 'General' section is present in the configuration.
        """
        dialog_model.create_configuration()
        assert dialog_model.config is not None
        assert "General" in dialog_model.config

    def test_create_custom_configuration(
        self, dialog_model: DialogModel, mock_general_config_object: MagicMock
    ) -> None:
        """
        Test case for creating a custom configuration.

        given: A DialogModel instance and a mock of GeneralConfig.
        when: Calling the create_configuration method with a mocked GeneralConfig object.
        then: The configuration is customized with the mocked GeneralConfig attributes.
        """
        org = GeneralConfig.model_dump
        GeneralConfig.model_dump = mock_general_config_object
        dialog_model.create_configuration()
        GeneralConfig.model_dump = org
        assert dialog_model.config is not None
        assert "General" in dialog_model.config
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

def test_load_configuration(dialog_model: DialogModel, mocker) -> None:
    """
    Test case for loading configuration.

    given: A DialogModel instance and mocker.
    when: Loading a configuration file.
    then: The configuration object is not None.
    """
    filename = "test.cfg"
    config = ConfigParser()
    config["General"] = {}
    mock_load_config = mocker.patch.object(
        ConfigFileOperations, "load_configuration_file", return_value=config
    )
    assert dialog_model.load_configuration(filename)
    mock_load_config.assert_called_once_with(filename)
    assert dialog_model.config is not None


def test_load_configuration_except(dialog_model: DialogModel, mocker) -> None:
    """
    Test case for loading configuration with an exception.

    given: A DialogModel instance and mocker.
    when: Loading a configuration file that raises an exception.
    then: The loading process fails.
    """
    filename = "test.cfg"
    config = ConfigParser()
    config["General"] = {}
    mocker.patch.object(
        ConfigFileOperations,
        "load_configuration_file",
        side_effect=Exception("mocked error"),
    )
    assert not dialog_model.load_configuration(filename)


def test_load_configuration_except_true(dialog_model: DialogModel, mocker) -> None:
    """
    Test case for loading configuration with an exception.

    given: A DialogModel instance and mocker.
    when: Loading a configuration file that raises an exception.
    then: The loading process fails, but the method returns True.
    """
    filename = "dfastmi.cfg"
    config = ConfigParser()
    config["General"] = {}
    mocker.patch.object(
        ConfigFileOperations,
        "load_configuration_file",
        side_effect=Exception("mocked error"),
    )
    assert dialog_model.load_configuration(filename)


def test_check_configuration(
    dialog_model: DialogModel,
    mock_branch: MagicMock,
    mock_reach: MagicMock,
    mock_reference_files: Dict[float, str],
    mock_measure_files: Dict[float, str],
) -> None:
    """
    Test case for checking configuration.

    given: A DialogModel instance and mocked branch, reach, reference files, and measurement files.
    when: Checking the configuration.
    then: The configuration is checked with the expected branch, reach, reference files, and measurement files.
    """
    # Mocking the method calls inside the methods
    dialog_model.get_configuration = MagicMock(return_value=ConfigParser())
    dialog_model._get_condition_configuration = MagicMock()

    # Call the check_configuration method
    result = dialog_model.check_configuration(
        mock_branch, mock_reach, mock_reference_files, mock_measure_files
    )

    assert (
        not result
    )  # no valid configuration is created to be checked, logically this is false

    # Assert that get_configuration is called with the correct arguments
    dialog_model.get_configuration.assert_called_once_with(
        mock_branch, mock_reach, mock_reference_files, mock_measure_files
    )


def test_get_configuration(
    dialog_model: DialogModel,
    mock_branch: MagicMock,
    mock_reach: MagicMock,
    mock_reference_files: Dict[float, str],
    mock_measure_files: Dict[float, str],
) -> None:
    """
    Test case for getting configuration.

    given: A DialogModel instance and mocked branch, reach, reference files, and measurement files.
    when: Getting the configuration.
    then: The configuration is retrieved and checked for correctness.
    """
    # Call the get_configuration method
    config_parser = dialog_model.get_configuration(
        mock_branch, mock_reach, mock_reference_files, mock_measure_files
    )

    # Check if the configuration parser is an instance of ConfigParser
    assert isinstance(config_parser, ConfigParser)

    # Check if the "General" section is present in the configuration parser
    assert "General" in config_parser

    # Check if the values in the "General" section are set correctly
    general_section = config_parser["General"]
    assert general_section["Branch"] == mock_branch.name
    assert general_section["Reach"] == mock_reach.name
    assert float(general_section["Qthreshold"]) == dialog_model.qthreshold
    assert float(general_section["Ucrit"]) == dialog_model.ucritical
    assert general_section["OutputDir"] == dialog_model.output_dir
    assert general_section.getboolean("Plotting") == dialog_model.plotting
    assert general_section.getboolean("SavePlots") == dialog_model.save_plots
    assert general_section["FigureDir"] == dialog_model.figure_dir
    assert general_section.getboolean("ClosePlots") == dialog_model.close_plots

    # Check if the condition configurations are added correctly
    num_conditions = len(mock_reach.hydro_q)
    for i in range(1, num_conditions + 1):
        condition_key = f"C{i}"
        assert condition_key in config_parser
        condition_section = config_parser[condition_key]
        discharge = list(mock_reference_files.keys())[i - 1]
        assert condition_section["Discharge"] == discharge
        assert condition_section["Reference"] == mock_reference_files[discharge]
        assert condition_section["WithMeasure"] == mock_measure_files[discharge]
