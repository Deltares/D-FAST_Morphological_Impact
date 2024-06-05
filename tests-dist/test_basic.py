import os
import subprocess
import sys
from contextlib import contextmanager
from io import StringIO

import context

# dfast binary path relative to tstdir
dfastexe = "../../dfastmi.dist/dfastmi.exe"


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Test_basic:
    def test_basic_00(self):
        """
        Test whether program runs at all.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        success = False
        try:
            os.chdir(tstdir)
            result = subprocess.run([dfastexe, "--help"])
            success = result.returncode == 0
        finally:
            os.chdir(cwd)
        #
        self.maxDiff = None
        assert success == True

    def test_basic_01(self):
        """
        Testing program help.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            result = subprocess.run([dfastexe, "--help"], capture_output=True)
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        self.maxDiff = None
        assert outstr == [
            "usage: dfastmi.exe [-h] [--mode MODE] [--config CONFIG] [--rivers RIVERS]",
	    "",
	    "D-FAST Morphological Impact.",
	    "",
	    "optional arguments:",
	    "  -h, --help       show this help message and exit",
	    "  --mode MODE      run mode 'BATCH' or 'GUI' (GUI is default)",
	    "  --config CONFIG  name of analysis configuration file ('dfastmi.cfg' is",
	    "                   default)",
	    "  --rivers RIVERS  name of rivers configuration file ('Dutch_rivers_v3.ini' is",
	    "                   default)'] != ['usage: dfastmi.exe [-h] [--language LANGUAGE] [--mode MODE] [--config CONFIG]",
	    "                   [--rivers RIVERS] [--reduced_output]",
            "",
        ]

    def test_basic_gui(self):
        """
        Testing startup of the GUI.
        GUI will be started and closed.
        If GUI does not start test will fail.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            try:
                process = subprocess.Popen(
                    dfastexe, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                process.wait(timeout=1)

            except subprocess.TimeoutExpired:
                process.kill()

            assert (
                process.returncode is None
            ), f"Process returned exit code: {process.returncode}, please run the dfastmi.exe to find the specific error."
        finally:
            os.chdir(cwd)
