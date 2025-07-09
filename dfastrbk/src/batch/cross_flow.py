import numpy as np
from dfastrbk.src.batch import plotting
from dfastrbk.src.kernel import flow
from dfastrbk.src.config import config

def run(ucx: list[np.ndarray],
        ucy: list[np.ndarray],
        profile_angles: np.ndarray,
        rkm: np.ndarray,
        ship_params: config.Ship,
        invert_xaxis: bool) -> None:

    transverse_velocity = []
    for x, y in zip(ucx,ucy):
        cross_flow = flow.trans_velocity(x, y, profile_angles)
        transverse_velocity.append(cross_flow)

    plotter = plotting.CrossFlow()
    plotter.create_figure(rkm, 
                            transverse_velocity, 
                            ship_params.depth,
                            ship_params.length,
                            invert_xaxis)