from dfastmi.io.CelerObject import CelerProperties


class Test_celerity_calculation():
    """
    Testing get celerity calculation, now a protected member of Celerity properties object 
    but used to be a method in dfastmi.kernel.core
    """

    def test_given_first_element_Of_celq_is_smaller_than_q_when_get_celerity_then_return_first_element_of_celc(self):

        first_element_of_celc = 10
        q = 11.0
        first_element_of_celq = q-1
        cel_q = [first_element_of_celq,20,30,40]
        cel_c = [first_element_of_celc,20,30,40]

        celerity = CelerProperties()._get_celerity(q, cel_q, cel_c)
        assert celerity == 11

    def test_given_first_element_Of_celq_is_bigger_than_q_when_get_celerity_then_return_first_element_of_celc(self):

        first_element_of_celc = 10
        q = 11.0
        first_element_of_celq = q+1
        cel_q = [first_element_of_celq,20,30,40]
        cel_c = [first_element_of_celc,20,30,40]

        celerity = CelerProperties()._get_celerity(q, cel_q, cel_c)
        assert celerity == first_element_of_celc

    def test_given_q_bigger_than_any_celq_when_get_celerity_then_return_last_element_of_celc(self):

        LastElementOfCelc = 40

        q = 50.0
        cel_q = [10,20,30,40]
        cel_c = [10,20,30,LastElementOfCelc]

        celerity = CelerProperties()._get_celerity(q, cel_q, cel_c)
        assert celerity == LastElementOfCelc