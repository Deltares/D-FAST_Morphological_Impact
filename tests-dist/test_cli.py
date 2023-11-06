import context
import os
import sys

from contextlib import contextmanager
from io import StringIO
import subprocess

# dfast binary path relative to tstdir
dfastexe = "../../dfast-dist/dfast.exe"

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class Test_interactive_mode():
    def test_interactive_mode_01(self):
        """
        Testing interactive_mode in Dutch.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                with open("waqmorf.in", "r") as input:
                    subprocess.call([dfastexe,"--mode","CLI"])
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        refstr = open(tstdir + os.sep + "ref_stdout_NL.txt", "r").read().splitlines()
        assert outstr[:21] == refstr[:21]
        # line 22 contains the version number and will thus change
        assert outstr[23:] == refstr[23:]
        #
        result = open(tstdir + os.sep + "verslag.run", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_verslag.run", "r").read().splitlines()
        assert result[:21] == refstr[:21]
        # line 22 contains the version number and will thus change
        assert result[23:] == refstr[23:]
        #
        result = open(tstdir + os.sep + "jaargem.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "maxmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "minmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_interactive_mode_02(self):
        """
        Testing interactive_mode in English.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                with open("waqmorf.in", "r") as input:
                    subprocess.call([dfastexe,"--mode","CLI"])
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        refstr = open(tstdir + os.sep + "ref_stdout_UK.txt", "r").read().splitlines()
        assert outstr[:21] == refstr[:21]
        # line 22 contains the version number and will thus change
        assert outstr[23:] == refstr[23:]
        #
        result = open(tstdir + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_report.txt", "r").read().splitlines()
        assert result[:21] == refstr[:21]
        # line 22 contains the version number and will thus change
        assert result[23:] == refstr[23:]
        #
        result = open(tstdir + os.sep + "yearavg_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "max_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "min_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr
