import context
import dfastmi.io
import configparser
import os
import numpy

import pytest
import unittest

class load_program_texts(unittest.TestCase):
    def test_load_program_texts_01(self):
        """
        Testing load_program_texts.
        """
        print("current work directory: ", os.getcwd())
        self.assertEqual(dfastmi.io.load_program_texts("dfastmi/messages.UK.ini"), None)

class program_texts(unittest.TestCase):
    def test_program_texts_01(self):
        """
        Testing program_texts: key not found.
        """
        self.assertEqual(dfastmi.io.program_texts("@"), ["No message found for @"])

    def test_program_texts_02(self):
        """
        Testing program_texts: empty line key.
        """
        self.assertEqual(dfastmi.io.program_texts(""), [""])

    def test_program_texts_03(self):
        """
        Testing program_texts: "confirm" key.
        """
        self.assertEqual(dfastmi.io.program_texts("confirm"), ['Confirm using "y" ...',''])

class read_rivers(unittest.TestCase):
    def test_read_rivers_01(self):
        """
        Testing read_rivers, collect_values1, collect_values2 and collect_values4.
        """
        print("current work directory: ", os.getcwd())
        rivers = {}
        rivers['branches'] = ['Branch1', 'Branch2']
        rivers['reaches'] = [['Branch1 R1'], ['Branch2 R1', 'Branch2 R2']]
        rivers['qlocations'] = ['L1', 'L2']
        rivers['proprate_high'] = [[3.14], [3.65, 3.65]]
        rivers['proprate_low'] = [[0.8], [0.8, 0.9]]
        rivers['normal_width'] = [[250.0], [250.0, 100.0]]
        rivers['ucritical'] = [[0.3], [0.3, 0.3]]
        rivers['qbankfull'] = [[150.0], [2500.0, 2500.0]]
        rivers['qstagnant'] = [[50.0], [0.0, 1500.0]]
        rivers['qmin'] = [[1.0], [1.0, 1.0]]
        rivers['qfit'] = [[(10.0, 20.0)], [(800.0, 1280.0), (800.0, 1280.0)]]
        rivers['qlevels'] = [[(100.0, 200.0, 300.0, 400.0)], [(1000.0, 2000.0, 3000.0, 4000.0), (1000.0, 2000.0, 3000.0, 4000.0)]]
        rivers['dq'] = [[(5.0, 15.0)], [(1000.0, 1000.0), (1000.0, 1000.0)]]
        self.maxDiff = None
        self.assertEqual(dfastmi.io.read_rivers("tests/read_rivers_test.ini"), rivers)

class collect_values1(unittest.TestCase):
    def test_collect_values1_01(self):
        """
        Testing sucessful collect_values1 call.
        """
        config = configparser.ConfigParser()
        config.add_section("Branches")
        config["Branches"]["A"] = "0.0"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0"
        config["Branch1"]["A1"] = "2.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0"
        config["Branch2"]["A3"] = "4.0"
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        data = [[2.0, 1.0], [3.0, 0.0, 4.0]]
        self.maxDiff = None
        self.assertEqual(dfastmi.io.collect_values1(config, branches, nreaches, key), data)

    def test_collect_values1_02(self):
        """
        Testing collect_values1 raising an Exception.
        """
        config = configparser.ConfigParser()
        config.add_section("Branches")
        config["Branches"]["A"] = "0.0 0.1"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0"
        config["Branch1"]["A1"] = "2.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0"
        config["Branch2"]["A3"] = "4.0"
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        with self.assertRaises(Exception) as cm:
            dfastmi.io.collect_values1(config, branches, nreaches, key)
        self.assertEqual(str(cm.exception), 'Incorrect number of values read from "0.0 0.1". Need 1 values.')

class collect_values2(unittest.TestCase):
    def test_collect_values2_01(self):
        """
        Testing successful collect_values2 call.
        """
        config = configparser.ConfigParser()
        config.add_section("Branches")
        config["Branches"]["A"] = "0.0 0.0"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0 0.1"
        config["Branch1"]["A1"] = "2.0 0.2"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3"
        config["Branch2"]["A3"] = "4.0 0.4"
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        data = [[(2.0, 0.2), (1.0, 0.1)], [(3.0, 0.3), (0.0, 0.0), (4.0, 0.4)]]
        self.maxDiff = None
        self.assertEqual(dfastmi.io.collect_values2(config, branches, nreaches, key), data)

    def test_collect_values2_02(self):
        """
        Testing collect_values2 raising an Exception.
        """
        config = configparser.ConfigParser()
        config.add_section("Branches")
        config["Branches"]["A"] = "0.0 0.0"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0"
        config["Branch1"]["A1"] = "2.0 0.2"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3"
        config["Branch2"]["A3"] = "4.0 0.4"
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        with self.assertRaises(Exception) as cm:
            dfastmi.io.collect_values2(config, branches, nreaches, key)
        self.assertEqual(str(cm.exception), 'Incorrect number of values read from "1.0". Need 2 values.')

class collect_values4(unittest.TestCase):
    def test_collect_values4_01(self):
        """
        Testing collect_values4.
        """
        config = configparser.ConfigParser()
        config.add_section("Branches")
        config["Branches"]["A"] = "0.0 0.0 0.0 0.1"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0 0.1 0.0 0.01"
        config["Branch1"]["A1"] = "2.0 0.2 0.02 0.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3 -0.03 0.0"
        config["Branch2"]["A3"] = "4.0 0.4 0.0 -0.04"
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        data = [[(2.0, 0.2, 0.02, 0.0), (1.0, 0.1, 0.0, 0.01)], [(3.0, 0.3, -0.03, 0.0), (0.0, 0.0, 0.0, 0.1), (4.0, 0.4, 0.0, -0.04)]]
        self.maxDiff = None
        self.assertEqual(dfastmi.io.collect_values4(config, branches, nreaches, key), data)

    def test_collect_values4_02(self):
        """
        Testing collect_values4 raising an Exception.
        """
        config = configparser.ConfigParser()
        config.add_section("Branches")
        config["Branches"]["A"] = "0.0 0.0 0.0 0.1"
        config.add_section("Branch1")
        config["Branch1"]["A"] = "1.0 0.1 0.0 0.01"
        config["Branch1"]["A1"] = "2.0 0.2 0.02 0.0"
        config.add_section("Branch2")
        config["Branch2"]["A1"] = "3.0 0.3 -0.03 0.0"
        config["Branch2"]["A3"] = "4.0 0.4 -0.04"
        branches = ["Branch1", "Branch2"]
        nreaches = [2, 3]
        key = "A"
        with self.assertRaises(Exception) as cm:
            dfastmi.io.collect_values4(config, branches, nreaches, key)
        self.assertEqual(str(cm.exception), 'Incorrect number of values read from "4.0 0.4 -0.04". Need 4 values.')

class write_config(unittest.TestCase):
    def test_write_config_01(self):
        """
        Testing write_config.
        """
        filename = "test.cfg"
        config = configparser.ConfigParser()
        config.add_section("G 1")
        config["G 1"]["K 1"] = "V 1"
        config.add_section("Group 2")
        config["Group 2"]["K1"] = "1.0 0.1 0.0 0.01"
        config["Group 2"]["K2"] = "2.0 0.2 0.02 0.0"
        config.add_section("Group 3")
        config["Group 3"]["LongKey"] = "3"
        dfastmi.io.write_config(filename, config)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['[G 1]',
                         '  k 1     = V 1',
                         '',
                         '[Group 2]',
                         '  k1      = 1.0 0.1 0.0 0.01',
                         '  k2      = 2.0 0.2 0.02 0.0',
                         '',
                         '[Group 3]',
                         '  longkey = 3']
        self.assertEqual(all_lines, all_lines_ref)

#class read_fm_map(unittest.TestCase):
#    def test_read_fm_map_01(self):
#        """
#        Testing read_fm_map.
#        """
#        filename = "test-map.nc"
#        varname = "var"
#        location = "face"
#        datac = dfastmi.io.read_fm_map(filename, varname)
#        data = []
#        self.assertTrue((data == datac).all())

# get_mesh_and_facedim_names
# copy_ugrid
# copy_var
# ugrid_add

class read_waqua_xyz(unittest.TestCase):
    def test_read_waqua_xyz_01(self):
        """
        Read WAQUA xyz file default column 2.
        """
        filename = "tests/read_waqua_xyz_test.xyc"
        data = dfastmi.io.read_waqua_xyz(filename)
        datar = numpy.array([3., 6., 9., 12.])
        print("data reference: ", datar)
        print("data read     : ", data)
        self.assertEqual(numpy.shape(data), (4,))
        self.assertTrue((data == datar).all())

    def test_read_waqua_xyz_02(self):
        """
        Read WAQUA xyz file columns 1 and 2.
        """
        filename = "tests/read_waqua_xyz_test.xyc"
        col = (1,2)
        data = dfastmi.io.read_waqua_xyz(filename, col)
        datar = numpy.array([[ 2., 3.], [ 5., 6.], [ 8., 9.], [11., 12.]])
        print("data reference: ", datar)
        print("data read     : ", data)
        self.assertEqual(numpy.shape(data), (4,2))
        self.assertTrue((data == datar).all())

class write_simona_box(unittest.TestCase):
    def test_write_simona_box_01(self):
        """
        Write small SIMONA BOX file.
        """
        filename = "test.box"
        data = numpy.array([[1, 2, 3],[4, 5, 6],[7, 8, 9]])
        firstm = 0
        firstn = 0
        dfastmi.io.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['      BOX MNMN=(   1,    1,    3,    3), VARIABLE_VAL=',
                         '          1.000       2.000       3.000',
                         '          4.000       5.000       6.000',
                         '          7.000       8.000       9.000']
        self.assertEqual(all_lines, all_lines_ref)

    def test_write_simona_box_02(self):
        """
        Write small SIMONA BOX file with offset.
        """
        filename = "test.box"
        data = numpy.array([[0, 0, 0, 0, 0], [0, 0, 1, 2, 3],[0, 0, 4, 5, 6],[0, 0, 7, 8, 9]])
        firstm = 1
        firstn = 2
        dfastmi.io.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['      BOX MNMN=(   2,    3,    4,    5), VARIABLE_VAL=',
                         '          1.000       2.000       3.000',
                         '          4.000       5.000       6.000',
                         '          7.000       8.000       9.000']
        self.assertEqual(all_lines, all_lines_ref)

    def test_write_simona_box_03(self):
        """
        Write large SIMONA BOX file.
        """
        filename = "test.box"
        data = numpy.zeros((15,15))
        firstm = 0
        firstn = 0
        dfastmi.io.write_simona_box(filename, data, firstm, firstn)
        all_lines = open(filename, "r").read().splitlines()
        all_lines_ref = ['      BOX MNMN=(   1,    1,   15,   10), VARIABLE_VAL=']
        all_lines_ref.extend(['          0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000       0.000']*15)
        all_lines_ref.extend(['      BOX MNMN=(   1,   11,   15,   15), VARIABLE_VAL='])
        all_lines_ref.extend(['          0.000       0.000       0.000       0.000       0.000']*15)
        self.maxDiff = None
        self.assertEqual(all_lines, all_lines_ref)

class absolute_path(unittest.TestCase):
    def test_absolute_path_01(self):
        """
        Convert absolute path into relative path using relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        afile = "d:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        self.assertEqual(dfastmi.io.absolute_path(rootdir, rfile), afile)

    def test_absolute_path_02(self):
        """
        Empty string should not be adjusted by relative_path.
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = ""
        self.assertEqual(dfastmi.io.absolute_path(rootdir, file), file)

    def test_absolute_path_03(self):
        """
        If path on different drive, it shouldn't be adjusted by relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = "e:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        self.assertEqual(dfastmi.io.absolute_path(rootdir, file), file)

    def test_absolute_path_04(self):
        """
        Convert absolute path into relative path using relative_path (Linux).
        """
        rootdir = os.sep + "some" + os.sep + "dir"
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        self.assertEqual(dfastmi.io.absolute_path(rootdir, rfile), afile)

class relative_path(unittest.TestCase):
    def test_relative_path_01(self):
        """
        Convert absolute path into relative path using relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        afile = "d:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        self.assertEqual(dfastmi.io.relative_path(rootdir, afile), rfile)

    def test_relative_path_02(self):
        """
        Empty string should not be adjusted by relative_path.
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = ""
        self.assertEqual(dfastmi.io.relative_path(rootdir, file), file)

    def test_relative_path_03(self):
        """
        If path on different drive, it shouldn't be adjusted by relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = "e:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        self.assertEqual(dfastmi.io.relative_path(rootdir, file), file)

    def test_relative_path_04(self):
        """
        Convert absolute path into relative path using relative_path (Linux).
        """
        rootdir = os.sep + "some" + os.sep + "dir"
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        self.assertEqual(dfastmi.io.relative_path(rootdir, afile), rfile)
