import os
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import netCDF4
import numpy
import pytest

from dfastmi.io.FouFile import FouFile
from dfastmi.io.MapFile import MapFile
from dfastmi.io.OutputFileFactory import OutputFileFactory
from tests.io.test_OutputFile import TestOutputFile


class Test_OutputFileFactory:

    def test_creation_of_MapFileType(self):
        """
        Testing if generate Mapfile is done with key
        """
        output_file = OutputFileFactory.generate("myfile_map.nc")
        assert isinstance(output_file, MapFile)

    def test_creation_of_MapFileType_unknownKey(self):
        """
        Testing if generate Mapfile is done by default
        """
        output_file = OutputFileFactory.generate("myfile.nc")
        assert isinstance(output_file, MapFile)

    def test_creation_of_FouFileType(self):
        """
        Testing if generate Foufile is done with key
        """
        output_file = OutputFileFactory.generate("myfile_fou.nc")
        assert isinstance(output_file, FouFile)

    def test_creation_of_CustomFileType_after_registration(self):
        """
        Testing if generate Foufile is done with key
        """
        custom_file_name_suffix = "_tst.nc"
        assert custom_file_name_suffix not in OutputFileFactory._creators
        OutputFileFactory.register_creator(custom_file_name_suffix, TestOutputFile)
        output_file = OutputFileFactory.generate("myfile_tst.nc")
        assert isinstance(output_file, TestOutputFile)
        OutputFileFactory.unregister_creator(custom_file_name_suffix)
        output_file = OutputFileFactory.generate("myfile_tst.nc")
        assert isinstance(output_file, MapFile)
