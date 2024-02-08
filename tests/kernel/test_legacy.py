import dfastmi.kernel.legacy
import pytest

class Test_estimate_sedimentation_length():        
    @pytest.mark.parametrize("applyQ, expected_length", [
        ((True, True, True), 1384),
        ((False, False, False),0),
        ((True, False, False),730),
        ((False, True, False),354),
        ((True, True, False),1085),
        ((False, True, True),654),
        ((False, False, True),299),
    ])
    def test_given_varying_applyq_when_estimate_sedimentation_length_then_return_expected_length_as_int(self, applyQ, expected_length):
        rsigma = (0.3415830625333821, 0.5934734581592429, 0.6436479901670012)
        nwidth = 340
        
        result = int(dfastmi.kernel.legacy.estimate_sedimentation_length(rsigma, applyQ, nwidth))
        assert  result == expected_length
        
    @pytest.mark.parametrize("nwidth, expected_length", [
        (0, 0),
        (500, 2036),
        (2000, 8146),
    ])
    def test_given_varying_nwidth_when_estimate_sedimentation_length_then_return_expected_length_as_int(self, nwidth, expected_length):
        rsigma = (0.3415830625333821, 0.5934734581592429, 0.6436479901670012)
        applyQ = (True, True, True)
        
        result = int(dfastmi.kernel.legacy.estimate_sedimentation_length(rsigma, applyQ, nwidth))
        assert  result == expected_length