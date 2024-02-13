import os
import sys
from contextlib import contextmanager
from io import StringIO
import pytest

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


class Test_read_rivers():
    def test_read_rivers_01(self):
        """
        Testing read_rivers, collect_values1, collect_values2 and collect_values4.
        """
        print("current work directory: ", os.getcwd())       
        
        rivers = RiversObject("tests/files/read_rivers_test.ini")
        
        assert rivers.branches == ['Branch1', 'Branch2']
        assert rivers.allreaches == [['Branch1 R1'], ['Branch2 R1', 'Branch2 R2']]
        assert rivers.qlocations == ['L1', 'L2']
        assert rivers.proprate_high == [[3.14], [3.65, 3.65]]
        assert rivers.proprate_low == [[0.8], [0.8, 0.9]]
        assert rivers.normal_width == [[250.0], [250.0, 100.0]]
        assert rivers.ucritical == [[0.3], [0.3, 0.3]]
        assert rivers.qbankfull == [[150.0], [2500.0, 2500.0]]
        assert rivers.qstagnant == [[50.0], [0.0, 1500.0]]
        assert rivers.qmin == [[1.0], [1.0, 1.0]]
        assert rivers.qfit == [[(10.0, 20.0)], [(800.0, 1280.0), (800.0, 1280.0)]]
        assert rivers.qlevels == [[(100.0, 200.0, 300.0, 400.0)], [(1000.0, 2000.0, 3000.0, 4000.0), (1000.0, 2000.0, 3000.0, 4000.0)]]
        assert rivers.dq == [[(5.0, 15.0)], [(1000.0, 1000.0), (1000.0, 1000.0)]]
        assert rivers.version.major == 1
        assert rivers.version.minor == 0
    
    def test_read_rivers_02(self):
        """
        Testing read rivers raising an Exception.
        """        
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_rivers_test_no_version.ini")
        assert str(cm.value) == 'No version information in the file tests/files/read_rivers_test_no_version.ini!'

    def test_read_rivers_03(self):
        """
        Testing read rivers raising an Exception.
        """        
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_rivers_test_wrong_version.ini")
        assert str(cm.value) == 'Unsupported version number 0.0 in the file tests/files/read_rivers_test_wrong_version.ini!'

class Test_read_rivers2():    
    def test_read_rivers2_01(self):
        """
        Testing version
        """
        print("current work directory: ", os.getcwd())
        rivers = RiversObject("tests/files/read_rivers_test_2_0_version.ini")
        assert rivers.version == '2.0'
    
    def test_read_rivers2_02(self):
        """
        Testing read_rivers2, collect_values1, collect_values2 and collect_values4.
        """
        print("current work directory: ", os.getcwd())
        rivers = RiversObject("tests/files/read_riversv2_test.ini")
        assert rivers.branches == ['Branch1', 'Branch2']
        assert rivers.allreaches == [['Branch1 R1'], ['Branch2 R1', 'Branch2 R2']]
        assert rivers.qlocations == ['L1', 'L2']
        assert rivers.normal_width == [[250.0], [250.0, 100.0]]
        assert rivers.ucritical == [[0.3], [0.3, 0.3]]
        assert rivers.qstagnant == [[50.0], [0.0, 1500.0]]
        assert rivers.qfit == [[(10.0, 20.0)], [(800.0, 1280.0), (800.0, 1280.0)]]
        
        assert rivers.version.major == 2
        assert rivers.version.minor == 0
        
        assert rivers.autotime == [[False], [False, False]]
        assert rivers.cdisch == [[(11.0, 21.0)], [(11.0, 21.0), (11.0, 21.0)]]
        assert rivers.cform == [[2], [2, 2]]
        assert rivers.hydro_q == [[()], [(), ()]]
        assert rivers.hydro_t == [[()], [(), ()]]
        assert rivers.prop_c == [[()], [(), ()]]
        assert rivers.prop_q == [[()], [(), ()]]
        assert rivers.tide == [[True], [True, True]]
        assert rivers.tide_bc == [[()], [(), ()]]
        
    
    def test_read_rivers2_03(self):
        """
        Testing read_rivers2, all defaults results in failing CeleryQ
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_CelerQ.ini") 
        assert str(cm.value) == 'The parameter "CelerQ" must be specified for branch "Branch1", reach "Branch1 R1" since "CelerForm" is set to 2.'
        
    def test_read_rivers2_04(self):
        """
        Testing read_rivers2, setting AutoTime true expects QFit to be set
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_HydroQ.ini") 
        assert str(cm.value) == 'The parameter "QFit" must be specified for branch "Branch1", reach "Branch1 R1" since "AutoTime" is set to True.'
    
    def test_read_rivers2_05(self):
        """
        Testing read_rivers2, with setting AutoTime false expects HydroT to be set with same consistency as HydroQ
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_HydroT.ini") 
        assert str(cm.value) == 'Length of "HydroQ" and "HydroT" for branch "Branch1", reach "Branch1 R1" are not consistent: 2 and 1 values read respectively.'
    
    def test_read_rivers2_06(self):
        """
        Testing read_rivers2, with setting AutoTime false & Tide true expects HydroQ to be set with same consistency as TideBC 
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_TideBC.ini") 
        assert str(cm.value) == 'Length of "HydroQ" and "TideBC" for branch "Branch1", reach "Branch1 R1" are not consistent: 2 and 1 values read respectively.'
    
    def test_read_rivers2_07(self):
        """
        Testing read_rivers2, with setting AutoTime false & Cform 1 expects PropQ to be set with same consistency as PropC
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_cform.ini") 
        assert str(cm.value) == 'Length of "PropQ" and "PropC" for branch "Branch1", reach "Branch1 R1" are not consistent: 2 and 1 values read respectively.'
    
    def test_read_rivers2_08(self):
        """
        Testing read_rivers2, with setting AutoTime false & Cform 1 expects PropQ and PropC to be set 
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_noPropQC.ini") 
        assert str(cm.value) == 'The parameters "PropQ" and "PropC" must be specified for branch "Branch1", reach "Branch1 R1" since "CelerForm" is set to 1.'
    
    def test_read_rivers2_09(self):
        """
        Testing read_rivers2, with setting AutoTime false & Cform 1 expects PropQ and PropC to be set 
        """
        with pytest.raises(Exception) as cm:
            RiversObject("tests/files/read_riversv2_test_failing_wrongcform.ini") 
        assert str(cm.value) == 'Invalid value 8 specified for "CelerForm" for branch "Branch1", reach "Branch1 R1"; only 1 and 2 are supported.'
