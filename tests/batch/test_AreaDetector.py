import math

import numpy
from mock import patch

from dfastmi.batch.AreaDetector import AreaDetector


class Test_AreaDetector:

    def test_detect_connected_regions(self):
        fcondition = numpy.array([True, False, True, True, False])
        edgeface_indexes = numpy.array([[0, 1], [1, 2], [3, 4], [4, 0], [2, 3]])

        expected_partition = numpy.array([0, -1, 1, 1, -1])
        expected_num_regions = 2

        area_detector = AreaDetector()
        partition, num_regions = area_detector._detect_connected_regions(
            fcondition, edgeface_indexes
        )

        assert numpy.array_equal(partition, expected_partition)
        assert num_regions == expected_num_regions

    def test_comp_sedimentation_volume2(self):
        dzgem = numpy.array([0.1, 0.2, 0.3, 0.4, 0.5])
        dzmin = 0.2
        area = numpy.array([100, 200, 300, 400, 500])
        slength = 10.0
        nwidth = 5.0

        area_detector = AreaDetector()
        dvol_result, area_eq_result, dvol_eq_result = (
            area_detector._comp_sedimentation_volume2(
                dzgem, dzmin, area, slength, nwidth
            )
        )

        expected_dvol = 20.833333333333336
        expected_area_eq = 1200.0
        expected_dvol_eq = 500.0

        assert numpy.isclose(
            dvol_result, expected_dvol
        ), f"Incorrect dvol: {dvol_result}"
        assert numpy.isclose(
            area_eq_result, expected_area_eq
        ), f"Incorrect area_eq: {area_eq_result}"
        assert numpy.isclose(
            dvol_eq_result, expected_dvol_eq
        ), f"Incorrect dvol_eq: {dvol_eq_result}"

    def test_comp_sedimentation_volume1_tot(self):
        sedvol = numpy.array([1, 2, 3, 4, 5])
        sbin = numpy.array([1, 2, 3, 4, 5])
        afrac = numpy.array([1, 2, 3, 4, 5])
        siface = numpy.array([1, 2, 3, 4, 5])
        sbin_length = 10.0
        slength = 20.0

        area_detector = AreaDetector()
        tot_dredge_vol, wght_all_dredge_sed = (
            area_detector._comp_sedimentation_volume1_tot(
                sedvol, sbin, afrac, siface, sbin_length, slength
            )
        )

        expected_tot_dredge_vol = 5.0
        expected_wght_all_dredge_sed = numpy.array([1.0, 2.0, 0.0, 0.0, 0.0])

        assert math.isclose(
            tot_dredge_vol, expected_tot_dredge_vol
        ), f"Incorrect tot_dredge_vol: {tot_dredge_vol}"
        assert numpy.isclose(
            wght_all_dredge_sed.all(), expected_wght_all_dredge_sed.all()
        ), f"Incorrect wght_all_dredge_sed: {wght_all_dredge_sed}"

    def test_comp_sedimentation_volume1_one_width_bin(self):
        dvol = numpy.array([0.1, 0.2, 1.1, 0.3])
        sbin = numpy.array([0.1, 0.2, 0.3, 0.4])
        afrac = numpy.array([0.5, 0.6, 0.7, 0.8])
        siface = numpy.array([0.9, 1.0, 1.1, 1.2])
        sbin_length = 1.0
        slength = 2.0

        expected_tot_dredge_vol = 10.0
        expected_wght_all_dredge = numpy.array([0.1, 0.2, 0.3, 0.4])

        with patch(
            "dfastmi.batch.AreaDetector.AreaDetector._comp_sedimentation_volume1_tot"
        ) as mock_comp_sedimentation_volume1_tot:
            mock_comp_sedimentation_volume1_tot.return_value = (
                expected_tot_dredge_vol,
                expected_wght_all_dredge,
            )

            area_detector = AreaDetector()
            tot_dredge_vol, wght_all_dredge = (
                area_detector._comp_sedimentation_volume1_one_width_bin(
                    dvol, sbin, afrac, siface, sbin_length, slength
                )
            )

            assert mock_comp_sedimentation_volume1_tot.call_count == 1
            assert math.isclose(
                tot_dredge_vol, expected_tot_dredge_vol
            ), f"Incorrect tot_dredge_vol: {tot_dredge_vol}"
            assert numpy.isclose(
                wght_all_dredge.all(), expected_wght_all_dredge.all()
            ), f"Incorrect wght_all_dredge: {wght_all_dredge}"

    def test_comp_sedimentation_volume1(self):
        dzgem = numpy.array([0.1, 0.2, -0.1, 0.3])
        dzmin = 0.05
        area = numpy.array([1.0, 2.0, 3.0, 4.0])
        wbin = numpy.array([0, 1, 0, 1])
        siface = numpy.array([0, 1, 0, 1])
        afrac = numpy.array([0.5, 0.6, 0.7, 0.8])
        sbin = numpy.array([0.1, 0.2, 0.3, 0.4])
        wthresh = numpy.array([0.1, 0.2, 0.3])
        slength = 1.0
        sbin_length = 1.0

        returned_dredge_vol = 10
        expected_call_count_comp_sedimentation_volume1_one_width_bin = 2
        expected_tot_dredge_vol = expected_call_count_comp_sedimentation_volume1_one_width_bin*returned_dredge_vol
        expected_wght_all_dredge = numpy.array([0.1, 0.2, 0.3, 0.4])
        
        with (patch("dfastmi.batch.AreaDetector.AreaDetector._comp_sedimentation_volume1_one_width_bin") as mock_comp_sedimentation_volume1_one_width_bin, 
              patch("dfastmi.batch.AreaDetector.numpy.bincount", return_value=expected_wght_all_dredge)):
            mock_comp_sedimentation_volume1_one_width_bin.return_value = (returned_dredge_vol, expected_wght_all_dredge)

            area_detector = AreaDetector()
            tot_dredge_vol, wght_all_dredge = area_detector._comp_sedimentation_volume1(dzgem, dzmin, area, wbin, siface, afrac, sbin, wthresh, slength, sbin_length)
            
            assert mock_comp_sedimentation_volume1_one_width_bin.call_count == expected_call_count_comp_sedimentation_volume1_one_width_bin
            assert math.isclose(tot_dredge_vol, expected_tot_dredge_vol), f"Incorrect tot_dredge_vol: {tot_dredge_vol}"
            assert numpy.isclose(wght_all_dredge.all(), expected_wght_all_dredge.all()), f"Incorrect wght_all_dredge: {wght_all_dredge}"

