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
import sys
import os
import numpy
import dfastmi.io
import dfastmi.kernel
import configparser


def getfilename(key):
    filename = dfastmi.io.program_texts("filename_" + key)[0]
    return filename


def interactive_mode_opening(version, report):
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
            log_text("results_with_input", dict={"avgdzb": getfilename("avgdzb.out"), "maxdzb": getfilename("maxdzb.out"), "mindzb": getfilename("mindzb.out")})
        else:
            log_text("results_without_input")
        log_text("---")
        tdum = interactive_get_bool("confirm_or_restart")

    log_text("header", dict={"version": version}, file = report)
    log_text("limits", file = report)
    log_text("===", file = report)
    if havefiles:
        log_text("results_with_input", file = report, dict={"avgdzb": getfilename("avgdzb.out"), "maxdzb": getfilename("maxdzb.out"), "mindzb": getfilename("mindzb.out")})
    else:
        log_text("results_without_input", file = report)
    return havefiles


def interactive_get_location(rivers):
    branches = rivers["branches"]
    reaches = rivers["reaches"]

    ibranch = interactive_get_item("branch", branches)
    ireach = interactive_get_item("reach", reaches[ibranch])
    log_text("---")
    #branch = branches[ibranch]
    reach = reaches[ibranch][ireach]

    log_text("reach", dict={"reach": reach})
    log_text("---")
    accept = interactive_get_bool("confirm_location")
    if accept:
        return ibranch, ireach
    else:
        return None, None


def interactive_get_discharges(rivers, ibranch, ireach):
    stages = dfastmi.io.program_texts("stage_descriptions")

    q_location = rivers["qlocations"][ibranch]
    q_border = rivers["qbankfull"][ibranch][ireach]
    q_stagnant = rivers["qstagnant"][ibranch][ireach]
    q_min = rivers["qmin"][ibranch][ireach]
    q_fit = rivers["qfit"][ibranch][ireach]
    q_levels = rivers["qlevels"][ibranch][ireach]
    dq = rivers["dq"][ibranch][ireach]

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

    Q = dfastmi.kernel.char_discharges(
        q_levels, dq, q_threshold, q_bankfull
    )

    all_q = False
    Q[0] = check_discharge(1, Q[0])
    if not Q[0] is None and not Q[1] is None:
        Q[1] = check_discharge(2, Q[1], stages[0], Q[0])
        if not Q[1] is None and not Q[2] is None:
            Q[2] = check_discharge(3, Q[2], stages[1], Q[1])
            if not Q[2] is None:
                all_q = True
    return all_q, q_location, q_threshold, q_bankfull, q_fit, q_stagnant, Q


def batch_get_discharges(rivers, ibranch, ireach, config):
    stages = dfastmi.io.program_texts("stage_descriptions")

    q_location = rivers["qlocations"][ibranch]
    q_border = rivers["qbankfull"][ibranch][ireach]
    q_stagnant = rivers["qstagnant"][ibranch][ireach]
    q_fit = rivers["qfit"][ibranch][ireach]
    q_levels = rivers["qlevels"][ibranch][ireach]
    dq = rivers["dq"][ibranch][ireach]

    q_min = rivers["qmin"][ibranch][ireach]
    try:
        q_threshold = float(config["General"]["Qmin"])
    except:
        q_threshold = None

    if q_threshold is None or q_threshold < q_border:
        q_bankfull = float(config["General"]["Qbankfull"])
    else:
        q_bankfull = 0

    Q = dfastmi.kernel.char_discharges(
        q_levels, dq, q_threshold, q_bankfull
    )

    if not Q[0] is None:
        Q[0] = float(config["Q1"]["Discharge"])
    if not Q[1] is None:
        Q[1] = float(config["Q2"]["Discharge"])
    if not Q[2] is None:
        Q[2] = float(config["Q3"]["Discharge"])
    all_q = True
    return all_q, q_location, q_threshold, q_bankfull, q_fit, q_stagnant, Q


def get_filenames(mode, config = None):
    if mode == 0:
        filenames = []
    else:
        j = 0
        filenames = [""]*6
        for i in range(3):
            QSTR = "Q{}".format(i + 1)
            if QSTR in config:
                filenames[j] = config[QSTR]["Reference"]
                j += 1
                filenames[j] = config[QSTR]["WithMeasure"]
                j += 1
            else:
                j += 2
    return filenames


def analyse_and_report(mode, display, report, reduced_output, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit, filenames):
   if mode == 0:
       return analyse_and_report_waqua(display, report, reduced_output, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit)
   else:
       return analyse_and_report_dflowfm(display, report, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit, filenames)


def analyse_and_report_waqua(display, report, reduced_output, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit):
    missing_data = False
    if not Q[0] is None:
        dzq1, firstm, firstn = get_values(
            1, Q[0], ucrit, display, report, reduced_output, nargout=3
        )
        if dzq1 is None:
            missing_data = True
    else:
        dzq1 = 0
    if not missing_data and not Q[1] is None:
        dzq2 = get_values(2, Q[1], ucrit, display, report, reduced_output)
        if dzq2 is None:
            missing_data = True
    else:
        dzq2 = 0
    if not missing_data and not Q[2] is None:
        dzq3 = get_values(3, Q[2], ucrit, display, report, reduced_output)
        if dzq3 is None:
            missing_data = True
    else:
        dzq3 = 0
    
    if not missing_data:
        if display:
            log_text("char_bed_changes")
        data_zgem, data_z1o, data_z2o = dfastmi.kernel.main_computation(
            dzq1, dzq2, dzq3, tstag, T, rsigma
        )

        dfastmi.io.write_simona_box(getfilename("avgdzb.out"), data_zgem, firstm, firstn)
        dfastmi.io.write_simona_box(getfilename("maxdzb.out"), data_z1o, firstm, firstn)
        dfastmi.io.write_simona_box(getfilename("mindzb.out"), data_z2o, firstm, firstn)

    return missing_data


def analyse_and_report_dflowfm(display, report, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit, filenames):
    missing_data = False
    if not Q[0] is None:
        dzq1 = get_values_fm(1, Q[0], ucrit, report, filenames[0:2])
        if dzq1 is None:
            missing_data = True
    else:
        dzq1 = 0
    if not missing_data and not Q[1] is None:
        dzq2 = get_values_fm(2, Q[1], ucrit, report, filenames[2:4])
        if dzq2 is None:
            missing_data = True
    else:
        dzq2 = 0
    if not missing_data and not Q[2] is None:
        dzq3 = get_values_fm(3, Q[2], ucrit, report, filenames[4:6])
        if dzq3 is None:
            missing_data = True
    else:
        dzq3 = 0
    
    if not missing_data:
        if display:
            log_text("char_bed_changes")
        data_zgem, data_z1o, data_z2o = dfastmi.kernel.main_computation(
            dzq1, dzq2, dzq3, tstag, T, rsigma
        )

        meshname, facedim = dfastmi.io.get_mesh_and_facedim_names(filenames[0])
        dst = getfilename("netcdf.out")
        dfastmi.io.copy_ugrid(filenames[0], meshname, dst)
        dfastmi.io.ugrid_add(dst, "avgdzb", data_zgem, meshname, facedim, long_name = "year-averaged change without dredging", units = "m")
        dfastmi.io.ugrid_add(dst, "maxdzb", data_z1o , meshname, facedim, long_name = "maximum change after flood without dredging", units = "m")
        dfastmi.io.ugrid_add(dst, "mindzb", data_z2o , meshname, facedim, long_name = "minimum change after low flow without dredging", units = "m")

    return missing_data


def write_report_nodata(report, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, nlength):
    log_text("---")
    nQ = countQ(Q)
    if nQ == 1:
        log_text("need_single_input", dict={"reach": reach})
    else:
        log_text("need_multiple_input", dict={"reach": reach, "numq": nQ})
    if not Q[0] is None:
        log_text("lowwater", dict={"border": q_location, "q": Q[0]})
    if not Q[1] is None:
        log_text("transition", dict={"border": q_location, "q": Q[1]})
    if not Q[2] is None:
        log_text("highwater", dict={"border": q_location, "q": Q[2]})
    log_text("length_estimate", dict={"nlength": nlength})
    log_text("---")
    log_text("canclose")
    alldone = interactive_get_bool("confirm_or_repeat")
    if alldone:
        write_report(report, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, nlength)
    else:
        log_text("", repeat=10)
        log_text("===", file = report)
        log_text("repeat_input", file = report)
    return alldone


def interactive_mode(rivers, reduced_output):
    if reduced_output:
        log_text("reduce_output")

    report = open(getfilename("report.out"), "w")
    
    version = dfastmi.__version__
    havefiles = interactive_mode_opening(version, report)

    alldone = False
    while not alldone:
        ibranch = None
        while ibranch is None:
            ibranch, ireach = interactive_get_location(rivers)
        
        all_q, q_location, q_threshold, q_bankfull, q_fit, q_stagnant, Q = interactive_get_discharges(rivers, ibranch, ireach)
        if not all_q:
            break
        
        celerity_hg = rivers["proprate_high"][ibranch][ireach]
        celerity_lw = rivers["proprate_low"][ibranch][ireach]
        nwidth = rivers["normal_width"][ibranch][ireach]

        tstag, T, rsigma = dfastmi.kernel.char_times(
            q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
        )
        nlength = dfastmi.kernel.estimate_sedimentation_length(
            rsigma, nwidth
        )

        reach = rivers["reaches"][ibranch][ireach]
        if havefiles:
            # determine critical flow velocity
            ucrit = rivers["ucritical"][ibranch][ireach]
            ucritMin = 0.01
            log_text("", repeat=3)
            log_text("default_ucrit", dict={"uc": ucrit, "reach": reach})
            tdum = interactive_get_bool("confirm_or")
            if not tdum:
                ucrit = interactive_get_float("query_ucrit")
                if ucrit < ucritMin:
                    log_text("ucrit_too_low", dict={"uc": ucritMin})
                    log_text("ucrit_too_low", dict={"uc": ucritMin}, file = report)
                    ucrit = ucritMin

            log_text("", repeat=19)
            filenames = get_filenames(0)
            missing_data = analyse_and_report(0, True, report, reduced_output, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit, filenames)
            if not missing_data:
                log_text("")
                log_text("length_estimate", dict={"nlength": nlength})
                log_text("length_estimate", dict={"nlength": nlength}, file = report)
                tdum = interactive_get_bool("confirm_to_close")
            alldone = True
        else:
            alldone = write_report_nodata(report, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, nlength)

    log_text("end")
    log_text("end", file = report)
    report.close()


def batch_mode_core(rivers, reduced_output, config):
    report = open(getfilename("report.out"), "w")

    version = dfastmi.__version__
    log_text("header", dict={"version": version}, file = report)
    log_text("limits", file = report)
    log_text("===", file = report)

    branch = config["General"]["Branch"]
    try:
        ibranch = rivers["branches"].index(branch)
    except:
        log_text("invalid_branch", dict={"branch": branch}, file = report)
        failed = True
    else:
        reach = config["General"]["Reach"]
        try:
            ireach = rivers["reaches"][ibranch].index(reach)
        except:
            log_text("invalid_reach", dict={"reach": reach, "branch": branch}, file = report)
            failed = True
        else:
            all_q, q_location, q_threshold, q_bankfull, q_fit, q_stagnant, Q = batch_get_discharges(rivers, ibranch, ireach, config)

            celerity_hg = rivers["proprate_high"][ibranch][ireach]
            celerity_lw = rivers["proprate_low"][ibranch][ireach]
            nwidth = rivers["normal_width"][ibranch][ireach]

            tstag, T, rsigma = dfastmi.kernel.char_times(
                q_fit, q_stagnant, Q, celerity_hg, celerity_lw, nwidth
            )
            nlength = dfastmi.kernel.estimate_sedimentation_length(
                rsigma, nwidth
            )

            reach = rivers["reaches"][ibranch][ireach]
            ucrit = rivers["ucritical"][ibranch][ireach]
            if config["General"]["Mode"] == "WAQUA export":
                mode = 0
                log_text("results_with_input_waqua", file = report, dict={"avgdzb": getfilename("avgdzb.out"), "maxdzb": getfilename("maxdzb.out"), "mindzb": getfilename("mindzb.out")})
            else:
                mode = 1
                log_text("results_with_input_dflowfm", file = report, dict={"netcdf": getfilename("netcdf.out")})
            filenames = get_filenames(mode, config)
            failed = analyse_and_report(mode, False, report, reduced_output, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, T, rsigma, nlength, ucrit, filenames)
            log_text("length_estimate", dict={"nlength": nlength}, file = report)

    log_text("end", file = report)
    report.close()
    return failed


def batch_mode(rivers, reduced_output, config_file):
    if reduced_output:
        log_text("reduce_output")
    
    try:
        config = load_configuration_file(config_file)
    except:
        print(sys.exc_info()[1])
    else:
        batch_mode_core(rivers, reduced_output, config_file)


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


def get_values(stage, q, ucrit, display, report, reduced_output, nargout=1):
    cblok = str(stage)
    if display:
        log_text("input_xyz", dict={"stage": stage, "q": q})
        log_text("---")
        log_text("")

    discriptions = dfastmi.io.program_texts("file_descriptions")
    quantities = ["velocity-zeta.001", "waterdepth-zeta.001", "velocity-zeta.002"]
    files = []
    for i in range(3):
        if display:
            log_text("input_xyz_name", dict={"name": discriptions[i]})
        cifil = "xyz_" + quantities[i] + ".Q" + cblok + ".xyz"
        if display:
            logging.info(cifil)
        if not os.path.isfile(cifil):
            log_text("file_not_found", dict={"name": cifil}, file = report)
            log_text("end_program", file = report)
            if nargout == 3:
                return None, None, None
            else:
                return None
        else:
            if display:
                log_text("input_xyz_found", dict={"name": cifil})
        files.extend([cifil])
        if display:
            log_text("")

    if display:
        log_text("input_xyz_read", dict={"stage": stage})
    u0temp = dfastmi.io.read_waqua_xyz(files[0], cols=(2, 3, 4))
    m = u0temp[:, 1].astype(int) - 1
    n = u0temp[:, 2].astype(int) - 1
    u0temp = u0temp[:, 0]
    h0temp = dfastmi.io.read_waqua_xyz(files[1])
    u1temp = dfastmi.io.read_waqua_xyz(files[2])

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

    dzq = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
    log_text("---")
    if nargout == 3:
        return dzq, firstm, firstn
    else:
        return dzq


def get_values_fm(stage, q, ucrit, report, filenames):
    cblok = str(stage)

    # reference file
    if filenames[0] == "":
        log_text("no_file_specified", dict={"q": q}, file = report)
        log_text("end_program", file = report)
        return None
    elif not os.path.isfile(filenames[0]):
        log_text("file_not_found", dict={"name": filenames[0]}, file = report)
        log_text("end_program", file = report)
        return None
    else:
        u = dfastmi.io.read_fm_map(filenames[0], "sea_water_x_velocity")
        v = dfastmi.io.read_fm_map(filenames[0], "sea_water_x_velocity")
        u0 = numpy.sqrt(u**2 + v**2)
        h0 = dfastmi.io.read_fm_map(filenames[0], "sea_floor_depth_below_sea_surface")

    # with measure
    if not os.path.isfile(filenames[1]):
        log_text("file_not_found", dict={"name": filenames[1]}, file = report)
        log_text("end_program", file = report)
        return None
    else:
        u = dfastmi.io.read_fm_map(filenames[1], "sea_water_x_velocity")
        v = dfastmi.io.read_fm_map(filenames[1], "sea_water_x_velocity")
        u1 = numpy.sqrt(u**2 + v**2)

    dzq = dfastmi.kernel.dzq_from_du_and_h(u0, h0, u1, ucrit)
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
    str = dfastmi.io.program_texts(key)
    for r in range(repeat):
        if file is None:
            for s in str:
                logging.info(s.format(**dict))
        else:
            for s in str:
                file.write(s.format(**dict) + "\n")


def write_report(report, reach, q_location, q_threshold, q_bankfull, tstag, q_fit, Q, t, nlength):
     log_text("", file = report)
     log_text("reach", dict={"reach": reach}, file = report)
     log_text("", file = report)
     if not q_threshold is None:
         log_text(
             "report_qthreshold",
             dict={"q": q_threshold, "border": q_location},
             file = report,
         )
     log_text(
         "report_qbankfull",
         dict={"q": q_bankfull, "border": q_location},
         file = report,
     )
     log_text("", file = report)
     if q_stagnant > q_fit[0]:
         log_text(
             "closed_barriers", dict={"ndays": int(tstag * 365)}, file = report
         )
         log_text("", file = report)
     for i in range(3):
         if not Q[i] is None:
             log_text(
                 "char_discharge",
                 dict={"n": i+1, "q": Q[i], "border": q_location},
                 file = report,
             )
             log_text(
                 "char_period", dict={"n": i+1, "ndays": int(t[i] * 365)}, file = report
             )
             if i < 2:
                 log_text("", file = report)
             else:
                 log_text("---", file = report)
     nQ = countQ(Q)
     if nQ == 1:
         log_text("need_single_input", dict={"reach": reach}, file = report)
     else:
         log_text(
             "need_multiple_input",
             dict={"reach": reach, "numq": nQ},
             file = report,
         )
     for i in range(3):
         if not Q[i] is None:
             log_text(
                 stagename(i), dict={"q": Q[i], "border": q_location}, file = report
             )
     log_text("---", file = report)
     log_text("length_estimate", dict={"nlength": nlength}, file = report)
     log_text("prepare_input", file = report)


def absolute_path(rootdir, file):
    if file == "":
        return file
    else:
        try:
            return os.path.normpath(os.path.join(rootdir, file))
        except:
            return file


def config_to_absolute_paths(filename, config):
    rootdir = os.path.dirname(filename)
    for q in range(3):
        QSTR = "Q{}".format(q + 1)
        if QSTR in config:
            if "Reference" in config[QSTR]:
                config[QSTR]["Reference"] = absolute_path(rootdir, config[QSTR]["Reference"])
            if "WithMeasures" in config[QSTR]:
                config[QSTR]["WithMeasure"] = absolute_path(rootdir, config[QSTR]["WithMeasure"])
    return config


def load_configuration_file(filename = None):
    config = configparser.ConfigParser()
    with open(filename, "r") as configfile:
        config.read_file(configfile)
    try:
        version = config["General"]["Version"]
    except:
        raise Exception("No version information in the file!")

    if version == "1.0":
        section = config["General"]
        branch = section["Branch"]
        reach = section["Reach"]
    else:
        raise Exception("Unsupported version number {} in the file!".format(version))
    
    return config_to_absolute_paths(filename, config)


def relative_path(rootdir, file):
    if file == "":
        return file
    else:
        try:
            rfile = os.path.relpath(file, rootdir) 
            return rfile
        except:
            return file


def config_to_relative_paths(filename, config):
    rootdir = os.path.dirname(filename)
    for q in range(3):
        QSTR = "Q{}".format(q + 1)
        if QSTR in config:
            if "Reference" in config[QSTR]:
                config[QSTR]["Reference"] = relative_path(rootdir, config[QSTR]["Reference"])
            if "WithMeasure" in config[QSTR]:
                config[QSTR]["WithMeasure"] = relative_path(rootdir, config[QSTR]["WithMeasure"])
    return config


def save_configuration_file(filename: str, config):
    config = config_to_relative_paths(filename, config)
    dfastmi.io.write_config(filename, config)


def stagename(i):
    stagenames = ["lowwater", "transition", "highwater"]
    return stagenames[i]
