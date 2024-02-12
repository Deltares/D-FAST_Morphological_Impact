import os
import sys
from contextlib import contextmanager
from io import StringIO
from dfastmi.io.FileUtils import FileUtils

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_get_progloc():
    def test_get_progloc_01(self):
        """
        Get the location of the program.
        """
        assert FileUtils.get_progloc() != ""


class Test_absolute_path():
    def test_absolute_path_01(self):
        """
        Convert absolute path into relative path using relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        afile = "d:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.absolute_path(rootdir, rfile) == afile

    def test_absolute_path_02(self):
        """
        Empty string should not be adjusted by relative_path.
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = ""
        assert FileUtils.absolute_path(rootdir, file) == file

    def test_absolute_path_03(self):
        """
        If path on different drive, it shouldn't be adjusted by relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = "e:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.absolute_path(rootdir, file) == file

    def test_absolute_path_04(self):
        """
        Convert absolute path into relative path using relative_path (Linux).
        """
        rootdir = os.sep + "some" + os.sep + "dir"
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.absolute_path(rootdir, rfile) == afile

    def test_absolute_path_05(self):
        """
        When can't convert, return relative path back
        """
        rootdir = None
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.absolute_path(rootdir, rfile) == rfile


class Test_relative_path():
    def test_relative_path_01(self):
        """
        Convert absolute path into relative path using relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        afile = "d:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.relative_path(rootdir, afile) == rfile

    def test_relative_path_02(self):
        """
        Empty string should not be adjusted by relative_path.
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = ""
        assert FileUtils.relative_path(rootdir, file) == file

    def test_relative_path_03(self):
        """
        If path on different drive, it shouldn't be adjusted by relative_path (Windows).
        """
        rootdir = "d:" + os.sep + "some" + os.sep + "dir"
        file = "e:" + os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.relative_path(rootdir, file) == file

    def test_relative_path_04(self):
        """
        Convert absolute path into relative path using relative_path (Linux).
        """
        rootdir = os.sep + "some" + os.sep + "dir"
        afile = os.sep + "some" + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        rfile = ".." + os.sep + "other" + os.sep + "dir" + os.sep + "file.ext"
        assert FileUtils.relative_path(rootdir, afile) == rfile