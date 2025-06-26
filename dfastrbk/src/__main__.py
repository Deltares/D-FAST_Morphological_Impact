from collections import namedtuple
from xugrid import UgridDataset
import argparse
import xugrid as xu
from dfastrbk.src.config.config import Config
from dfastrbk.src.batch import cross_flow, ice
#import dfastmi.batch.core

def parse_arguments() -> tuple:
    """
    Parse the command line arguments.

    Arguments
    ---------
    None

    Returns
    -------
    config_name : Optional[str]
        Name of the analysis configuration file.
    rivers_file : str
        Name of rivers configuration file.
    """

    parser = argparse.ArgumentParser(description="D-FAST Ice/Cross-flow")

    parser.add_argument(
        "--config",
        default="dfastmi.cfg",
        help="name of analysis configuration file ('%(default)s' is default)",
    )

    parser.add_argument(
        "--rivers",
        default="unspecified",
        help="name of rivers configuration file ('Dutch_rivers_v3.ini' is default)",
    )

    parser.set_defaults(reduced_output=False)
    args = parser.parse_args()

    config_file = args.__dict__["config"]
    rivers_file = args.__dict__["rivers"]
    if rivers_file == "unspecified":
        rivers_file = "Dutch_rivers_v3.ini"

    return config_file, rivers_file

# # if __name__ == "__main__":
# #     config_file, rivers_file = parse_arguments()
# #     core.run(config_file, rivers_file)

def main() -> None:

    #TODO: implement for loop for each simulation / section
    CASE: str = 'c02 - Maas'
    SECTION: str = 'C1'
    configuration = Config(CASE, SECTION)

    #TODO: replace by d-fast-mi io
    simulation_data: list[UgridDataset] = []
    for i, file in enumerate(configuration.output_files):
        simulation_data.append(xu.open_dataset(file))

        if hasattr(configuration,'bbox'):
            x_slice = slice(configuration.bbox[0],configuration.bbox[1])
            y_slice = slice(configuration.bbox[2],configuration.bbox[3])
            simulation_data[i] = simulation_data[i].ugrid.sel(x=x_slice,y=y_slice)
        
        if 'time' in list(simulation_data[i].coords):
            simulation_data[i] = simulation_data[i].isel(time=-1)
            varn_ucx, varn_ucy = 'mesh2d_ucx', 'mesh2d_ucy'
            varn_uc = 'mesh2d_ucmag'
            varn_h = 'mesh2d_waterdepth'
        else:
            varn_ucx, varn_ucy = 'mesh2d_last003', 'mesh2d_last004'
            varn_uc = 'mesh2d_last002'

    Variables = namedtuple('Variables', ['h', 'uc', 'ucx', 'ucy'])
    variables = Variables(varn_h, varn_uc, varn_ucx, varn_ucy)

    ### Ice:
    # 1D:
    # ice.run_1d(simulation_data, 
    #            variables, 
    #            configuration.profiles_file, 
    #            configuration.riverkm, 
    #            configuration.invert_xaxis)

    ## 2D:
    # ice.run_2d(simulation_data[0][variables.h], 
    #            simulation_data[0][variables.uc], 
    #            configuration.water_uplift_correction, 
    #            configuration.bed_change_correction,
    #            configuration.riverkm)

    # water_depth = [simulation_data[0][variables.h],simulation_data[1][variables.h]]
    # flow_velocity = [simulation_data[0][variables.uc],simulation_data[1][variables.uc]]
    # ice.run_2d_diff(water_depth, 
    #                 flow_velocity, 
    #                 configuration.water_uplift_correction, 
    #                 configuration.bed_change_correction)
    
    ### Cross flow:
    cross_flow.run(simulation_data, 
                   variables, 
                   configuration.profiles_file,
                   configuration.riverkm,
                   configuration.ship_params,
                   configuration.invert_xaxis)

if __name__ == "__main__":
    main()