import dfastmi.kernel
import numpy
import pytest

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
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (True, True, True))
        
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
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (False, True, True))

    @pytest.mark.parametrize("q_bankfull, expected_qruns", [
        (4000, (3500, 4500, 6000)), #Testing char_discharges for Qbf = 4000 and Qth = 3500.
        (6500, (3500, 6500, 6000)), #Testing char_discharges for Qbf = 6500 and Qth = 3500.
    ])
    def test_given_no_threshold_discharge_3500_with_qbankfull_variable_when_char_discharges_then_return_expected_qruns(self, q_bankfull, expected_qruns):
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 3500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (False, True, True))

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
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == (expected_qruns, (False, False, True))

class Test_char_times():
    
    def test_given_default_bovenrijn_conditions_when_char_times_then_return_expected_tstag_t_rsigma(self):
        q_fit = (800, 1280)
        q_stagnant = 800
        Q = (3000, 4000, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.89
        nwidth = 340

        result_tstag, result_T, result_rsigma = dfastmi.kernel.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth)
        
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

        result_tstag, result_T, result_rsigma = dfastmi.kernel.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth)
        
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
        
        result_tstag, result_T, result_rsigma = dfastmi.kernel.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth)
        
        assert result_tstag == 0.42124440138751573
        assert result_T == (0.39946547806236565, 0.09720512192621984, 0.08208499862389873)
        assert result_rsigma == (0.20232865227253677, 0.1696541246824568, 0.2235654146204697)

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
        
        result = int(dfastmi.kernel.estimate_sedimentation_length(rsigma, applyQ, nwidth))
        assert  result == expected_length
        
    @pytest.mark.parametrize("nwidth, expected_length", [
        (0, 0),
        (500, 2036),
        (2000, 8146),
    ])
    def test_given_varying_nwidth_when_estimate_sedimentation_length_then_return_expected_length_as_int(self, nwidth, expected_length):
        rsigma = (0.3415830625333821, 0.5934734581592429, 0.6436479901670012)
        applyQ = (True, True, True)
        
        result = int(dfastmi.kernel.estimate_sedimentation_length(rsigma, applyQ, nwidth))
        assert  result == expected_length

class Test_dzq_from_du_and_h():
    def test_given_situations_resulting_in_valid_values_when_dzq_from_du_and_h_then_all_values_returned_are_expected_values(self):
        u0  = numpy.array([0.5,  1.0, 1.0, 1.0,  0.5])
        h0  = numpy.array([1.0,  4.0, 1.0, 2.0,  1.0])
        u1  = numpy.array([0.5,  0.5, 0.5, 0.5,  1.0])
        ucrit = 0.3
        
        dzq = numpy.array([0.0, 2.0, 0.5, 1.0,  -1.0])
        dzqc = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
        assert (dzqc == dzq).all()

    def test_given_situations_resulting_in_nans_when_dzq_from_du_and_h_then_all_values_returned_are_nan(self):
        u0  = numpy.array([ 0.5, 0.2, 0.5, 120.0])
        h0  = numpy.array([ 1.0, 1.0, 1.0,   1.0])
        u1  = numpy.array([-0.5, 0.5, 0.2,   0.5])
        ucrit = 0.3

        dzqc = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
        assert numpy.isnan(dzqc).all()
   
class Test_main_computation():
    def test_given_varying_values_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, 1.0])
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        T = (0.5, 0.25, 0.25)
        rsigma = (0.1, 0.2, 0.4)
        
        zgem = numpy.array([0.25252016129032256, 0.5871975806451613, 0.5871975806451613, 1., 1.])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 1.])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., 1.])
        
        zdzb = [numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 1.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 1.]),
                numpy.array([0.012096774193548387, 0.8185483870967742, 0.8185483870967742, 1., 1.])]
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert ((zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()
        
    def test_given_one_miss_value_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
        mis = numpy.NaN
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, mis])
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        T = (0.5, 0.25, 0.25)
        rsigma = (0.1, 0.2, 0.4)
        
        zgem = numpy.array([0.25252016129032256, 0.5871975806451613, 0.5871975806451613, 1., .0])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., .0])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., .0])
        
        zdzb = [numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 0.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 0.]),
                numpy.array([0.012096774193548387, 0.8185483870967742, 0.8185483870967742, 1., 0.])]
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert ((zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()
        
    def test_given_one_miss_value_stagnant_t_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
        mis = numpy.NaN
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, mis])
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        t_stagnant = 0.25
        T = (t_stagnant, t_stagnant, t_stagnant, t_stagnant)
        rsigma = (0.1, 0.2, 0.4)
        
        zgem = numpy.array([0.1693548387096774, 0.45967741935483875, 0.45967741935483875, .75, 0.])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1.0000000000000002, 0.])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., 0.])
        
        zdzb = [numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 0.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 0.]),
                numpy.array([0.012096774193548387, 0.8185483870967742, 0.8185483870967742, 1., 0.])]
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert ((zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()
        
    def test_given_stagnant_t_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
        """
        Testing main_computation.
        """
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, 1.0])
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        t_stagnant = 0.25
        T = (t_stagnant, t_stagnant, t_stagnant, t_stagnant)
        rsigma = (0.1, 1, 0.2, 0.4)
        
        zgem = numpy.array([0.24489795918367346, 0.24489795918367346, 0.24489795918367346, 0.75, 0.75])
        zmax = numpy.array([0.8163265306122449, 0.8163265306122449, 0.8163265306122449, 1., 1.])
        zmin = numpy.array([0.08163265306122451,0.08163265306122451, 0.08163265306122451, 1., 1.])
        
        zdzb = [numpy.array([0.8163265306122449, 0.8163265306122449, 0.8163265306122449, 1., 1.]),
                numpy.array([0.08163265306122451, 0.08163265306122451, 0.08163265306122451, 1., 1.]),
                numpy.array([0.08163265306122451, 0.08163265306122451, 0.08163265306122451, 1., 1.])]
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)    

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert ((zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()
        
    def test_given_dummy_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, 1.0])
        dummy = numpy.array([-1.0, -1.0, -1.0, -1.0, -1.0]) 
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])

        T = (0.5, 0.25, 0.25, 0.25)
        rsigma = (0.1, 1, 0.2, 0.4)
        
        zgem = numpy.array([0.26764112903225806, 0.610383064516129 ,0.610383064516129, 1.25, 1.25])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1.0000000000000002, 1.0000000000000002])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., 1.])
        
        zdzb = [numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 1.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 1.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 1.])]
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dummy, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)   

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert ((zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()
        
    def test_given_stagnant_t_one_miss_value_one_dummy_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
        mis = numpy.NaN
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, mis])
        dzqS = numpy.array([-1.0, -1.0, -1.0, -1.0, -1.0]) # dummy
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        t_stagnant = 0.25
        T = (t_stagnant, t_stagnant, t_stagnant, t_stagnant)
        rsigma = (0.1, 1, 0.2, 0.4)
        
        zgem = numpy.array([0.1844758064516129, 0.4828629032258065, 0.4828629032258065, 1., 0.])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 0.])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., 0.])
        
        zdzb = [numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 0.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 0.]),
                numpy.array([0.06048387096774193, 0.09274193548387097, 0.09274193548387097, 1., 0.])]

        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzqS, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)   

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert ((zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()        
        
    def print_values_floatmode_unique(self, zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb):
        """
        Helper method to print the reference and computed values with their respective unique precision.
        """
        print("zdzb 0 reference: ", numpy.array2string(zdzb[0], floatmode = 'unique'))
        print("dzb 0 computed  : ", numpy.array2string(dzb[0], floatmode = 'unique'))
        print("zdzb 1 reference: ", numpy.array2string(zdzb[1], floatmode = 'unique'))
        print("dzb 1 computed  : ", numpy.array2string(dzb[1], floatmode = 'unique'))
        print("zdzb 2 reference: ", numpy.array2string(zdzb[2], floatmode = 'unique'))
        print("dzb 2 computed  : ", numpy.array2string(dzb[2], floatmode = 'unique'))
        
        print("zgem reference  : ", numpy.array2string(zgem, floatmode = 'unique'))
        print("zgem computed   : ", numpy.array2string(zgemc, floatmode = 'unique'))
        print("zmax reference  : ", numpy.array2string(zmax, floatmode = 'unique'))
        print("zmax computed   : ", numpy.array2string(zmaxc, floatmode = 'unique'))
        print("zmin reference  : ", numpy.array2string(zmin, floatmode = 'unique'))
        print("zmin computed   : ", numpy.array2string(zminc, floatmode = 'unique'))

if __name__ == '__main__':
    unittest.main()