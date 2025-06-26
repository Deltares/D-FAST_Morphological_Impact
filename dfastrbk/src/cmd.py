from collections import namedtuple
from typing import Optional
from xugrid import UgridDataset
import xugrid as xu
from dfastrbk.src.config.config import Config
from dfastrbk.src.batch import cross_flow, ice

def run(config_file: str, ships_file: Optional[str]) -> None:

    #TODO: implement for loop for each simulation / section
    SECTION: str = 'C1'
    configuration = Config(config_file, SECTION, ships_file)

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

    ## Ice:
    #1D:
    # ice.run_1d(simulation_data, 
    #            variables, 
    #            configuration.profiles_file, 
    #            configuration.riverkm, 
    #            invertxaxis)

    ## 2D:
    ice.run_2d(simulation_data[0][variables.h], 
               simulation_data[0][variables.uc], 
               configuration.waterupliftcorrection, 
               configuration.bedchangecorrection,
               configuration.riverkm)

    # water_depth = [simulation_data[0][variables.h],simulation_data[1][variables.h]]
    # flow_velocity = [simulation_data[0][variables.uc],simulation_data[1][variables.uc]]
    # ice.run_2d_diff(water_depth, 
    #                 flow_velocity, 
    #                 configuration.water_uplift_correction, 
    #                 configuration.bed_change_correction)
    
    # ### Cross flow:
    # cross_flow.run(simulation_data, 
    #             variables, 
    #             configuration.profiles_file,
    #             configuration.riverkm,
    #             configuration.ship_params,
    #             invertxaxis)