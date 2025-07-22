from pathlib import Path
import numpy as np
from dfastrbk.src.batch import plotting
from dfastrbk.src.kernel import flow
from dfastrbk.src.config import Config
from dfastrbk.src.batch import support

def run(ucx: list[np.ndarray],
        ucy: list[np.ndarray],
        profile_angles: np.ndarray,
        rkm: np.ndarray,
        configuration: Config,
        figfile: Path,
        outputfile: Path) -> None:

    COLUMN_LABELS = ('afstand (rkm)',
                    'dwarsstroomsnelheid (m/s)')
    
    rkm_km = rkm / 1000
    transverse_velocity = []
    for x, y in zip(ucx,ucy):
        cross_flow = flow.trans_velocity(x, y, profile_angles)
        transverse_velocity.append(cross_flow)
    
        support.to_csv(outputfile,
                    COLUMN_LABELS,
                    rkm_km,
                    transverse_velocity[0])
    
    plotter = plotting.CrossFlow()
    plotter.create_figure(rkm,
                            transverse_velocity,
                            configuration.ship_params.depth,
                            configuration.ship_params.length,
                            configuration.general.bool_flags['invertxaxis'],
                            figfile)