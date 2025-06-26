from pathlib import Path
from shapely import LineString
import numpy as np
from dfastrbk.src.batch.plotting import CrossFlow
from dfastrbk.src.kernel import flow
import dfastrbk.src.batch.dflowfm as dflowfm
import dfastrbk.src.config.config as config

def run(simulation_data: list, 
        variables,
        profiles_file: Path,
        riverkm: LineString,
        ship_params: config.Ship,
        invert_xaxis: bool):
    
    #TODO: loop over geom_idx
    geom_idx = 0
    transverse_velocity = []

    for data in simulation_data:
        #TODO: fix this
        
        profile_data, prof_line_df, rkm, segment_idx, face_idx = dflowfm.slice_simulation_data(data, 
                                                                        profiles_file,
                                                                        riverkm)
        angles = np.array(prof_line_df['angle'][geom_idx][segment_idx])
        cross_flow = flow.trans_velocity(profile_data[variables.ucx].values[face_idx], 
                        profile_data[variables.ucy].values[face_idx], 
                        angles)
        transverse_velocity.append(cross_flow)

    plotter = CrossFlow()
    plotter.create_figure(rkm, 
                            transverse_velocity, 
                            ship_params.depth,
                            ship_params.length,
                            invert_xaxis)