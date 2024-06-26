from typing import List

import numpy

from dfastmi.kernel.typehints import Vector


class BedLevelCalculator:
    """
    This class is used to calculate bed level related values.
    """

    def __init__(self, number_of_periods: int):
        """
        number_of_periods : int
         Amount of the equilibrium bed level change for each respective discharge period available.

        Raises:
        - TypeError, when number_of_periods is not of type int
        """
        if not isinstance(number_of_periods, int):
            raise TypeError(
                f"Amount of the equilibrium bed level change for each respective discharge period available is not of expected type {int}."
            )
        self.number_of_periods = number_of_periods

    def get_element_wise_maximum(self, dzb: List[numpy.ndarray]) -> numpy.ndarray:
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

    def get_element_wise_minimum(self, dzb: List[numpy.ndarray]) -> numpy.ndarray:
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

    def get_linear_average(
        self, fraction_of_year: Vector, dzb: List[numpy.ndarray]
    ) -> numpy.ndarray:
        """
        This method gets the linear average from the given bed levels.

        Arguments
        ---------
        fraction_of_year : Vector
            A vector of values each representing the fraction of the year.
        dzb   : List[numpy.ndarray]
            List of arrays containing the bed level change at the beginning of each respective discharge period.

        Returns
        -------
        dzgem : numpy.ndarray
            Yearly mean bed level change.
        """
        dzgem = 0
        for i in range(self.number_of_periods):
            dzgem += dzb[i] * (fraction_of_year[i] + fraction_of_year[i - 1]) / 2
        return dzgem

    def get_bed_level_changes(
        self, dzq: List[numpy.ndarray], rsigma: Vector
    ) -> List[numpy.ndarray]:
        """
        This routine computes the bed level changes.
        This routine requires that dzq and rsigma have the same length.
        A stagnant period can be represented by a period with rsigma = 1.

        Arguments
        ---------
        dzq : List[numpy.ndarray]
            A list of arrays containing the equilibrium bed level change for each respective discharge period.
        rsigma : Vector
            A Vector of relaxation factors, one for each period.

        Returns
        -------
        dzb   : List[numpy.ndarray]
            List of arrays containing the bed level change at the beginning of each respective discharge period.
        """
        vsigma = self.__compute_vsigma(rsigma, dzq)
        den = self.__compute_denominator(vsigma)
        dzb = self.__compute_dzb_at_the_beginning_of_each_period(dzq, vsigma, den)
        return dzb

    def __compute_vsigma(
        self, rsigma: Vector, dzq: List[numpy.ndarray]
    ) -> List[numpy.ndarray]:
        vsigma = []

        mask = self.__get_mask(dzq)

        for rsigma_value in rsigma:
            vsigma_tmp = numpy.ones(mask.shape) * rsigma_value
            vsigma_tmp[mask] = 1
            vsigma.append(vsigma_tmp)

        return vsigma

    def __get_mask(self, dzq: List[numpy.ndarray]) -> numpy.ndarray[bool]:
        mask = numpy.zeros_like(self.number_of_periods, dtype=bool)
        for dzq_value in dzq:
            if dzq_value is not None:
                mask = mask | numpy.isnan(dzq_value)
        return mask

    def __compute_denominator(self, vsigma: List[numpy.ndarray]) -> int:
        for i in range(self.number_of_periods):
            if i == 0:
                den = vsigma[0]
            else:
                den = den * vsigma[i]
        den = 1 - den
        return den

    def __compute_dzb_at_the_beginning_of_each_period(
        self, dzq: List[numpy.ndarray], vsigma: List[numpy.ndarray], den: int
    ) -> List[numpy.ndarray]:
        dzb: List[numpy.ndarray] = []
        for i in range(self.number_of_periods):
            enm = self.__compute_enumerator(dzq, i, vsigma)

            # divide by denominator
            with numpy.errstate(divide="ignore", invalid="ignore"):
                dzb.append(numpy.where(den != 0, enm / den, 0))
        return dzb

    def __compute_enumerator(
        self, dzq: List[numpy.ndarray], i: int, vsigma: List[numpy.ndarray]
    ) -> int:
        enm = 0
        for j in range(self.number_of_periods):
            jr = (i + j) % self.number_of_periods
            dzb_tmp = dzq[jr] * (1 - vsigma[jr])

            for k in range(j + 1, self.number_of_periods):
                kr = (i + k) % self.number_of_periods
                dzb_tmp = dzb_tmp * vsigma[kr]

            enm += dzb_tmp

        return enm
