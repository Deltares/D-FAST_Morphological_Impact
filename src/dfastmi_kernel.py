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
import math
import numpy
from configparser import ConfigParser


def program_version():
    return 'PRE-ALPHA'


def main_program(input_file):
    # Report program name and version
    program_header()

    # Reading configuration file
    config = read_config(input_file)
    verify_config(config,input_file)

    # Running analysis
    results = run_analysis(config)

    # Writing results
    write_results(results)

    # Finished
    logging.info('Finished')


def program_header():
    logging.critical('D-FAST Morphological Impact '+program_version())
    logging.critical('Copyright (c) 2020 Deltares.')
    logging.critical('')
    logging.critical('This program is distributed under the terms of the')
    logging.critical('GNU Lesser General Public License Version 2.1; see')
    logging.critical('the LICENSE.md file for details.')
    logging.critical('')
    logging.info('Source code location:')
    logging.info('https://github.com/Deltares/D-FAST_Morphological_Impact')
    logging.info('')


def read_config(input_file):
    logging.info('Reading configuration file '+input_file)

    # instantiate file parser
    config = ConfigParser()

    # open the configuration file
    fid = open(input_file,'r')

    # read and parse the configuration file
    config.read_file(fid)

    # close the configuration file
    fid.close()
    return config


def logkeyvalue(level,key,val):
    logging.log(level,str.format('%-30s: %s' % (key,val)))


def verify_config(config,input_file):
    logging.info('Verifying configuration file')
    try:
        filename = config['General']['File1']
        logkeyvalue(logging.DEBUG,'Simulation without measure',filename)
    except:
        raise SystemExit('Unable to read General\File1 from "'+input_file+'"!')
    try:
        filename = config['General']['File2']
        logkeyvalue(logging.DEBUG,'Simulation with measure',filename)
    except:
        raise SystemExit('Unable to read General\File2 from "'+input_file+'"!')
    logging.debug('')
    return


def read_dflowfm(map_file):
    logging.debug('Loading file "'+map_file+'"')
    data = 1
    return data


def run_analysis(config):
    # Load data
    logging.info('Loading data')
    data1 = read_dflowfm(config['General']['File1'])
    data2 = read_dflowfm(config['General']['File2'])
    logging.debug('')

    # Do actual analysis
    logging.info('Running analysis')
    logging.debug('')
    return 0


def write_results(results):
    logging.info('Writing results')
    logging.debug('')


def char_discharge(jtak, jstuk, q_threshold, q_bankfull):
    if jtak == 4: # Maas
        q_stagnant = 1000
    elif jtak == 1 and jstuk > 0: # stuwpanden Nederrijn en Lek
        q_stagnant = 1500
    else:
        q_stagnant = 800

    if jtak == 4: # Maas
        Q1, Q2, Q3 = char_discharges_maas(q_stagnant, q_threshold, q_bankfull)
    else:
        Q1, Q2, Q3 = char_discharges_rijntakken(q_stagnant, q_threshold, q_bankfull)

    return q_stagnant, Q1, Q2, Q3


def char_times(jtak, jstuk, q_stagnant, Q1, Q2, Q3, proprate_hg, proprate_lw, nwidth):
    if jtak == 4: # Maas
        Qa = 0
        Qb = 300
    else:
        Qa = 800
        Qb = 1280

    if jtak == 4 or (jtak == 1 and jstuk > 0): # Maas or stuwpanden Nederrijn en Lek
        t_stagnant = 1 - math.exp((Qa-q_stagnant)/Qb)
    else:
        t_stagnant = 0

    t1 = 1 - math.exp((Qa-Q1)/Qb) - t_stagnant
    if Q2 is None:
        t2 = 0
    else:
        t2 = math.exp((Qa-Q1)/Qb) - math.exp((Qa-Q2)/Qb)
    t3 = max(1-t1-t2-t_stagnant, 0) # math.exp((Qa-Q2)/Qb)

    rsigma1 = math.exp(-500*proprate_lw*t1/nwidth)
    if not Q2 is None:
        rsigma2 = math.exp(-500*proprate_hg*t2/nwidth)
    else:
        rsigma2 = 1
    if not Q3 is None:
        rsigma3 = math.exp(-500*proprate_hg*t3/nwidth)
    else:
        rsigma3 = 1

    return t_stagnant, t1, t2, t3, rsigma1, rsigma2, rsigma3


def char_discharges_rijntakken(q_stagnant, q_threshold, q_bankfull):
    if not q_threshold is None: # has threshold discharge
        Q1      = q_threshold
        if q_threshold < 3000:
            if q_bankfull < 6000:
                Q2 = max(q_bankfull, Q1+1000)
                Q3 = max(6000, Q2+1000)
            else:
                Q2 = 4000
                Q3 = q_bankfull
        elif q_threshold < 4000:
            Q2      = max(q_bankfull, q_threshold+1000)
            Q3      = 6000
        else: # q_threshold >= 4000
            Q2      = None
            if q_threshold > 6000:
                Q3   = min(q_threshold+1000, 10000)
            else:
                Q3   = max(6000, q_threshold+1000)
    else: # no threshold discharge
        Q1      = 3000
        if q_bankfull < 6000:
            Q2 = max(4000, q_bankfull)
            Q3 = 6000
        else:
            Q2 = min(4000, q_bankfull-1000)
            Q3 = q_bankfull

    return Q1, Q2, Q3

def char_discharges_maas(q_stagnant, q_threshold, q_bankfull):
    if not q_threshold is None: # has threshold discharge
        Q1      = q_threshold
        if q_threshold < 1250:
            if q_bankfull < 2000:
                Q2 = max(q_bankfull, q_threshold+250)
                Q3 = max(2000, Q2+250)
            else:
                Q2 = 1500
                Q3 = q_bankfull
        else:
            if q_threshold < 1500:
                Q2      = max(q_bankfull, q_threshold+250)
                Q3      = 2000
            else:
                Q2      = None
                if q_threshold > 2000:
                    Q3   = min(q_threshold+200, 3000)
                else:
                    Q3   = max(2000, q_threshold+200)
    else: # no threshold discharge
        Q1      = 1250
        if q_bankfull < 2000:
            Q2 = max(1500, q_bankfull)
            Q3 = 2000
        else:
            Q2 = min(1500, q_bankfull-250)
            Q3 = q_bankfull
        if Q2 == Q3:
           Q3 = None
        if Q1 == Q2:
            Q2 = None

    return Q1, Q2, Q3


def estimate_sedimentationlength(rsigma1, rsigma2, rsigma3, nwidth):
    length = - math.log(rsigma1) - math.log(rsigma2) - math.log(rsigma3)
    return int(2 * nwidth * length)


def dzq_from_du_and_h(u0, h0, u1, ucrit):
    with numpy.errstate(divide='ignore', invalid='ignore'):
        dzq = numpy.where((abs(u0)>ucrit) & (abs(u1)>ucrit) & (abs(u0)<100), h0*(u0-u1)/u0, numpy.NaN)
    return dzq



def main_computation(dzq1, dzq2, dzq3, tstag, t1, t2, t3, rsigma1, rsigma2, rsigma3):
    mask = numpy.isnan(dzq1) | numpy.isnan(dzq2) | numpy.isnan(dzq3)
    sz = numpy.shape(dzq1)
    rsigma1l = numpy.ones(sz)*rsigma1
    rsigma2l = numpy.ones(sz)*rsigma2
    rsigma3l = numpy.ones(sz)*rsigma3
    rsigma1l[mask] = 1
    rsigma2l[mask] = 1
    rsigma3l[mask] = 1

    den  = 1-rsigma1l*rsigma2l*rsigma3l

    zmbb = (dzq1 * (1-rsigma1l) * rsigma2l * rsigma3l
            + dzq2 * (1-rsigma2l) * rsigma3l
            + dzq3 * (1-rsigma3l))

    with numpy.errstate(divide='ignore', invalid='ignore'):
        z1o  = numpy.where(den != 0,
                           (dzq1 * (1-rsigma1l) * rsigma2l * rsigma3l
                            + dzq2 * (1-rsigma2l) * rsigma3l
                            + dzq3 * (1-rsigma3l)
                           )/den,
                           0)

        z2o  = numpy.where(den != 0,
                           (dzq1 * (1-rsigma1l)
                            + dzq2 * (1-rsigma2l) * rsigma3l * rsigma1l
                            + dzq3 * (1-rsigma3l) * rsigma1l
                           )/den,
                           0)

        z3o  = numpy.where(den != 0,
                           (dzq1 * (1-rsigma1l) * rsigma2l
                            + dzq2 * (1-rsigma2l)
                            + dzq3 * (1-rsigma3l) * rsigma1l * rsigma2l
                           )/den,
                           0)

    zgem = z1o * (t1+t3)/2 + z2o * ((t2+t1)/2+tstag) + z3o*(t3+t2)/2

    return zgem, z1o, z2o
