import numpy
from typing import Tuple, List
Vector = Tuple[float, ...]


class BedLevelCalculator:
    """
    This class is used to calculate bed level related values.
    """

    def __init__(self, dzq:List[numpy.ndarray]):
        """
        dzq : List[numpy.ndarray]
        A list of arrays containing the equilibrium bed level change for each respective discharge period.

        number_of_periods
            Amount of the equilibrium bed level change for each respective discharge period available.
        """
        self.number_of_periods = len(dzq)

    def get_element_wise_maximum(self, dzb: List[numpy.ndarray]):
        """
        This method gets the element wise maximum from the given bed levels.

        Arguments
        ---------
        dzb   : List[numpy.ndarray]
            List of arrays containing the bed level change at the beginning of each respective discharge period.

        Returns
        -------
        dzmax : numpy.ndarray
            Maximum bed level change.
        """
        return numpy.maximum.reduce(dzb)

    def get_element_wise_minimum(self, dzb: List[numpy.ndarray]):
        """
        This method gets the element wise minimum from the given bed levels.

        Arguments
        ---------
        dzb   : List[numpy.ndarray]
            List of arrays containing the bed level change at the beginning of each respective discharge period.

        Returns
        -------
        dzmin : numpy.ndarray
            minimum bed level change.
        """
        return numpy.minimum.reduce(dzb)

    def linear_average(self, T, dzb):
        """
        This method gets the linear average from the given bed levels.

        Arguments
        ---------
        T     : Vector
            A vector of periods indicating the number of days during which each discharge applies.
        N     : int
            Amount of the equilibrium bed level change for each respective discharge period available.
        dzb   : List[numpy.ndarray]
            List of arrays containing the bed level change at the beginning of each respective discharge period.

        Returns
        -------
        dzgem : numpy.ndarray
            Yearly mean bed level change.
        """
        for i in range(self.number_of_periods):
            if i == 0:
                dzgem = dzb[0] * (T[0] + T[-1]) / 2
            else:
                dzgem = dzgem + dzb[i] * (T[i] + T[i-1]) / 2
        return dzgem

    def get_bed_level_changes(self, dzq: List[numpy.ndarray], rsigma: Vector):
        """
        This routine computes the bed level changes.
        This routine requires that dzq and rsigma have the same length.
        A stagnant period can be represented by a period with rsigma = 1.

        Arguments
        ---------
        dzq : List[numpy.ndarray]
            A list of arrays containing the equilibrium bed level change for each respective discharge period.
        rsigma : Vector
            A tuple of relaxation factors, one for each period.

        Returns
        -------
        dzb   : List[numpy.ndarray]
            List of arrays containing the bed level change at the beginning of each respective discharge period.
        """
        mask = self.__get_mask__(dzq)
        vsigma = self.__compute_vsigma__(rsigma, mask)
        den = self.__compute_denominator__(self.number_of_periods, vsigma)
        dzb = self.__compute_dzb_at_the_beginning_of_each_period__(dzq, vsigma, den)
        return dzb

    def __get_mask__(self, dzq):
        firstQ = True
        for i in range(self.number_of_periods):
            if dzq[i] is None:
                pass
            elif firstQ:
                mask = numpy.isnan(dzq[0])
                firstQ = False
            else:
                mask = mask | numpy.isnan(dzq[i])
        return mask

    def __compute_vsigma__(self, rsigma, mask):
        vsigma: List[numpy.ndarray]
        vsigma = []
        sz = numpy.shape(mask)
        for i in range(self.number_of_periods):
            vsigma_tmp = numpy.ones(sz) * rsigma[i]
            vsigma_tmp[mask] = 1
            vsigma.append( vsigma_tmp )
        return vsigma

    def __compute_denominator__(self, N, vsigma):
        for i in range(N):
            if i == 0:
                den = vsigma[0]
            else:
                den = den * vsigma[i]
        den = 1 - den
        return den

    def __compute_dzb_at_the_beginning_of_each_period__(self, dzq, vsigma, den):
        dzb: List[numpy.ndarray] = []
        for i in range(self.number_of_periods):
            enm = self.__compute_enumerator__(dzq, self.number_of_periods, i, vsigma)

            # divide by denominator
            with numpy.errstate(divide="ignore", invalid="ignore"):
                dzb.append(numpy.where(den != 0, enm / den, 0))
        return dzb

    def __compute_enumerator__(self, dzq, N, i, vsigma):
        for j in range(N):
            jr = (i + j) % N
            dzb_tmp = dzq[jr] * (1 - vsigma[jr])
            for k in range(j+1,N):
                kr = (i + k) % N
                dzb_tmp = dzb_tmp * vsigma[kr]
            if j == 0:
                enm = dzb_tmp
            else:
                enm = enm + dzb_tmp
        return enm