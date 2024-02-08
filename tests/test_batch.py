import context
import dfastmi.batch

import os

import sys
import numpy
import netCDF4
from contextlib import contextmanager
from io import StringIO

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_batch_mode():
    def test_batch_mode_00(self):
        """
        Testing batch_mode: missing configuration file.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.NL.ini")
        rivers = dfastmi.io.RiversObject("dfastmi/Dutch_rivers_v1.ini")
        with captured_output() as (out, err):
            dfastmi.batch.batch_mode("config.cfg", rivers, False)
        outstr = out.getvalue().splitlines()
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == ["[Errno 2] No such file or directory: 'config.cfg'"]

    def test_batch_mode_01(self):
        """
        Testing batch_mode: running configuration file - Dutch report.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.NL.ini")
        rivers = dfastmi.io.RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("c01.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = ('Dit is versie')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "verslag.run", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_verslag.run", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "jaargem.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "maxmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "minmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_batch_mode_02(self):
        """
        Testing batch_mode: running configuration file - English report.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.UK.ini")
        rivers = dfastmi.RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("c01.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = ('This is version')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "yearavg_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "max_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "output" + os.sep + "min_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_batch_mode_03(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        """
        dfastmi.io.load_program_texts("dfastmi/messages.UK.ini")
        rivers = dfastmi.RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                dfastmi.batch.batch_mode("Qmin_4000.cfg", rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        print(outstr)
        #assert outstr == []
        #
        prefixes = ('This is version')
        #
        result = open(tstdir + os.sep + "output" + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(refdir + os.sep + "report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        ncRes = netCDF4.Dataset(tstdir + os.sep + "output" + os.sep + "dfastmi_results.nc")
        ncRef = netCDF4.Dataset(refdir + os.sep + "dfastmi_results.nc")
        
        fields = ["avgdzb", "mindzb", "maxdzb"]
        for f in fields:
            result = ncRes.variables[f]
            refdat = ncRef.variables[f]
            assert (result[...] == refdat[...]).all()
