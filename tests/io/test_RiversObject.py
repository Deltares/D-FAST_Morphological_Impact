import os
import sys
from contextlib import contextmanager
from io import StringIO
import pytest
from dfastmi.io.CelerObject import CelerDischarge
from dfastmi.io.Reach import Reach
from dfastmi.io.ReachLegacy import ReachLegacy

from dfastmi.io.RiversObject import RiversObject

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_read_rivers_legacy():
    def given_a_legacy_rivers_config_file_when_read_rivers_then_data_loaded_in_RiverObject(self):
        """
        Testing read_rivers with legacy data
        """
        print("current work directory: ", os.getcwd())       
        
        rivers = RiversObject("tests/files/read_rivers_test.ini")
        
        branch1 = rivers.branches[0]
        assert branch1.name == 'Branch1'
        assert branch1.qlocation == 'L1'
        
        reach1 = branch1.reaches[0]
        assert isinstance(reach1, ReachLegacy)
        assert reach1.name == 'Branch1 R1'
        assert reach1.normal_width == 250.0
        assert reach1.ucritical == 0.3
        assert reach1.qstagnant == 50.0

        assert reach1.proprate_high == 3.14
        assert reach1.proprate_low == 0.8
        assert reach1.qbankfull == 150.0
        assert reach1.qmin == 1.0
        assert reach1.qfit == (10.0, 20.0)
        assert reach1.qlevels == (100.0, 200.0, 300.0, 400.0)
        assert reach1.dq == (5.0, 15.0)
        
        branch2 = rivers.branches[1]
        assert branch2.name == 'Branch2'
        assert branch2.qlocation == 'L2'
        
        reach2 = branch2.reaches[0]
        assert isinstance(reach2, ReachLegacy)
        assert reach2.name == 'Branch2 R1'
        assert reach2.normal_width == 250.0
        assert reach2.ucritical == 0.3
        assert reach2.qstagnant == 0.0
        
        assert reach2.proprate_high == 3.65
        assert reach2.proprate_low == 0.8
        assert reach2.qbankfull == 2500.0
        assert reach2.qmin == 1.0
        assert reach2.qfit == (800.0, 1280.0)
        assert reach2.qlevels == (1000.0, 2000.0, 3000.0, 4000.0)
        assert reach2.dq == (1000.0, 1000.0)

        reach3 = branch2.reaches[1]
        assert isinstance(reach3, ReachLegacy)
        assert reach3.name == 'Branch2 R2'
        assert reach3.normal_width == 100.0
        assert reach3.ucritical == 0.3
        assert reach3.qstagnant == 1500.0
        
        assert reach3.proprate_high == 3.65
        assert reach3.proprate_low == 0.9
        assert reach3.qbankfull == 2500.0
        assert reach3.qmin == 1.0
        assert reach3.qfit == (800.0, 1280.0)
        assert reach3.qlevels == (1000.0, 2000.0, 3000.0, 4000.0)
        assert reach3.dq == (1000.0, 1000.0)

        assert rivers.version.major == 1
        assert rivers.version.minor == 0
    
    def given_a_legacy_rivers_config_file_with_no_version_when_read_rivers_then_exception_thrown(self):
        """
        Testing read rivers with legacy file but no version number raising an Exception.
        """        
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_rivers_test_no_version.ini")
        assert str(cm.value) == 'No version information in the file tests/files/read_rivers_test_no_version.ini!'

    def given_a_legacy_rivers_config_file_with_wrong_version_when_read_rivers_then_exception_thrown(self):
        """
        Testing read rivers raising an Exception.
        """        
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_rivers_test_wrong_version.ini")
        assert str(cm.value) == 'Unsupported version number 0.0 in the file tests/files/read_rivers_test_wrong_version.ini!'

class Test_read_rivers():    
    def given_a_rivers_config_file_when_read_rivers_then_version_number_is_correct(self):
        """
        Testing version is correct in rivers configuration file
        """
        print("current work directory: ", os.getcwd())
        rivers = RiversObject("tests/files/read_rivers_test_2_0_version.ini")
        assert rivers.version.major == 2
        assert rivers.version.minor == 0
    
    def given_a_rivers_config_file_when_read_rivers_then_data_loaded_in_RiverObject(self):
        """
        Testing read_rivers with data
        """
        print("current work directory: ", os.getcwd())
        rivers = RiversObject("tests/files/read_riversv2_test.ini")

        branch1 = rivers.branches[0]
        assert branch1.name == 'Branch1'
        assert branch1.qlocation == 'L1'
        
        reach1 = branch1.reaches[0]
        assert isinstance(reach1, Reach)
        assert reach1.name == 'Branch1 R1'
        assert reach1.normal_width == 250.0
        assert reach1.ucritical == 0.3
        assert reach1.qstagnant == 50.0
        
        assert reach1.qfit == (10.0, 20.0)
        assert not reach1.autotime 
        assert reach1.celer_form == 2
        assert isinstance(reach1.celer_object, CelerDischarge)
        assert reach1.celer_object.cdisch == (11.0, 21.0)
        
        assert reach1.hydro_q == ()
        assert reach1.hydro_t == ()
        assert reach1.tide
        assert reach1.tide_bc == ()
        
        branch2 = rivers.branches[1]
        assert branch2.name == 'Branch2'
        assert branch2.qlocation == 'L2'
        
        reach2 = branch2.reaches[0]
        assert isinstance(reach2, Reach)
        assert reach2.name == 'Branch2 R1'
        assert reach2.normal_width == 250.0
        assert reach2.ucritical == 0.3
        assert reach2.qstagnant == 0.0
        
        assert reach2.qfit == (800.0, 1280.0)
        assert not reach2.autotime
        assert reach2.celer_form == 2
        assert isinstance(reach2.celer_object, CelerDischarge)
        assert reach2.celer_object.cdisch == (11.0, 21.0)
        assert reach2.hydro_q == ()
        assert reach2.hydro_t == ()
        assert reach2.tide
        assert reach2.tide_bc == ()

        reach3 = branch2.reaches[1]
        assert isinstance(reach3, Reach)
        assert reach3.name == 'Branch2 R2'
        assert reach3.normal_width == 100.0
        assert reach3.ucritical == 0.3
        assert reach3.qstagnant == 1500.0
        
        assert reach3.qfit == (800.0, 1280.0)
        assert not reach3.autotime
        assert reach3.celer_form == 2
        assert isinstance(reach3.celer_object, CelerDischarge)
        assert reach3.celer_object.cdisch == (11.0, 21.0)
        assert reach3.hydro_q == ()
        assert reach3.hydro_t == ()
        assert reach3.tide
        assert reach3.tide_bc == ()
        
        assert rivers.version.major == 2
        assert rivers.version.minor == 0
    
    def given_a_rivers_config_file_with_defaults_loaded_because_not_in_file_when_read_rivers_then_throw_exception_of_failing_Celery_discharge_values(self):
        """
        Testing read_rivers, all defaults results in failing CeleryQ
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_CelerQ.ini") 
        assert str(cm.value) == 'The parameter "CelerQ" must be specified for branch "Branch1", reach "Branch1 R1" since "CelerForm" is set to 2.'
        
    def given_a_rivers_config_file_with_autotime_set_but_no_qfit_values_when_read_rivers_then_throw_exception_of_missing_Qfit_values(self):
        """
        Testing read_rivers, setting AutoTime true expects QFit to be set
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_HydroQ.ini") 
        assert str(cm.value) == 'The parameter "QFit" must be specified for branch "Branch1", reach "Branch1 R1" since "AutoTime" is set to True.'
    
    def given_a_rivers_config_file_with_autotime_unset_but_no_consistency_between_hydroq_and_hydrot_values_when_read_rivers_then_throw_exception_of_invalid_value_size_of_hydrot_and_hydroq_values(self):
        """
        Testing read_rivers2, with setting AutoTime false expects HydroT to be set with same consistency as HydroQ
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_HydroT.ini") 
        assert str(cm.value) == 'Length of "HydroQ" and "HydroT" for branch "Branch1", reach "Branch1 R1" are not consistent: 2 and 1 values read respectively.'
    
    def given_a_rivers_config_file_with_autotime_unset_and_tide_set_but_no_consistency_between_hydroq_and_tidebc_values_when_read_rivers_then_throw_exception_of_invalid_value_size_of_hydroq_and_tidebc_values(self):
        """
        Testing read_rivers2, with setting AutoTime false & Tide true expects HydroQ to be set with same consistency as TideBC 
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_TideBC.ini") 
        assert str(cm.value) == 'Length of "HydroQ" and "TideBC" for branch "Branch1", reach "Branch1 R1" are not consistent: 2 and 1 values read respectively.'
    
    def given_a_rivers_config_file_with_autotime_unset_and_cellery_form_is_1_but_no_consistency_between_propq_and_propc_values_when_read_rivers_then_throw_exception_of_invalid_value_size_of_propq_and_propc_values(self):
        """
        Testing read_rivers2, with setting AutoTime false & Cform 1 expects PropQ to be set with same consistency as PropC
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_cform.ini") 
        assert str(cm.value) == 'Length of "PropQ" and "PropC" for branch "Branch1", reach "Branch1 R1" are not consistent: 2 and 1 values read respectively.'
    
    def given_a_rivers_config_file_with_autotime_unset_and_cellery_form_is_1_but_no_default_for_propq_and_propc_values_when_read_rivers_then_throw_exception_of_invalid_value_of_propq_and_propc_values(self):
        """
        Testing read_rivers2, with setting AutoTime false & Cform 1 expects PropQ and PropC to be set 
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_noPropQC.ini") 
        assert str(cm.value) == 'The parameters "PropQ" and "PropC" must be specified for branch "Branch1", reach "Branch1 R1" since "CelerForm" is set to 1.'
    
    def given_a_rivers_config_file_with_autotime_unset_and_cellery_form_is_invalid_when_read_rivers_then_throw_exception_of_invalid_value_of_celerform(self):
        """
        Testing read_rivers2, with setting AutoTime false & Cform 8 exception as this is unsupported
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_wrongcform.ini") 
        assert str(cm.value) == 'Invalid value 8 specified for "CelerForm" for branch "Branch1", reach "Branch1 R1"; only 1 and 2 are supported.'
