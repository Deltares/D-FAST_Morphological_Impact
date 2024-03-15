import numpy
import pytest

from dfastmi.kernel.BedLevelCalculator import BedLevelCalculator


class Test_BedLevelCalculator:

    @pytest.mark.parametrize(
        "correct_type",
        [
            0,
            1,
            20000,
            124356789,
        ],
    )
    def test_given_correct_type_when_constructing_BedLevelCalculator_then_no_exception_error_is_raised(
        self, correct_type: int
    ):
        try:
            _ = BedLevelCalculator(correct_type)
        except Exception as exeption:
            pytest.fail(f"Unexpected exception: {exeption}")

    @pytest.mark.parametrize("incorrect_type", [None, "string", 3.14, [], {}])
    def test_given_incorrect_type_when_constructing_BedLevelCalculator_then_exception_is_raised_with_message(
        self, incorrect_type
    ):
        with pytest.raises(Exception) as exeption:
            _ = BedLevelCalculator(incorrect_type)
        assert (
            str(exeption.value)
            == f"Amount of the equilibrium bed level change for each respective discharge period available is not of expected type {int}."
        )

    def test_given_array_with_value_when_get_element_wise_maximum_then_return_maximum_array(
        self,
    ):
        number_of_periods = 0
        blc = BedLevelCalculator(number_of_periods)
        maximum_array = numpy.array([40, 45, 50, 1.0, 0.0])

        zdzb = [
            numpy.array([5, 10, 20, 1.0, 0.0]),
            numpy.array([25, 30, 35, 1.0, 0.0]),
            maximum_array,
        ]

        element_wise_maximum = blc.get_element_wise_maximum(zdzb)
        assert numpy.array_equal(element_wise_maximum, maximum_array)

    def test_given_array_with_value_when_get_element_wise_minimum_then_return_minimum_array(
        self,
    ):
        number_of_periods = 0
        blc = BedLevelCalculator(number_of_periods)
        minimum_array = numpy.array([5, 10, 20, 1.0, 0.0])

        dzb = [
            minimum_array,
            numpy.array([25, 30, 35, 1.0, 0.0]),
            numpy.array([40, 45, 50, 1.0, 0.0]),
        ]

        element_wise_minimum = blc.get_element_wise_minimum(dzb)
        assert numpy.array_equal(element_wise_minimum, minimum_array)

    @pytest.mark.parametrize(
        "fraction_of_year, linear_average_array",
        [
            ((0.5, 0.25, 0.25, 0.25), numpy.array([21.25, 26.25, 33.125, 1.0, 0.0])),
            ((0.25, 0.25, 0.25, 0.25), numpy.array([17.5, 21.25, 26.25, 0.75, 0.0])),
        ],
    )
    def test_given_array_with_value_and_varying_fraction_of_year_when_linear_average_then_return_linear_average_array(
        self, fraction_of_year, linear_average_array
    ):
        number_of_periods = 3
        blc = BedLevelCalculator(number_of_periods)

        dzb = [
            numpy.array([5, 10, 20, 1.0, 0.0]),
            numpy.array([25, 30, 35, 1.0, 0.0]),
            numpy.array([40, 45, 50, 1.0, 0.0]),
        ]

        linear_average = blc.get_linear_average(fraction_of_year, dzb)
        assert numpy.array_equal(linear_average, linear_average_array)

    @pytest.mark.parametrize(
        "rsigma, expected_bed_level_change",
        [
            (
                (2, 1, 1),
                [
                    numpy.array([5.0, 10.0, 20.0, 1.0, -0.0]),
                    numpy.array([5.0, 10.0, 20.0, 1.0, -0.0]),
                    numpy.array([5.0, 10.0, 20.0, 1.0, -0.0]),
                ],
            ),
            (
                (0, 0, 0),
                [
                    numpy.array([40, 45, 50, 1.0, 0.0]),
                    numpy.array([5, 10, 20, 1.0, 0.0]),
                    numpy.array([25, 30, 35, 1.0, 0.0]),
                ],
            ),
            (
                (0.2, 0, 1),
                [
                    numpy.array([25.0, 30.0, 35.0, 1.0, 0.0]),
                    numpy.array([9.0, 14.0, 23.0, 1.0, 0.0]),
                    numpy.array([25.0, 30.0, 35.0, 1.0, 0.0]),
                ],
            ),
            (
                (1, 0.2, 0.2),
                [
                    numpy.array([37.5, 42.5, 47.5, 1.0, 0.0]),
                    numpy.array([37.5, 42.5, 47.5, 1.0, 0.0]),
                    numpy.array([27.5, 32.5, 37.5, 1.0, 0.0]),
                ],
            ),
        ],
    )
    def test_given_array_with_value_and_varying_rsigma_when_get_bed_level_changes_then_return_bed_level_change(
        self, rsigma, expected_bed_level_change
    ):
        dzq = [
            numpy.array([5, 10, 20, 1.0, 0.0]),
            numpy.array([25, 30, 35, 1.0, 0.0]),
            numpy.array([40, 45, 50, 1.0, 0.0]),
        ]

        number_of_periods = len(dzq)
        blc = BedLevelCalculator(number_of_periods)

        bed_level_change = blc.get_bed_level_changes(dzq, rsigma)
        assert numpy.allclose(bed_level_change, expected_bed_level_change, atol=1e-6)
