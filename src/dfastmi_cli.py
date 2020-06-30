# -*- coding: utf-8 -*-
"""
Copyright (C) 2020 Stichting Deltares.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation version 2.1.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see <http://www.gnu.org/licenses/>.

contact: delft3d.support@deltares.nl
Stichting Deltares
P.O. Box 177
2600 MH Delft, The Netherlands

All indications and logos of, and references to, "Delft3D" and "Deltares"
are registered trademarks of Stichting Deltares, and remain the property of
Stichting Deltares. All rights reserved.

INFORMATION
This file is part of D-FAST Morphological Impact: https://github.com/Deltares/D-FAST_Morphological_Impact
"""

import logging
import argparse
import sys
import os
import numpy
import dfastmi_io
import dfastmi_kernel
import pathlib


def interactive_mode(reduced_output):
    global PROGTEXTS
    progloc = str(pathlib.Path(__file__).parent.absolute())
    PROGTEXTS = dfastmi_io.read_program_texts(progloc + os.path.sep + "messages.NL.ini")

    report = open("verslag.run", "w")

    rivers = dfastmi_io.read_rivers(progloc + os.path.sep + "rivers.ini")
    branches = rivers["branches"]
    reaches = rivers["reaches"]
    stages = program_texts("stage_descriptions")
    version = dfastmi_kernel.program_version()

    log_text("header", dict={"version": version})
    tdum = interactive_get_bool("confirm")

    log_text("limits")
    log_text("qblocks")
    tdum = False
    while not tdum:
        log_text("query_input-available")
        havefiles = interactive_get_bool("confirm_or")

        log_text("---")
        if havefiles:
            log_text("results_with_input")
        else:
            log_text("results_without_input")
        log_text("---")
        tdum = interactive_get_bool("confirm_or_restart")

    log_text("header", dict={"version": version}, file=report)
    log_text("limits", file=report)
    log_text("===", file=report)
    if havefiles:
        log_text("results_with_input", file=report)
    else:
        log_text("results_without_input", file=report)

    alldone = False
    while not alldone:
        ibranch = interactive_get_item("branch", branches)
        ireach = interactive_get_item("reach", reaches[ibranch])
        log_text("---")
        branch = branches[ibranch]
        reach = reaches[ibranch][ireach]

        q_location = rivers["qlocations"][ibranch]
        q_border = rivers["qbankfull"][ibranch][ireach]
        q_stagnant = rivers["qstagnant"][ibranch][ireach]
        q_min = rivers["qmin"][ibranch][ireach]
        q_fit = rivers["qfit"][ibranch][ireach]
        q_levels = rivers["qlevels"][ibranch][ireach]
        dq = rivers["dq"][ibranch][ireach]

        celerity_hg = rivers["proprate_high"][ibranch][ireach]
        celerity_lw = rivers["proprate_low"][ibranch][ireach]
        nwidth = rivers["normal_width"][ibranch][ireach]
        ucrit = rivers["ucritical"][ibranch][ireach]

        log_text("reach", dict={"reach": reach})
        log_text("---")
        alldone = interactive_get_bool("confirm_location")
        if not alldone:
            continue

        log_text("intro-measure")
        if q_stagnant > q_fit[0]:
            log_text("query_flowing_when_barriers_open")
        else:
            log_text(
                "query_flowing_above_qmin",
                dict={"border": q_location, "qmin": int(q_min)},
            )
        tdrem = interactive_get_bool("confirm_or")
        if tdrem:
            q_threshold = None
        else:
            q_threshold = interactive_get_float("query_qthreshold", dict={"border": q_location})

        if q_threshold is None or q_threshold < q_border:
            log_text("query_flowing", dict={"qborder": int(q_border)})
            tdum = interactive_get_bool("confirm_or")
            if tdum:
                q_bankfull = q_border
            else:
                q_bankfull = interactive_get_float("query_qbankfull")
        else:
            q_bankfull = 0

        Q1, Q2, Q3 = dfastmi_kernel.char_discharges(
            q_levels, dq, q_threshold, q_bankfull
        )

        Q1 = check_discharge(1, Q1)
        if Q1 is None:
            break
        if not Q2 is None:
            Q2 = check_discharge(2, Q2, stages[0], Q1)
            if Q2 is None:
                break
        if not Q3 is None:
            Q3 = check_discharge(3, Q3, stages[1], Q2)
            if Q3 is None:
                break

        tstag, t1, t2, t3, rsigma1, rsigma2, rsigma3 = dfastmi_kernel.char_times(
            q_fit, q_stagnant, Q1, Q2, Q3, celerity_hg, celerity_lw, nwidth
        )
        nlength = dfastmi_kernel.estimate_sedimentation_length(
            rsigma1, rsigma2, rsigma3, nwidth
        )
        nQ = countQ([Q1, Q2, Q3])

        if havefiles:
            # determine critical flow velocity
            ucritMin = 0.01
            log_text("", repeat=3)
            log_text("default_ucrit", dict={"uc": ucrit, "reach": reach})
            tdum = interactive_get_bool("confirm_or")
            if not tdum:
                ucrit = interactive_get_float("query_ucrit")
                if ucrit < ucritMin:
                    log_text("ucrit_too_low", dict={"uc": ucritMin})
                    log_text("ucrit_too_low", dict={"uc": ucritMin}, file=report)
                    ucrit = ucritMin
            log_text("", repeat=19)

            if not Q1 is None:
                dzq1, firstm, firstn = get_values(
                    1, Q1, ucrit, report, reduced_output, nargout=3
                )
                if dzq1 is None:
                    break
            else:
                dzq1 = 0
            if not Q2 is None:
                dzq2 = get_values(2, Q2, ucrit, report, reduced_output)
                if dzq2 is None:
                    break
            else:
                dzq2 = 0
            if not Q3 is None:
                dzq3 = get_values(3, Q3, ucrit, report, reduced_output)
                if dzq3 is None:
                    break
            else:
                dzq3 = 0
            log_text("char_bed_changes")
            data_zgem, data_z1o, data_z2o = dfastmi_kernel.main_computation(
                dzq1, dzq2, dzq3, tstag, t1, t2, t3, rsigma1, rsigma2, rsigma3
            )

            dfastmi_io.write_simona_box("jaargem.out", data_zgem, firstm, firstn)
            dfastmi_io.write_simona_box("maxmorf.out", data_z1o, firstm, firstn)
            dfastmi_io.write_simona_box("minmorf.out", data_z2o, firstm, firstn)

            log_text("")
            log_text("length_estimate", dict={"nlength": nlength})
            log_text("length_estimate", dict={"nlength": nlength}, file=report)
            tdum = interactive_get_bool("confirm_to_close")
            alldone = True
        else:
            log_text("---")
            if nQ == 1:
                log_text("need_single_input", dict={"reach": reach})
            else:
                log_text("need_multiple_input", dict={"reach": reach, "numq": nQ})
            if not Q1 is None:
                log_text("lowwater", dict={"border": q_location, "q": Q1})
            if not Q2 is None:
                log_text("transition", dict={"border": q_location, "q": Q2})
            if not Q3 is None:
                log_text("highwater", dict={"border": q_location, "q": Q3})
            log_text("length_estimate", dict={"nlength": nlength})
            log_text("---")
            log_text("canclose")
            alldone = interactive_get_bool("confirm_or_repeat")
            if alldone:
                write_report(report, reach, q_location, q_threshold, q_bankfull, tstag, qfit, [Q1, Q2, Q3], [t1, t2, t3], nlength)
            else:
                log_text("", repeat=10)
                log_text("===", file=report)
                log_text("repeat_input", file=report)
    log_text("end")
    log_text("end", file=report)
    report.close()
    
    
def countQ(Q):
    return sum([not q is None for q in Q])


def check_discharge(i, Q, pname="dummy", Qp=0):
    log_text("")
    log_text("input_avail", dict={"i": i, "q": Q})
    tdum = interactive_get_bool("confirm_or")
    if not tdum:
        while True:
            Q = interactive_get_float("query_qavail", dict={"i": i})
            if Q is None:
                break
            elif Q < Qp:
                log_text("")
                if i == 1:
                    log_text("qavail_too_small_1")
                else:
                    log_text(
                        "qavail_too_small_2",
                        dict={"p": i - 1, "pname": pname, "qp": Qp, "i": i},
                    )
            else:
                break
    return Q


def get_values(stage, q, ucrit, report, reduced_output, nargout=1):
    cblok = str(stage)
    log_text("input_xyz", dict={"stage": stage, "q": q})
    log_text("---")
    log_text("")

    discriptions = program_texts("file_descriptions")
    quantities = ["velocity-zeta.001", "waterdepth-zeta.001", "velocity-zeta.002"]
    files = []
    for i in range(3):
        log_text("input_xyz_name", dict={"name": discriptions[i]})
        cifil = "xyz_" + quantities[i] + ".Q" + cblok + ".xyz"
        logging.info(cifil)
        if not os.path.isfile(cifil):
            log_text("file_not_found", dict={"name": cifil}, file=report)
            return None
        else:
            log_text("input_xyz_found", dict={"name": cifil})
        files.extend([cifil])
        log_text("")

    log_text("input_xyz_read", dict={"stage": stage})
    u0temp = dfastmi_io.read_waqua_xyz(files[0], cols=(2, 3, 4))
    m = u0temp[:, 1].astype(int) - 1
    n = u0temp[:, 2].astype(int) - 1
    u0temp = u0temp[:, 0]
    h0temp = dfastmi_io.read_waqua_xyz(files[1])
    u1temp = dfastmi_io.read_waqua_xyz(files[2])

    if reduced_output:
        firstm = min(m)
        firstn = min(n)
    else:
        firstm = 0
        firstn = 0
    szm = max(m) + 1 - firstm
    szn = max(n) + 1 - firstn
    szk = szm * szn
    k = szn * m + n
    u0 = numpy.zeros([szk])
    h0 = numpy.zeros([szk])
    u1 = numpy.zeros([szk])

    u0[k] = u0temp
    h0[k] = h0temp
    u1[k] = u1temp

    sz = [szm, szn]
    u0 = u0.reshape(sz)
    h0 = h0.reshape(sz)
    u1 = u1.reshape(sz)

    dzq = dfastmi_kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
    log_text("---")
    if nargout == 3:
        return dzq, firstm, firstn
    else:
        return dzq


def interactive_get_bool(key, dict={}):
    log_text(key, dict=dict)
    str = sys.stdin.readline().lower()
    bool = str == "j\n" or str == "y\n"
    if bool:
        log_text("yes")
    else:
        log_text("no")
    return bool


def interactive_get_int(key, dict={}):
    log_text(key, dict=dict)
    str = sys.stdin.readline()
    logging.info(str)
    try:
        val = int(str)
    except:
        val = None
    return val


def interactive_get_float(key, dict={}):
    log_text(key, dict=dict)
    str = sys.stdin.readline()
    logging.info(str)
    try:
        val = float(str)
    except:
        val = None
    return val


def interactive_get_item(type, list):
    i = 0
    nitems = len(list)
    while i < 1 or i > nitems:
        log_text("query_" + type + "_header")
        for i in range(nitems):
            log_text("query_list", dict={"item": list[i], "index": i + 1})
        i = interactive_get_int("query_" + type)
        if i is None:
            return None
    return i - 1


def log_text(key, file=None, dict={}, repeat=1):
    str = program_texts(key)
    for r in range(repeat):
        if file is None:
            for s in str:
                logging.info(s.format(**dict))
        else:
            for s in str:
                file.write(s.format(**dict) + "\n")


def program_texts(key):
    try:
        str = PROGTEXTS[key]
    except:
        str = ["No message found for " + key]
    return str


def write_report(report, reach, q_location, q_threshold, q_bankfull, tstag, qfit, Q, t, nlength):
     log_text("", file=report)
     log_text("reach", dict={"reach": reach}, file=report)
     log_text("", file=report)
     if not q_threshold is None:
         log_text(
             "report_qthreshold",
             dict={"q": q_threshold, "border": q_location},
             file=report,
         )
     log_text(
         "report_qbankfull",
         dict={"q": q_bankfull, "border": q_location},
         file=report,
     )
     log_text("", file=report)
     if q_stagnant > q_fit[0]:
         log_text(
             "closed_barriers", dict={"ndays": int(tstag * 365)}, file=report
         )
         log_text("", file=report)
     for i in range(3):
         if not Q[i] is None:
             log_text(
                 "char_discharge",
                 dict={"n": i+1, "q": Q[i], "border": q_location},
                 file=report,
             )
             log_text(
                 "char_period", dict={"n": i+1, "ndays": int(t[i] * 365)}, file=report
             )
             if i < 2:
                 log_text("", file=report)
             else:
                 log_text("---", file=report)
     nQ = countQ(Q)
     if nQ == 1:
         log_text("need_single_input", dict={"reach": reach}, file=report)
     else:
         log_text(
             "need_multiple_input",
             dict={"reach": reach, "numq": nQ},
             file=report,
         )
     for i in range(3):
         if not Q[i] is None:
             log_text(
                 stagename(i), dict={"q": Q[i], "border": q_location}, file=report
             )
     log_text("---", file=report)
     log_text("length_estimate", dict={"nlength": nlength}, file=report)
     log_text("prepare_input", file=report)


def stagename(i):
    stagenames = ["lowwater", "transition", "highwater"]
    return stagenames[i]

def parse_arguments():
    parser = argparse.ArgumentParser(description="D-FAST Morphological Impact.")
    parser.add_argument("--reduced_output", dest="reduced_output", action="store_true")
    parser.set_defaults(reduced_output=False)
    args = parser.parse_args()

    reduced_output = args.__dict__["reduced_output"]
    return reduced_output


if __name__ == "__main__":
    reduced_output = parse_arguments()

    logging.basicConfig(level="INFO", format="%(message)s")

    if reduced_output:
        logging.info("option 'reduce_output' is active.")

    interactive_mode(reduced_output)
