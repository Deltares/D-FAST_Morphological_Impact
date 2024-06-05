import os
from pathlib import Path

import mock
import pytest

from dfastmi.gui.dialog_model import DialogModel
from dfastmi.io.IBranch import IBranch
from dfastmi.io.IReach import IReach
from dfastmi.io.RiversObject import RiversObject

pytestmark = pytest.mark.qt_api("pyqt5")
from unittest.mock import MagicMock

from dfastmi.batch.DFastUtils import get_progloc
from dfastmi.gui.dialog_view_model import DialogViewModel


@pytest.fixture
def mock_model():
    # Create a MagicMock instance to use as a mock model
    mock_model = MagicMock()
    mock_model.rivers.branches = [MagicMock()]
    mock_model.rivers.branches[0].name = "New Branch"
    mock_model.rivers.branches[0].reaches = [MagicMock()]
    # Mock qthreshold and qstagnant attributes with numeric values
    mock_model.qthreshold = 5.0
    mock_model.rivers.branches[0].reaches[0].qstagnant = 10.0
    mock_model.ucritical = 5.0
    mock_model.rivers.branches[0].reaches[0].ucritical = 10.0
    return mock_model


@pytest.fixture
def dialog_view_model(mock_model):
    # Create a DialogViewModel instance with the mock model
    return DialogViewModel(mock_model)


def test_initialization(dialog_view_model, mock_model):
    """
    given : dialog_view_model and mock_model
    when  : initialization method is called
    then  : current branch and reach should be set correctly
    """
    # Check if the current branch and reach are set correctly during initialization
    assert dialog_view_model.current_branch == mock_model.rivers.branches[0]
    assert dialog_view_model.current_reach == mock_model.rivers.branches[0].reaches[0]


def test_updated_branch(qtbot, dialog_view_model):
    """
    given : qtbot and dialog_view_model
    when  : current branch is updated
    then  : signal should be emitted and received correctly
    """
    result = []

    def on_branch_changed(branch):
        result.append(branch)

    dialog_view_model.branch_changed.connect(on_branch_changed)
    mock_branch = mock.create_autospec(spec=IBranch)
    mock_branch.name = "myBranch"

    # Use qtbot to wait for the signal
    with qtbot.waitSignal(dialog_view_model.branch_changed):
        # Set the current branch
        dialog_view_model.current_branch = mock_branch

    # Check if the signal was emitted and received correctly
    assert result == ["myBranch"]
    assert dialog_view_model.current_branch == mock_branch


def test_updated_reach(qtbot, dialog_view_model):
    """
    given : qtbot and dialog_view_model
    when  : current reach is updated
    then  : signal should be emitted and received correctly
    """
    result = []

    def on_reach_changed(reach):
        result.append(reach)

    dialog_view_model.reach_changed.connect(on_reach_changed)
    mock_reach = mock.create_autospec(spec=IReach)
    mock_reach.name = "myReach"
    mock_reach.qstagnant = 10.0
    mock_reach.ucritical = 5.0

    # Use qtbot to wait for the signal
    with qtbot.waitSignal(dialog_view_model.reach_changed):
        # Set the current reach
        dialog_view_model.current_reach = mock_reach

    # Check if the signal was emitted and received correctly
    assert result == ["myReach"]
    assert dialog_view_model.current_reach == mock_reach


def test_get_configuration(dialog_view_model, mock_model):
    """
    given : dialog_view_model and mock_model
    when  : get_configuration method is called
    then  : correct configuration parser should be returned
    """
    # Test the get_configuration method
    config_parser = MagicMock()
    mock_model.get_configuration.return_value = config_parser
    assert dialog_view_model.get_configuration() == config_parser


def test_run_analysis(dialog_view_model, mock_model):
    """
    given : dialog_view_model and mock_model
    when  : run_analysis method is called
    then  : it should return True
    """
    # Test the run_analysis method
    mock_model.run_analysis.return_value = True
    assert dialog_view_model.run_analysis() is True


def test_load_configuration(dialog_view_model, mock_model):
    """
    given : dialog_view_model and mock_model
    when  : load_configuration method is called
    then  : current branch and reach should be set correctly
    """
    # Test the load_configuration method
    mock_model.branch_name = "Branch1"
    mock_model.reach_name = "Reach1"
    mock_model.config.sections.return_value = ["section1"]
    mock_model.config["section1"].getfloat.return_value = 10.0
    mock_model.config["section1"].get.return_value = "reference_file", "measure_file"
    mock_model.figure_dir = "mocked_figure_directory"
    mock_model.output_dir = "mocked_output_directory"

    mock_branch = mock.create_autospec(spec=IBranch)
    mock_branch.name = "myBranch"
    mock_model.rivers.get_branch.return_value = mock_branch

    mock_reach = mock.create_autospec(spec=IReach)
    mock_reach.name = "myReach"
    mock_reach.qstagnant = 10.0
    mock_reach.ucritical = 5.0
    mock_branch.get_reach.return_value = mock_reach

    assert dialog_view_model.load_configuration("test_config.ini")
    assert dialog_view_model.current_branch == mock_branch
    assert dialog_view_model.current_reach == mock_reach


def test_check_configuration(dialog_view_model, mock_model):
    """
    given : dialog_view_model and mock_model
    when  : check_configuration method is called
    then  : it should return True
    """
    # Test the check_configuration method
    mock_model.check_configuration.return_value = True
    assert dialog_view_model.check_configuration() is True


def test_manual_filename(dialog_view_model):
    """
    given : dialog_view_model
    when  : accessing manual_filename property
    then  : correct path to the user manual should be returned
    """
    # Test the manual_filename property
    assert dialog_view_model.manual_filename == str(
        get_progloc().joinpath("dfastmi_usermanual.pdf")
    )


def test_report(dialog_view_model):
    """
    given : dialog_view_model
    when  : accessing report property
    then  : correct report filename should be returned
    """
    # Test the report property
    mock_get_filename = MagicMock(return_value="dummy_report_filename")
    with mock.patch(
        "dfastmi.io.ApplicationSettingsHelper.ApplicationSettingsHelper.get_filename",
        mock_get_filename,
    ):
        assert dialog_view_model.report == "dummy_report_filename"


def test_load_configuration_with_unknown_key_value_save_and_load_unknown_are_retained(
    dialog_view_model, tmp_path
):
    """
    given : dialog_view_model and mock_model
    when  : load_configuration method is called
    then  : current branch and reach should be set correctly
    """
    rivers = RiversObject("tests/c01 - GendtseWaardNevengeul/rivers_Q4000_v2.ini")
    dialog_view_model.model = DialogModel(rivers)
    cwd = os.getcwd()
    tstdir = "tests/files"
    try:
        os.chdir(tstdir)
        config_file = "Qmin_4000_v2_rkm_with_unknown_key.cfg"
        dialog_view_model.load_configuration(config_file)
        file_location = tmp_path.joinpath("test.cfg")
        dialog_view_model.save_configuration(file_location)
        dialog_view_model.model = DialogModel(rivers)
        dialog_view_model.load_configuration(file_location)
        assert dialog_view_model.model.config.has_option("General", "UnknownKey")
        assert dialog_view_model.model.config["General"]["UnknownKey"] == "unkown value"
        assert dialog_view_model.model.config["Onzin1"]["Troep"] == "1000.0"
    finally:
        os.chdir(cwd)
