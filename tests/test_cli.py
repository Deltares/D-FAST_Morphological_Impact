import os
import sys
from contextlib import contextmanager
from io import StringIO

import context

import dfastmi.cli
from dfastmi.io.ApplicationSettingsHelper import ApplicationSettingsHelper
from dfastmi.io.RiversObject import RiversObject


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_interactive_mode:
    def test_interactive_mode_01(self):
        """
        Testing interactive_mode in Dutch.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.NL.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                with open("waqmorf.in", "r") as input:
                    dfastmi.cli.interactive_mode(input, rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        prefixes = "Dit is versie"
        #
        self.maxDiff = None
        refstr = open(tstdir + os.sep + "ref_stdout_NL.txt", "r").read().splitlines()
        outstr = [x for x in outstr if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert outstr == refstr
        #
        result = open(tstdir + os.sep + "verslag.run", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_verslag.run", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = open(tstdir + os.sep + "jaargem.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "maxmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf_org.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "minmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf_org.out", "r").read().splitlines()
        assert result == refstr

    def test_interactive_mode_02(self):
        """
        Testing interactive_mode in English.
        """
        ApplicationSettingsHelper.load_program_texts("dfastmi/messages.UK.ini")
        rivers = RiversObject("dfastmi/Dutch_rivers_v1.ini")
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            with captured_output() as (out, err):
                with open("waqmorf.in", "r") as input:
                    dfastmi.cli.interactive_mode(input, rivers, False)
            outstr = out.getvalue().splitlines()
        finally:
            os.chdir(cwd)
        #
        prefixes = "This is version"
        #
        self.maxDiff = None
        refstr = open(tstdir + os.sep + "ref_stdout_UK.txt", "r").read().splitlines()
        outstr = [x for x in outstr if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert outstr == refstr
        #
        result = open(tstdir + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = open(tstdir + os.sep + "yearavg_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "max_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf_org.out", "r").read().splitlines()
        assert result == refstr
        #
        result = open(tstdir + os.sep + "min_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf_org.out", "r").read().splitlines()
        assert result == refstr
