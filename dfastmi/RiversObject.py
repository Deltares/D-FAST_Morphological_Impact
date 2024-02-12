from packaging import version
import configparser
from typing import Tuple, List, TypedDict, Optional
import zlib
from dfastmi.io import collect_int_values1, collect_values_logical, log_text 

class RiversObject(TypedDict, total=False):
    version: str
    branches: List[str]
    reaches: List[List[str]]
    qlocations: List[str]
    normal_width: List[List[float]]
    ucritical: List[List[float]]
    qstagnant: List[List[float]]
    tide: List[List[bool]]
    hydro_q: List[List[Tuple[float, ...]]]
    autotime: List[List[bool]]
    hydro_t: List[List[Tuple[float, ...]]]
    qfit: List[List[Tuple[float, float]]]
    tide_bc: List[List[Tuple[float, ...]]]
    cform: List[List[int]]
    cdisch: List[List[Tuple[float, float]]]
    prop_q: List[List[Tuple[float, ...]]]
    prop_c: List[List[Tuple[float, ...]]]
    proprate_high: List[List[float]] # only for version = 1
    proprate_low: List[List[float]] # only for version = 1
    qbankfull: List[List[float]] # only for version = 1
    qmin: List[List[float]] # only for version = 1
    qlevels: List[List[Tuple[float, float, float, float]]] # only for version = 1
    dq: List[List[Tuple[float, float]]] # only for version = 1

def read_rivers(filename: str = "rivers.ini") -> RiversObject:
    """
    Read a configuration file containing the river data.

    Read the configuration file containing the listing of various branches/reaches
    and their associated default parameter settings.

    Parameters
    ----------
    filename : str
        The name of the river configuration file (default "rivers.ini").

    Returns
    -------
    river_config : RiversObject
        A dictionary containing the river data.
    """
    branch: str
    branches: List[str]
    config: configparser.ConfigParser
    i: int
    name: str
    rivers: RiversObject

    # read the file
    config = configparser.ConfigParser()
    with open(filename, "r") as configfile:
        config.read_file(configfile)

    # initialize rivers dictionary
    try:
        file_version = config["General"]["Version"]
    except:
        raise Exception("No version information in the file {}!".format(filename))

    if version.parse(file_version) == version.parse("1"):
        iversion = 1
    elif version.parse(file_version) == version.parse("2"):
        iversion = 2
    else:
        raise Exception("Unsupported version number {} in the file {}!".format(file_version, filename))

    verify_checksum_rivers(config, filename)
    
    # parse branches
    branches = [k for k in config.keys()]
    branches.remove("DEFAULT")
    branches.remove("General")

    # parse reaches and discharge locations
    allreaches = []
    qlocations = []
    for branch in branches:
        qlocation = config[branch]["QLocation"]
        qlocations.extend([qlocation])

        i = 0
        reaches = []
        while True:
            i = i + 1
            try:
                reach = config[branch]["Reach" + str(i)]
                reaches.extend([reach])
            except:
                break
        allreaches.extend([reaches])

    # collect the values for all other quantities
    nreaches = [len(x) for x in allreaches]
    
    # call the specific reader for the file version
    if iversion == 1:
        rivers = read_rivers1(config, branches, allreaches, qlocations)
        
    else: # iversion == 2
        rivers = read_rivers2(config, branches, allreaches, qlocations)
    
    return rivers

def read_rivers1(config: configparser.ConfigParser, branches: List[str], allreaches: List[List[str]], qlocations: List[str]) -> RiversObject:
    """
    Read a configuration file containing the river data.

    Read the configuration file containing the listing of various branches/reaches
    and their associated default parameter settings.

    Parameters
    ----------
    filename : str
        The name of the river configuration file (default "rivers.ini").

    Returns
    -------
    river_config : RiversObject
        A dictionary containing the river data.
    """
    rivers : RiversObject = {}
    
    rivers["version"] = "1.0"
    rivers["branches"] = branches
    rivers["reaches"] = allreaches
    rivers["qlocations"] = qlocations
    
    nreaches = [len(x) for x in allreaches]

    rivers["normal_width"] = collect_values1(config, branches, nreaches, "NWidth")
    rivers["ucritical"] = collect_values1(config, branches, nreaches, "UCrit")
    rivers["qstagnant"] = collect_values1(config, branches, nreaches, "QStagnant")

    rivers["proprate_high"] = collect_values1(config, branches, nreaches, "PrHigh")
    rivers["proprate_low"] = collect_values1(config, branches, nreaches, "PrLow")
    rivers["qbankfull"] = collect_values1(config, branches, nreaches, "QBankfull")
    rivers["qmin"] = collect_values1(config, branches, nreaches, "QMin")
    rivers["qfit"] = collect_values2(config, branches, nreaches, "QFit")
    rivers["qlevels"] = collect_values4(config, branches, nreaches, "QLevels")
    rivers["dq"] = collect_values2(config, branches, nreaches, "dQ")
    
    return rivers
        
def read_rivers2(config: configparser.ConfigParser, branches: List[str], allreaches: List[List[str]], qlocations: List[str]) -> RiversObject:
    """
    Read a configuration file containing the river data.

    Read the configuration file containing the listing of various branches/reaches
    and their associated default parameter settings.

    Parameters
    ----------
    filename : str
        The name of the river configuration file (default "rivers.ini").

    Returns
    -------
    river_config : RiversObject
        A dictionary containing the river data.
    """
    rivers : RiversObject = {}
    
    rivers["version"] = "2.0"
    rivers["branches"] = branches
    rivers["reaches"] = allreaches
    rivers["qlocations"] = qlocations
    
    nreaches = [len(x) for x in allreaches]

    rivers["normal_width"] = collect_values1(config, branches, nreaches, "NWidth")
    rivers["ucritical"] = collect_values1(config, branches, nreaches, "UCrit")
    rivers["qstagnant"] = collect_values1(config, branches, nreaches, "QStagnant")

    rivers["hydro_q"] = collect_valuesN(config, branches, nreaches, "HydroQ")

    rivers["autotime"] = collect_values_logical(config, branches, nreaches, "AutoTime", False)
    # for AutoTime = True
    rivers["qfit"] = collect_values2(config, branches, nreaches, "QFit", (0.0, 0.0))
    # for AutoTime = False
    rivers["hydro_t"] = collect_valuesN(config, branches, nreaches, "HydroT")

    rivers["tide"] = collect_values_logical(config, branches, nreaches, "Tide", False)
    # for Tide = True
    rivers["tide_bc"] = collect_valuesN(config, branches, nreaches, "TideBC")

    rivers["cform"] = collect_int_values1(config, branches, nreaches, "CelerForm", 2)
    # for CelerForm = 1
    rivers["prop_q"] = collect_valuesN(config, branches, nreaches, "PropQ")
    rivers["prop_c"] = collect_valuesN(config, branches, nreaches, "PropC")
    # for CelerForm = 2
    rivers["cdisch"] = collect_values2(config, branches, nreaches, "CelerQ", (0.0, 0.0))
    
    # verify consistent length of hydro_q and hydro_t
    tup1: Tuple[float, ...]
    tup2: Tuple[float, ...]
    branches = rivers["branches"]
    for ib in range(len(branches)):
        reaches = rivers["reaches"][ib]
        for i in range(len(reaches)):
            tup1 = rivers["hydro_q"][ib][i]
            if rivers["autotime"][ib][i]:
                tup2 = rivers["qfit"][ib][i]
                if tup2 == (0.0, 0.0):
                    raise Exception(
                        'The parameter "QFit" must be specified for branch "{}", reach "{}" since "AutoTime" is set to True.'.format(
                            branches[ib],
                            reaches[i],
                        )
                    )
            else:
                tup2 = rivers["hydro_t"][ib][i]
                if len(tup1) != len(tup2):
                    raise Exception(
                        'Length of "HydroQ" and "HydroT" for branch "{}", reach "{}" are not consistent: {} and {} values read respectively.'.format(
                            branches[ib],
                            reaches[i],
                            len(tup1),
                            len(tup2),
                        )
                    )
            if rivers["tide"][ib][i]:
                tup2 = rivers["tide_bc"][ib][i]
                if len(tup1) != len(tup2):
                    raise Exception(
                        'Length of "HydroQ" and "TideBC" for branch "{}", reach "{}" are not consistent: {} and {} values read respectively.'.format(
                            branches[ib],
                            reaches[i],
                            len(tup1),
                            len(tup2),
                        )
                    )
            if rivers["cform"][ib][i] == 1:
                tup1 = rivers["prop_q"][ib][i]
                tup2 = rivers["prop_c"][ib][i]
                if len(tup1) != len(tup2):
                    raise Exception(
                        'Length of "PropQ" and "PropC" for branch "{}", reach "{}" are not consistent: {} and {} values read respectively.'.format(
                            branches[ib],
                            reaches[i],
                            len(tup1),
                            len(tup2),
                        )
                    )
                elif len(tup1) == 0:
                    raise Exception(
                        'The parameters "PropQ" and "PropC" must be specified for branch "{}", reach "{}" since "CelerForm" is set to 1.'.format(
                            branches[ib],
                            reaches[i],
                        )
                    )
            elif rivers["cform"][ib][i] == 2:
                tup2 = rivers["cdisch"][ib][i]
                if tup2 == (0.0, 0.0):
                    raise Exception(
                        'The parameter "CelerQ" must be specified for branch "{}", reach "{}" since "CelerForm" is set to 2.'.format(
                            branches[ib],
                            reaches[i],
                        )
                    )
                    
            else:
                raise Exception(
                    'Invalid value {} specified for "CelerForm" for branch "{}", reach "{}"; only 1 and 2 are supported.'.format(
                        rivers["cform"][ib][i],
                        branches[ib],
                        reaches[i],
                    )
                )
                

    return rivers

def verify_checksum_rivers(
    config: configparser.ConfigParser,
    filename: str,
):
    chapters = [k for k in config.keys()]
    checksum = ""
    checkval = 1
    for chapter in chapters:
        keys = [k for k in config[chapter].keys()]
        for key in keys:
            str = config[chapter][key]
            if chapter == "General" and key == "checksum":
                checksum = str
            else:
                checkval = zlib.adler32(str.encode("utf-8"), checkval) & 0xffffffff
    #print("Expected checksum: ", checkval)
    if checksum == "":
        log_text("checksum", dict = {"filename": filename})
    else:
        checkval2 = int(checksum)
        if checkval2 != checkval:
            raise Exception("Checksum mismatch: configuration file {} has been modified!".format(filename))

def collect_values1(
    config: configparser.ConfigParser,
    branches: List[str],
    nreaches: List[int],
    key: str,
    default: Optional[float] = None,
) -> List[List[float]]:
    """
    Collect river parameter data from river configuration object.

    This routines collects entries of type float.

    Arguments
    ---------
    config : configparser.ConfigParser
        The dictionary containing river data.
    branches : List[str]
        The list of river branches. The length of this list is nBranches.
    nreaches : List[int]
        The number of reaches per river branch. The length of this list is nBranches.
    key : str
        The name of the parameter for which the values are to be retrieved.

    Raises
    ------
    Exception
        If the number of values read from the file doesn't match 1.

    Returns
    -------
    data : List[List[float]]
        A list of lists. Each list contains per reach within the corresponding
        branch one float.
    """
    try:
        g_val = config["General"][key]
    except:
        g_val = ""

    all_values = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val

        values_per_branch = []
        for i in range(nreaches[ib]):
            stri = str(i + 1)
            try:
                val = config[branch][key + stri]
            except:
                val = b_val
            if val == "" and default is not None:
                fval = default
            else:
                try:
                    vals = tuple(float(x) for x in val.split())
                except:
                    vals = ()
                if len(vals) != 1:
                    raise Exception(
                        'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                            key, i+1, branches[ib], val, 1
                        )
                    )
                fval = vals[0]
            values_per_branch.append(fval)

        all_values.append(values_per_branch)

    return all_values
def collect_values2(
    config: configparser.ConfigParser,
    branches: List[str],
    nreaches: List[int],
    key: str,
    default: Optional[Tuple[float, float]] = None,
) -> List[List[Tuple[float, float]]]:
    """
    Collect river parameter data from river configuration object.

    This routines collects entries of type Tuple[float, float].

    Arguments
    ---------
    config : configparser.ConfigParser
        The dictionary containing river data.
    branches : List[str]
        The list of river branches. The length of this list is nBranches.
    nreaches : List[int]
        The number of reaches per river branch. The length of this list is nBranches.
    key : str
        The name of the parameter for which the values are to be retrieved.
    default : Optional[Tuple[float, float]]
        Default tuple if not specified in file.

    Raises
    ------
    Exception
        If the number of values read from the file doesn't match 2.

    Returns
    -------
    data : List[List[Tuple[float, float]]]
        A list of lists. Each list contains per reach within the corresponding
        branch a list of 2 floats.
    """
    vals: Tuple[float, ...]
    try:
        g_val = config["General"][key]
    except:
        g_val = ""
    all_values = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val
        values_per_branch = []
        for i in range(nreaches[ib]):
            stri = str(i + 1)
            try:
                val = config[branch][key + stri]
            except:
                val = b_val
            if val == "" and default is not None:
                vals = default
            else:
                try:
                    vals = tuple(float(x) for x in val.split())
                except:
                    vals = ()
                if len(vals) != 2:
                    raise Exception(
                        'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                            key, i+1, branches[ib], val, 2
                        )
                    )
            values_per_branch.append((vals[0], vals[1]))
        all_values.append(values_per_branch)
    return all_values
def collect_values4(
    config: configparser.ConfigParser,
    branches: List[str],
    nreaches: List[int],
    key: str,
    default: Optional[Tuple[float, float, float, float]] = None,
) -> List[List[Tuple[float, float, float, float]]]:
    """
    Collect river parameter data from river configuration object.

    This routines collects entries of type Tuple[float, float, float, float].

    Arguments
    ---------
    config : configparser.ConfigParser
        The dictionary containing river data.
    branches : List[str]
        The list of river branches. The length of this list is nBranches.
    nreaches : List[int]
        The number of reaches per river branch. The length of this list is nBranches.
    key : str
        The name of the parameter for which the values are to be retrieved.
    default : Optional[Tuple[float, float, float, float]]
        Default tuple if not specified in file.

    Raises
    ------
    Exception
        If the number of values read from the file doesn't match 4.

    Returns
    -------
    data : List[List[Tuple[float, float, float, float]]]
        A list of lists. Each list contains per reach within the corresponding
        branch a list of 4 floats.
    """
    vals: Tuple[float, ...]
    try:
        g_val = config["General"][key]
    except:
        g_val = ""
    all_values = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val
        values_per_branch = []
        for i in range(nreaches[ib]):
            stri = str(i + 1)
            try:
                val = config[branch][key + stri]
            except:
                val = b_val
            if val == "" and default is not None:
                vals = default
            else:
                try:
                    vals = tuple(float(x) for x in val.split())
                except:
                    vals = ()
                if len(vals) != 4:
                    raise Exception(
                        'Reading {} for reach {} on {} returns "{}". Expecting {} values.'.format(
                            key, i+1, branches[ib], val, 4
                        )
                    )
            values_per_branch.append((vals[0], vals[1], vals[2], vals[3]))
        all_values.append(values_per_branch)
    return all_values

def collect_valuesN(
    config: configparser.ConfigParser,
    branches: List[str],
    nreaches: List[int],
    key: str,
) -> List[List[Tuple[float, ...]]]:
    """
    Collect river parameter data from river configuration object.

    This routines collects entries of type Tuple[float, ...]

    Arguments
    ---------
    config : configparser.ConfigParser
        The dictionary containing river data.
    branches : List[str]
        The list of river branches. The length of this list is nBranches.
    nreaches : List[int]
        The number of reaches per river branch. The length of this list is nBranches.
    key : str
        The name of the parameter for which the values are to be retrieved.

    Returns
    -------
    data : List[List[Tuple[float, ...]]]
        A list of lists. Each list contains per reach within the corresponding
        branch a list of floats.
    """
    vals: Tuple[float, ...]
    try:
        g_val = config["General"][key]
    except:
        g_val = ""
    all_values = []
    for ib in range(len(branches)):
        branch = branches[ib]
        try:
            b_val = config[branch][key]
        except:
            b_val = g_val
        values_per_branch = []
        for i in range(nreaches[ib]):
            stri = str(i + 1)
            try:
                val = config[branch][key + stri]
            except:
                val = b_val
            vals = tuple(float(x) for x in val.split())
            values_per_branch.append(vals)
        all_values.append(values_per_branch)
    return all_values
