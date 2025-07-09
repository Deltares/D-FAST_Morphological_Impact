from collections import namedtuple
import numpy as np
from typing import Optional, NamedTuple
from xugrid import UgridDataset
import xugrid as xu
from tqdm import tqdm
import pandas as pd
from dfastrbk.src.config.config import Config
from dfastrbk.src.batch import cross_flow, ice, dflowfm
from dfastrbk.src.batch.plotting import Plot2D

def run(config_file: str, ships_file: Optional[str]) -> None:
    print("Running analysis...")

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
       
        varn_h = 'mesh2d_waterdepth'
        varn_bl = 'mesh2d_flowelem_bl'
        if 'time' in list(simulation_data[i].coords):
            simulation_data[i] = simulation_data[i].isel(time=-1)
            varn_ucx, varn_ucy = 'mesh2d_ucx', 'mesh2d_ucy'
            varn_uc = 'mesh2d_ucmag'
        else:
            varn_ucx, varn_ucy = 'mesh2d_last003', 'mesh2d_last004'
            varn_uc = 'mesh2d_last002'
            varn_H = 'mesh2d_last001'
            simulation_data[i][varn_h] = simulation_data[i][varn_H] - simulation_data[i][varn_bl]

    Variables = namedtuple('Variables', ['h', 'uc', 'ucx', 'ucy', 'bl'])
    variables = Variables(varn_h, varn_uc, varn_ucx, varn_ucy, varn_bl)

    if configuration.plottype == '1D':
        run_1d_analysis(configuration, simulation_data, variables)

    elif configuration.plottype == '2D':
        run_2d_analysis(configuration, simulation_data)
        
    elif configuration.plottype == 'both':
        run_1d_analysis(configuration, simulation_data, variables)
        run_2d_analysis(configuration, simulation_data)
    else:
        raise ValueError(f"Unknown plot type {configuration.plottype}.")
        
def run_1d_analysis(configuration: Config, 
                    simulation_data: list[UgridDataset], 
                    variables: NamedTuple):
    prof_line_df = dflowfm.read_profile_lines(configuration.profiles_file)
    riverkm_coords = np.array(configuration.riverkm.coords)
    bedlevel = simulation_data[-1][variables.bl]
    bedlevel_masked = bedlevel.where(bedlevel != 999)

    for geom_idx, profile_line in enumerate(tqdm(prof_line_df.geometry, desc="geometry")):
        profile_coords = np.array(profile_line.coords)
    
        profile_data = {}
        for variable, name in variables._asdict().items():
            profile_data[variable] = []

        for data in tqdm(simulation_data, desc = "simulation data", leave=False):
            for variable, name in variables._asdict().items():
                profile_dataset, rkm, segment_idx, face_idx = dflowfm.slice_ugrid(data, 
                                                                        profile_line,
                                                                        profile_coords,
                                                                         riverkm_coords)
                profile_angles = np.array(prof_line_df['angle'].iloc[geom_idx][segment_idx])
                profile_data[variable].append(dflowfm.get_profile_data(profile_dataset,name,face_idx))
    
        # ice.run_1d(profile_data["uc"],
        #             profile_data["ucx"],
        #             profile_data["ucy"],
        #             profile_angles,
        #             rkm,
        #             configuration.invertxaxis)
        
        # cross_flow.run(profile_data["ucx"],
        #                profile_data['ucy'],
        #                 profile_angles,
        #                 rkm,
        #                 configuration.ship_params,
        #                 configuration.invertxaxis)

        Plot2D().plot_profile_line(profile_line, 
                                   bedlevel_masked)

def run_2d_analysis(configuration: Config, 
                    simulation_data: list[UgridDataset],
                    variables: NamedTuple):
    ice.run_2d(simulation_data[0][variables.h], 
                simulation_data[0][variables.uc], 
                configuration.waterupliftcorrection, 
                configuration.bedchangecorrection,
                configuration.riverkm)

    water_depth = [simulation_data[0][variables.h],simulation_data[1][variables.h]]
    flow_velocity = [simulation_data[0][variables.uc],simulation_data[1][variables.uc]]
    ice.run_2d_diff(water_depth, 
                    flow_velocity, 
                    configuration.waterupliftcorrection, 
                    configuration.bedchangecorrection)
            