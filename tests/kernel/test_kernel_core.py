import dfastmi.kernel.core
import numpy
import pytest

class Test_dzq_from_du_and_h():
    def test_given_situations_resulting_in_valid_values_when_dzq_from_du_and_h_then_all_values_returned_are_expected_values(self):
        u0  = numpy.array([0.5,  1.0, 1.0, 1.0,  0.5])
        h0  = numpy.array([1.0,  4.0, 1.0, 2.0,  1.0])
        u1  = numpy.array([0.5,  0.5, 0.5, 0.5,  1.0])
        ucrit = 0.3
        
        dzq = numpy.array([0.0, 2.0, 0.5, 1.0,  -1.0])
        dzqc = dfastmi.kernel.core.dzq_from_du_and_h(u0, h0, u1, ucrit)
        assert (dzqc == dzq).all()

    def test_given_situations_resulting_in_nans_when_dzq_from_du_and_h_then_all_values_returned_are_nan(self):
        u0  = numpy.array([ 0.5, 0.2, 0.5, 120.0])
        h0  = numpy.array([ 1.0, 1.0, 1.0,   1.0])
        u1  = numpy.array([-0.5, 0.5, 0.2,   0.5])
        ucrit = 0.3

        dzqc = dfastmi.kernel.core.dzq_from_du_and_h(u0, h0, u1, ucrit)
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
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.core.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert (abs(zmin - zminc) < 1e-13).all()
        
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
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.core.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert (abs(zmin - zminc) < 1e-13).all()
        
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
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.core.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert (abs(zmin - zminc) < 1e-13).all()
        
        assert ((abs(zdzb[0]-dzb[0])) < 1e-13).all()
        assert ((abs(zdzb[1]-dzb[1])) < 1e-13).all()
        assert ((abs(zdzb[2]-dzb[2])) < 1e-13).all()
        
    def test_given_stagnant_t_when_main_computation_then_expect_returned_values_are_in_range_of_expected_values(self):
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
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.core.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)    

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert (abs(zmin - zminc) < 1e-13).all()
        
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
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.core.main_computation([dzq1, dummy, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)   

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert (abs(zmin - zminc) < 1e-13).all()
        
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

        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.core.main_computation([dzq1, dzqS, dzq2, dzq3], T, rsigma)
        
        self.print_values_floatmode_unique(zgem, zgemc, zmax, zmaxc, zmin, zminc, zdzb, dzb)   

        assert (abs(zgemc - zgem) < 1e-13).all()
        assert (abs(zmax - zmaxc) < 1e-13).all()
        assert (abs(zmin - zminc) < 1e-13).all()
        
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

class Test_relax_factors_calculation():
    def test_given_single_value_for_calculation_when_relax_factors_then_return_rsigma_value_between_expected_values(self):
        Q = [2]
        T = [0.0005]
        q_stagnant = 1.0
        celerity = [1.0]
        nwidth = 1.0
        
        rsigma = dfastmi.kernel.core.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert 0.76<= rsigma[0] <= 0.78
        
    def test_given_multiple_values_for_calculation_when_relax_factors_then_return_rsigma_values_between_expected_values(self):
        Q = [2,2]
        T = [0.0005,1.0]
        q_stagnant = 1.0
        celerity = [1.0,0.0005]
        nwidth = 1.0
        
        rsigma = dfastmi.kernel.core.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert 0.76<= rsigma[0] <= 0.78
        assert 0.76<= rsigma[1] <= 0.78
        
    def test_given_multiple_values_for_calculation_with_different_width_when_relax_factors_then_return_rsigma_varying_values_between_expected_values(self):
        Q = [2,2]
        T = [0.0005,1.0]
        q_stagnant = 1.0
        celerity = [1.0,0.0005]
        nwidth = 5.0
        
        rsigma = dfastmi.kernel.core.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert 0.94<= rsigma[0] <= 0.96
        assert 0.94<= rsigma[0] <= 0.96
        
    def test_given_q_same_as_q_stagnant_when_relax_factors_then_return_rsigma_values_of_1(self):
        Q = [2,2,2,2] 
        T = [5,5,5,5] 
        q_stagnant = 2.0
        celerity = [5,5,5,5] 
        nwidth = 2.0
        
        rsigma = dfastmi.kernel.core.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert rsigma == (1.0, 1.0, 1.0, 1.0)
        
    def test_given_q_smaller_than_q_stagnant_when_relax_factors_then_return_rsigma_values_of_1(self):
        Q = [2,2,2,2] 
        T = [5,5,5,5] 
        q_stagnant = 3.0
        celerity = [5,5,5,5] 
        nwidth = 2.0
        
        rsigma = dfastmi.kernel.core.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert rsigma == (1.0, 1.0, 1.0, 1.0)
  
class Test_estimate_sedimentation_length():
        
    @pytest.mark.parametrize("tmi, celerity, expected_length", [
        ([2],[2],4000),
        ([2,2],[2,2],8000),
        ([2,2,2],[2,2,2],12000),
        ([2,2,2,2],[2,2,2,2],16000),
        ([2,2,2,2,2],[2,2,2,2,2],20000),
    ]) 
    def test_given_tmi_and_celerity_when_estimate_sedimentation_length_then_return_expected_length(self, tmi, celerity, expected_length):
        length = dfastmi.kernel.core.estimate_sedimentation_length(tmi,celerity)
        assert length == expected_length