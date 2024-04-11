from pathlib import Path

import numpy

from dfastmi.batch.XyzFileWriter import XyzFileWriter


class Test_XyzFileWriter:

    def assert_lines_are_equal(self, xyz_file_location, expected_lines):
        with open(xyz_file_location, "r") as file:
            for expected_line in expected_lines:
                actual_line = file.readline().strip()
                assert (
                    actual_line == expected_line
                ), f"Expected line '{expected_line}' not found in the file."

    def test_plot_areas_with_SedimentationAreaPlotter_writes_xyz_file(
        self, tmp_path: Path
    ):
        xyz_file_location = tmp_path / "file.xyz"
        wbin_labels: list[str] = ["1", "2", "3"]
        kmid: numpy.ndarray = numpy.array([0, 1, 2, 3, 4])

        binvol = []
        binvol.append(numpy.array([1, 2, 3]))
        binvol.append(numpy.array([10, 11, 12]))
        binvol.append(numpy.array([19, 20, 21]))

        XyzFileWriter.write_xyz_file(wbin_labels, kmid, binvol, xyz_file_location)

        expected_lines = [
            '"chainage" "1" "2" "3"',
            "0.00     1.00    10.00    19.00",
            "1.00     2.00    11.00    20.00",
            "2.00     3.00    12.00    21.00",
        ]

        assert xyz_file_location.exists()
        self.assert_lines_are_equal(xyz_file_location, expected_lines)
