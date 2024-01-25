import context
import dfastmi.kernel
import numpy

class Test_char_discharges():
    def test_char_discharges_01(self):
        """
        Testing char_discharges for Qbf = 4000 (default) - no threshold (Qmin = 1000).
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = None
        q_bankfull = 4000
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((3000, 4000, 6000), (True, True, True))

    def test_char_discharges_02(self):
        """
        Testing char_discharges for Qbf < 4000 - no threshold.
        If q_bankfull < q_lvl[1]: no change in the results.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = None
        q_bankfull = 3500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((3000, 4000, 6000), (True, True, True))

    def test_char_discharges_03(self):
        """
        Testing char_discharges for 4000 < Qbf < 6000 - no threshold.
        If q_lvl[1] < q_bankfull < q_lvl[2]: returned discharge[1] is adjusted.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = None
        q_bankfull = 4500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((3000, 4500, 6000), (True, True, True))

    def test_char_discharges_04(self):
        """
        Testing char_discharges for Qbf > 6000 - no threshold.
        If q_lvl[2] < q_bankfull: returned discharge[2] is adjusted.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = None
        q_bankfull = 6500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((3000, 4000, 6500), (True, True, True))

    def test_char_discharges_05(self):
        """
        Testing char_discharges for Qbf = 3500 and Qth = 1500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 1500
        q_bankfull = 3500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((1500, 3500, 6000), (False, True, True))

    def test_char_discharges_06(self):
        """
        Testing char_discharges for Qbf = 2000 and Qth = 1500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 1500
        q_bankfull = 2000
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((1500, 2500, 6000), (False, True, True))

    def test_char_discharges_07(self):
        """
        Testing char_discharges for Qbf = 5500 and Qth = 1500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 1500
        q_bankfull = 5500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((1500, 5500, 6500), (False, True, True))

    def test_char_discharges_08(self):
        """
        Testing char_discharges for Qbf = 6500 and Qth = 1500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 1500
        q_bankfull = 6500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((1500, 4000, 6500), (False, True, True))

    def test_char_discharges_09(self):
        """
        Testing char_discharges for Qbf = 4000 and Qth = 3500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 3500
        q_bankfull = 4000
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((3500, 4500, 6000), (False, True, True))

    def test_char_discharges_10(self):
        """
        Testing char_discharges for Qbf = 6500 and Qth = 3500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 3500
        q_bankfull = 6500
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((3500, 6500, 6000), (False, True, True))

    def test_char_discharges_11(self):
        """
        Testing char_discharges for Qth = 4500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 4500
        q_bankfull = 999999999999
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((4500, None, 6000), (False, False, True))

    def test_char_discharges_12(self):
        """
        Testing char_discharges for Qth = 5500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 5500
        q_bankfull = 999999999999
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((5500, None, 6500), (False, False, True))

    def test_char_discharges_13(self):
        """
        Testing char_discharges for Qth = 6500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 6500
        q_bankfull = 999999999999
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((6500, None, 7500), (False, False, True))

    def test_char_discharges_13(self):
        """
        Testing char_discharges for Qth = 9500.
        """
        q_lvl = (3000, 4000, 6000, 10000)
        dq = (1000, 1000)
        q_threshold = 9500
        q_bankfull = 999999999999
        assert dfastmi.kernel.char_discharges(q_lvl, dq, q_threshold, q_bankfull) == ((9500, None, 10000), (False, False, True))

class Test_char_times():
    def test_char_times_01(self):
        """
        Testing char_times for default Bovenrijn conditions.
        """
        q_fit = (800, 1280)
        q_stagnant = 800
        Q = (3000, 4000, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.89
        nwidth = 340
        tstag = 0.0
        T = (0.8207098794498814, 0.09720512192621984, 0.08208499862389877)
        rsigma = (0.3415830625333821, 0.5934734581592429, 0.6436479901670012)
        assert dfastmi.kernel.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth) == (tstag, T, rsigma)

    def test_char_times_02(self):
        """
        Testing char_times for default Nederrijn stuwpand Driel conditions.
        """
        q_fit = (800, 1280)
        q_stagnant = 1500
        Q = (3000, 4000, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.80
        nwidth = 100
        tstag = 0.42124440138751573
        T = (0.39946547806236565, 0.09720512192621984, 0.08208499862389873)
        rsigma = (0.20232865227253677, 0.1696541246824568, 0.2235654146204697)
        assert dfastmi.kernel.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth) == (tstag, T, rsigma)

    def test_char_times_03(self):
        """
        Testing char_times for adjusted Bovenrijn conditions.
        """
        q_fit = (800, 1280)
        q_stagnant = 800
        Q = (4500, None, 6000)
        celerity_hg = 3.65
        celerity_lw = 0.89
        nwidth = 340
        tstag = 0.0
        T = (0.9444585116689311, 0.0, 0.05554148833106887)
        rsigma = (0.29050644338024023, 1.0, 0.7422069944312727)
        assert dfastmi.kernel.char_times(q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth) == (tstag, T, rsigma)

class Test_estimate_sedimentation_length():
    def test_estimate_sedimentation_length_01(self):
        """
        Testing char_times for default Bovenrijn conditions.
        """
        rsigma = (0.3415830625333821, 0.5934734581592429, 0.6436479901670012)
        applyQ = (True, True, True)
        nwidth = 340
        L = 1384
        assert int(dfastmi.kernel.estimate_sedimentation_length(rsigma, applyQ, nwidth)) == L

class Test_dzq_from_du_and_h():
    def test_dzq_from_du_and_h_01(self):
        """
        Testing dzq_from_du_and_h for situations not resulting in NaN.
        """
        u0  = numpy.array([0.5,  1.0, 1.0, 1.0,  0.5])
        h0  = numpy.array([1.0,  4.0, 1.0, 2.0,  1.0])
        u1  = numpy.array([0.5,  0.5, 0.5, 0.5,  1.0])
        ucrit = 0.3
        dzq = numpy.array([0.0, 2.0, 0.5, 1.0,  -1.0])
        dzqc = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
        print("dzq reference: ", dzq)
        print("dzq computed : ",dzqc)
        assert (dzqc == dzq).all() == True

    def test_dzq_from_du_and_h_02(self):
        """
        Testing dzq_from_du_and_h for situations resulting in NaN.
        """
        u0  = numpy.array([ 0.5, 0.2, 0.5, 120.0])
        h0  = numpy.array([ 1.0, 1.0, 1.0,   1.0])
        u1  = numpy.array([-0.5, 0.5, 0.2,   0.5])
        ucrit = 0.3
        # dzq = all NaN
        dzqc = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
        print("dzq computed : ",dzqc)
        assert numpy.isnan(dzqc).all() == True
   
class Test_main_computation():
    def test_main_computation_01(self):
        """
        Testing main_computation.
        """
        mis = numpy.NaN
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, mis])
        dzqS = numpy.array([-1.0, -1.0, -1.0, -1.0, -1.0]) # dummy
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        t_stagnant = 0.25
        T = (0.25, t_stagnant, 0.25, 0.25)
        rsigma = (0.1, 1, 0.2, 0.4)

        zgem = numpy.array([0.1844758064516129, 0.4828629032258065, 0.4828629032258065, 1., 0.])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 0.])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., 0.])

        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzqS, dzq2, dzq3], T, rsigma)

        print("zgem reference: ", numpy.array2string(zgem, floatmode = 'unique'))
        print("zgem computed : ", numpy.array2string(zgemc, floatmode = 'unique'))
        print("zmax reference: ", numpy.array2string(zmax, floatmode = 'unique'))
        print("zmax computed : ", numpy.array2string(zmaxc, floatmode = 'unique'))
        print("zmin reference: ", numpy.array2string(zmin, floatmode = 'unique'))
        print("zmin computed : ", numpy.array2string(zminc, floatmode = 'unique'))

        assert (abs(zgemc - zgem) < 1e-13).all() and (abs(zmax - zmaxc) < 1e-13).all() and ((zmin - zminc) < 1e-13).all() == True

    def test_main_computation_02(self):
        """
        Testing main_computation without stagnant period.
        """
        mis = numpy.NaN
        dzq1 = numpy.array([0.0, 0.0, 0.0, 1.0, mis])
        dzq2 = numpy.array([0.0, 1.0, 1.0, 1.0, 1.0])
        dzq3 = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0])
        t_stagnant = 0.0
        T = (0.5, 0.25, 0.25)
        rsigma = (0.1, 0.2, 0.4)
        
        zgem = numpy.array([0.25252016129032256, 0.5871975806451613, 0.5871975806451613, 1., 0.])
        zmax = numpy.array([0.6048387096774194, 0.9274193548387097, 0.9274193548387097, 1., 0.])
        zmin = numpy.array([0.012096774193548387, 0.09274193548387097, 0.09274193548387097, 1., 0.])
        
        zgemc, zmaxc, zminc, dzb = dfastmi.kernel.main_computation([dzq1, dzq2, dzq3], T, rsigma)
        
        print("zgem reference: ", numpy.array2string(zgem, floatmode = 'unique'))
        print("zgem computed : ", numpy.array2string(zgemc, floatmode = 'unique'))
        print("zmax reference: ", numpy.array2string(zmax, floatmode = 'unique'))
        print("zmax computed : ", numpy.array2string(zmaxc, floatmode = 'unique'))
        print("zmin reference: ", numpy.array2string(zmin, floatmode = 'unique'))
        print("zmin computed : ", numpy.array2string(zminc, floatmode = 'unique'))

        assert (abs(zgemc - zgem) < 1e-13).all() and (abs(zmax - zmaxc) < 1e-13).all() and ((zmin - zminc) < 1e-13).all() == True

class Test_celerity_calculation():
    
    def test_GivenFirstElementOfCelqIsSmallerThanQ_WhenGetCelerity_ThenReturnFirstElementOfCelc(self):
        
        FirtsElementOfCelc = 10  
        q = 11.0
        FirtsElementOfCelq = q-1
        cel_q = [FirtsElementOfCelq,20,30,40] 
        cel_c = [FirtsElementOfCelc,20,30,40] 
        
        celerity = dfastmi.kernel.get_celerity(q, cel_q, cel_c)
        assert celerity == 11
    
    def test_GivenFirstElementOfCelqIsBiggerThanQ_WhenGetCelerity_ThenReturnFirstElementOfCelc(self):
        
        FirtsElementOfCelc = 10  
        q = 11.0
        FirtsElementOfCelq = q+1
        cel_q = [FirtsElementOfCelq,20,30,40] 
        cel_c = [FirtsElementOfCelc,20,30,40] 
        
        celerity = dfastmi.kernel.get_celerity(q, cel_q, cel_c)
        assert celerity == FirtsElementOfCelc

    def test_GivenQBiggerThanAnyCelq_WhenGetCelerity_ThenReturnLastElementOfCelc(self):
        
        LastElementOfCelc = 40
        
        q = 50.0
        cel_q = [10,20,30,40]
        cel_c = [10,20,30,LastElementOfCelc] 
        
        celerity = dfastmi.kernel.get_celerity(q, cel_q, cel_c)
        assert celerity == LastElementOfCelc
    
class Test_relax_factors_calculation():
    def test_GivenSingleValueForCalculation_WhenRelaxFactors_ThenReturnRsigmaValueBetweenExpectedValues(self):
        Q = [2]
        T = [0.0005]
        q_stagnant = 1.0
        celerity = [1.0]
        nwidth = 1.0
        
        rsigma = dfastmi.kernel.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert 0.76<= rsigma[0] <= 0.78
        
    def test_GivenMultipleValuesForCalculation_WhenRelaxFactors_ThenReturnRsigmaValuesdBetweenExpectedValues(self):
        Q = [2,2]
        T = [0.0005,1.0]
        q_stagnant = 1.0
        celerity = [1.0,0.0005]
        nwidth = 1.0
        
        rsigma = dfastmi.kernel.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert 0.76<= rsigma[0] <= 0.78
        assert 0.76<= rsigma[1] <= 0.78
        
    def test_GivenMultipleValuesForCalculationWithDifferentWidth_WhenRelaxFactors_ThenReturnRsigmaVaryingValuesdBetweenExpectedValues(self):
        Q = [2,2]
        T = [0.0005,1.0]
        q_stagnant = 1.0
        celerity = [1.0,0.0005]
        nwidth = 5.0
        
        rsigma = dfastmi.kernel.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert 0.94<= rsigma[0] <= 0.96
        assert 0.94<= rsigma[0] <= 0.96
        
    def test_GivenQSameAsQStagnant_WhenRelaxFactors_ThenReturnRsigmaValuesOfOne(self):
        Q = [2,2,2,2] 
        T = [5,5,5,5] 
        q_stagnant = 2.0
        celerity = [5,5,5,5] 
        nwidth = 2.0
        
        rsigma = dfastmi.kernel.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert rsigma == (1.0, 1.0, 1.0, 1.0)
        
    def test_GivenQSmallerThanQStagnant_WhenRelaxFactors_ThenReturnRsigmaValuesOfOne(self):
        Q = [2,2,2,2] 
        T = [5,5,5,5] 
        q_stagnant = 3.0
        celerity = [5,5,5,5] 
        nwidth = 2.0
        
        rsigma = dfastmi.kernel.relax_factors(Q, T, q_stagnant, celerity, nwidth)
        assert rsigma == (1.0, 1.0, 1.0, 1.0)
        
        
if __name__ == '__main__':
    unittest.main()