import os
import subprocess
import sys
from contextlib import contextmanager
from io import StringIO

import context
import netCDF4
import numpy
import pytest

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


class Test_batch_mode:
    def test_batch_mode_00(self):
        """
        Testing batch_mode: missing configuration file.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            result = subprocess.run(
                [
                    dfastexe,
                    "--mode",
                    "BATCH",
                    "--rivers",
                    "Dutch_rivers_v1.ini",
                    "--config",
                    "config.cfg",
                    "--language",
                    "NL",
                ],
                capture_output=True,
            )
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == ["[Errno 2] No such file or directory: 'config.cfg'"]

    @pytest.mark.parametrize(
        "tstdir, cfgfile",
        [
            ("tests/c01 - GendtseWaardNevengeul", "c01.cfg"),
            ("tests/c02 - DeLymen", "c02.cfg"),
        ],
    )
    def test_batch_mode_01(self, tstdir, cfgfile):
        """
        Testing batch_mode: normal run using WAQUA txt files (NL).
        """
        cwd = os.getcwd()
        try:
            os.chdir(tstdir)
            result = subprocess.run(
                [
                    dfastexe,
                    "--mode",
                    "BATCH",
                    "--rivers",
                    "Dutch_rivers_v1.ini",
                    "--config",
                    cfgfile,
                    "--language",
                    "NL",
                ],
                capture_output=True,
            )
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = "Dit is versie"
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "verslag.run", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_verslag.run", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "jaargem.out", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "maxmorf.out", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "minmorf.out", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_batch_mode_02(self):
        """
        Testing batch_mode: normal run using WAQUA txt files (UK).
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        try:
            os.chdir(tstdir)
            result = subprocess.run(
                [
                    dfastexe,
                    "--mode",
                    "BATCH",
                    "--rivers",
                    "Dutch_rivers_v1.ini",
                    "--config",
                    "c01.cfg",
                ],
                capture_output=True,
            )
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = "This is version"
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "report.txt", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "yearavg_dzb.out", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_jaargem.out", "r").read().splitlines()
        assert result == refstr
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "max_dzb.out", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_maxmorf.out", "r").read().splitlines()
        assert result == refstr
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "min_dzb.out", "r")
            .read()
            .splitlines()
        )
        refstr = open(tstdir + os.sep + "ref_minmorf.out", "r").read().splitlines()
        assert result == refstr

    def test_batch_mode_03(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        Version 1 configuration files.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000"
        try:
            os.chdir(tstdir)
            result = subprocess.run(
                [
                    dfastexe,
                    "--mode",
                    "BATCH",
                    "--rivers",
                    "Dutch_rivers_v1.ini",
                    "--config",
                    "Qmin_4000.cfg",
                ],
                capture_output=True,
            )
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = "This is version"
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "report.txt", "r")
            .read()
            .splitlines()
        )
        refstr = open(refdir + os.sep + "report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        ncRes = netCDF4.Dataset(
            tstdir + os.sep + "output" + os.sep + "dfastmi_results.nc"
        )
        ncRef = netCDF4.Dataset(refdir + os.sep + "dfastmi_results.nc")

        fields = ["avgdzb", "mindzb", "maxdzb"]
        for f in fields:
            result = ncRes.variables[f]
            refdat = ncRef.variables[f]
            assert (result[...] == refdat[...]).all()

    def test_batch_mode_04(self):
        """
        Testing batch_mode: Qmin = 4000 run with netCDF files (UK).
        Version 2 configuration files ... special backward consistent river configuration.
        """
        cwd = os.getcwd()
        tstdir = "tests/c01 - GendtseWaardNevengeul"
        refdir = tstdir + os.sep + "ref_Qmin_Q4000"
        try:
            os.chdir(tstdir)
            result = subprocess.run(
                [
                    dfastexe,
                    "--mode",
                    "BATCH",
                    "--rivers",
                    "rivers_Q4000_v2.ini",
                    "--config",
                    "Qmin_4000_v2.cfg",
                ],
                capture_output=True,
            )
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = "This is version"
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "report.txt", "r")
            .read()
            .splitlines()
        )
        refstr = open(refdir + os.sep + "report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        ncRes = netCDF4.Dataset(
            tstdir + os.sep + "output" + os.sep + "dfastmi_results.nc"
        )
        ncRef = netCDF4.Dataset(refdir + os.sep + "dfastmi_results.nc")

        fields = ["avgdzb", "mindzb", "maxdzb"]
        for f in fields:
            result = ncRes.variables[f]
            refdat = ncRef.variables[f]
            assert (result[...] == refdat[...]).all()

    @pytest.mark.parametrize(
        "case, config",
        [
            ("01 - Palmerswaard", "example1.cfg"),
            ("02 - Pannerdensch Kanaal", "example2.cfg"),
        ],
    )
    def test_batch_examples(self, case, config):
        """
        Testing batch_mode: example cases user manual
        """
        cwd = os.getcwd()
        tstdir = "examples" + os.sep + case
        refdir = "examples_references" + os.sep + case + os.sep + "output"
        try:
            os.chdir(tstdir)
            result = subprocess.run(
                [
                    dfastexe,
                    "--mode",
                    "BATCH",
                    "--config",
                    config,
                ],
                capture_output=True,
            )
            outstr = result.stdout.decode("UTF-8").splitlines()
        finally:
            os.chdir(cwd)
        #
        # for s in outstr:
        #    print(s)
        self.maxDiff = None
        assert outstr == []
        #
        prefixes = "This is version"
        #
        result = (
            open(tstdir + os.sep + "output" + os.sep + "report.txt", "r")
            .read()
            .splitlines()
        )
        refstr = open(refdir + os.sep + "report.txt", "r").read().splitlines()
        result = [x for x in result if not x.startswith(prefixes)]
        refstr = [x for x in refstr if not x.startswith(prefixes)]
        assert result == refstr
        #
        ncRes = netCDF4.Dataset(
            tstdir + os.sep + "output" + os.sep + "dfastmi_results.nc"
        )
        ncRef = netCDF4.Dataset(refdir + os.sep + "dfastmi_results.nc")

        fields = ["avgdzb", "mindzb", "maxdzb"]
        for f in fields:
            result = ncRes.variables[f]
            refdat = ncRef.variables[f]
            assert (result[...] == refdat[...]).all()
