import pytest
import dfastmi.kernel.legacy


class Test_char_discharges():
    
    @pytest.mark.parametrize("q_bankfull, expected_qruns", [
        (4000, (3000, 4000, 6000)), #Testing char_discharges for Qbf = 4000 (default) - no threshold (Qmin = 1000).
        (3500, (3000, 4000, 6000)), #Testing char_discharges for Qbf < 4000 - no threshold. If q_bankfull < q_lvl[1]: no change in the results.
        (4500, (3000, 4500, 6000)), #Testing char_discharges for 4000 < Qbf < 6000 - no threshold. If q_lvl[1] < q_bankfull < q_lvl[2]: returned discharge[1] is adjusted.
        (6500, (3000, 4000, 6500)), #Testing char_discharges for Qbf > 6000 - no threshold. If q_lvl[2] < q_bankfull: returned discharge[2] is adjusted.
    ])
    def test_given_no_threshold_discharge_with_qbankfull_variable_when_char_discharges_then_return_expected_qruns(self, q_bankfull, expected_qruns):
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = None
        assert dfastmi.kernel.legacy.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (True, True, True))
        
    @pytest.mark.parametrize("q_bankfull, expected_qruns", [
        (2000, (1500, 2500, 6000)), #Testing char_discharges for Qbf = 2000 and Qth = 1500.
        (3500, (1500, 3500, 6000)), #Testing char_discharges for Qbf = 3500 and Qth = 1500.
        (5500, (1500, 5500, 6500)), #Testing char_discharges for Qbf = 5500 and Qth = 1500.
        (6500, (1500, 4000, 6500)), #Testing char_discharges for Qbf = 6500 and Qth = 1500.
    ])
    
    def test_given_no_threshold_discharge_1500_with_qbankfull_variable_when_char_discharges_then_return_expected_qruns(self, q_bankfull, expected_qruns):
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 1500
        assert dfastmi.kernel.legacy.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (False, True, True))

    @pytest.mark.parametrize("q_bankfull, expected_qruns", [
        (4000, (3500, 4500, 6000)), #Testing char_discharges for Qbf = 4000 and Qth = 3500.
        (6500, (3500, 6500, 6000)), #Testing char_discharges for Qbf = 6500 and Qth = 3500.
    ])
    def test_given_no_threshold_discharge_3500_with_qbankfull_variable_when_char_discharges_then_return_expected_qruns(self, q_bankfull, expected_qruns):
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 3500
        assert dfastmi.kernel.legacy.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (False, True, True))

    @pytest.mark.parametrize("q_threshold, expected_qruns", [
        (4500, (4500, None, 6000)), #Testing char_discharges for Qth = 4500.
        (5500, (5500, None, 6500)), #Testing char_discharges for Qth = 5500.
        (6500, (6500, None, 7500)), #Testing char_discharges for Qth = 6500.
        (9500, (9500, None, 10000)), #Testing char_discharges for Qth = 9500.
    ])
    def test_given_qbankfull_very_large_with_qthreshold_variable_when_char_discharges_then_return_expected_qruns(self, q_threshold, expected_qruns):
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_bankfull = 999999999999
        assert dfastmi.kernel.legacy.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (False, False, True))

class Test_char_times():
    
    def test_given_default_bovenrijn_conditions_when_char_times_then_return_expected_tstag_t_rsigma(self):
        q_fit = (800, 1280)
        q_stagnant = 800
        Q = (3000, 4000, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.89
        nwidth = 340

        result_tstag, result_T, result_rsigma = dfastmi.kernel.legacy.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth)
        
        assert result_tstag == 0.0
        assert result_T == (0.8207098794498814, 0.09720512192621984, 0.08208499862389877)
        assert result_rsigma == (0.3415830625333821, 0.5934734581592429, 0.6436479901670012)
        
    def test_given_adjusted_q_bovenrijn_conditions_when_char_times_then_return_expected_tstag_t_rsigma(self):   
        q_fit = (800, 1280)
        q_stagnant = 800
        Q = (4500, None, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.89
        nwidth = 340

        result_tstag, result_T, result_rsigma = dfastmi.kernel.legacy.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth)
        
        assert result_tstag == 0.0
        assert result_T == (0.9444585116689311, 0.0, 0.05554148833106887)
        assert result_rsigma == (0.29050644338024023, 1.0, 0.7422069944312727)

    def test_given_default_nederrijn_stuwpad_driel_conditions_when_char_times_then_return_expected_tstag_t_rsigma(self):       
        q_fit = (800, 1280)
        q_stagnant = 1500
        Q = (3000, 4000, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.80
        nwidth = 100
        
        result_tstag, result_T, result_rsigma = dfastmi.kernel.legacy.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth)
        
        assert result_tstag == 0.42124440138751573
        assert result_T == (0.39946547806236565, 0.09720512192621984, 0.08208499862389873)
        assert result_rsigma == (0.20232865227253677, 0.1696541246824568, 0.2235654146204697)