import context
import dfastmi.batch
import dfastmi.io
import os

import unittest

import sys
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


class batch_mode(unittest.TestCase):
    def test_batch_mode_00(self):
        """
        Testing batch_mode: missing configuration file.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.NL.ini")
        rivers = dfastmi.io.read_rivers("dfastmi/Dutch_rivers.ini")
        with captured_output() as (out, err):
            dfastmi.batch.batch_mode("config.cfg", rivers, False)
        outstr = out.getvalue().splitlines()
        #
        #for s in outstr:
        #    print(s)
        self.maxDiff = None
        self.assertEqual(outstr, ["[Errno 2] No such file or directory: 'config.cfg'"])

    def test_batch_mode_01(self):
        """
        Testing batch_mode: missing configuration file.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.NL.ini")
        rivers = dfastmi.io.read_rivers("dfastmi/Dutch_rivers.ini")
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
        self.assertEqual(outstr, [])
        #
        result = open(tstdir + os.sep + "verslag.run", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_verslag.run", "r").read().splitlines()
        self.assertEqual(result, refstr)
        #
        result = open(tstdir + os.sep + "jaargem.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        self.assertEqual(result, refstr)
        #
        result = open(tstdir + os.sep + "maxmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        self.assertEqual(result, refstr)
        #
        result = open(tstdir + os.sep + "minmorf.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        self.assertEqual(result, refstr)

    def test_batch_mode_02(self):
        """
        Testing batch_mode: missing configuration file.
        """
        dfastmi.io.load_program_texts("dfastmi/messages.UK.ini")
        rivers = dfastmi.io.read_rivers("dfastmi/Dutch_rivers.ini")
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
        self.assertEqual(outstr, [])
        #
        result = open(tstdir + os.sep + "report.txt", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_report.txt", "r").read().splitlines()
        self.assertEqual(result, refstr)
        #
        result = open(tstdir + os.sep + "yearavg_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        self.assertEqual(result, refstr)
        #
        result = open(tstdir + os.sep + "max_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        self.assertEqual(result, refstr)
        #
        result = open(tstdir + os.sep + "min_dzb.out", "r").read().splitlines()
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        self.assertEqual(result, refstr)

if __name__ == '__main__':
    unittest.main()