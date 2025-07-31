from pathlib import Path
import numpy as np
import pandas as pd
from dfastrbk.src.batch import plotting
from dfastrbk.src.kernel import flow
from dfastrbk.src.config import Config
from dfastrbk.src.batch import support
from dfastrbk.src.batch import operations

def run(ucx: list[np.ndarray],
        ucy: list[np.ndarray],
        profile_angles: np.ndarray,
        rkm: np.ndarray,
        configuration: Config,
        figfile: Path,
        outputfiles: Path) -> None:
    
    SHEET_LABELS = ["Reference","WithIntervention","Difference"]
    CRITERIA: tuple[float, float] = (0.15, 0.3)  # criteria for transverse velocity

    rkm_km = rkm / 1000
    
    # Transverse velocity:
    COLUMN_LABELS = ('afstand (rkm)',
                    'dwarsstroomsnelheid (m/s)')
    transverse_velocity = []
    for x, y in zip(ucx, ucy):
        cross_flow = flow.trans_velocity(x, y, profile_angles)
        transverse_velocity.append(cross_flow.compute())

    data = [transverse_velocity[0],
            transverse_velocity[1] 
            if len(transverse_velocity) > 1 else None,
            transverse_velocity[1] - transverse_velocity[0]
            if len(transverse_velocity) > 1 else None]
    
    with pd.ExcelWriter(outputfiles[0]) as writer:
        for label, d in zip(SHEET_LABELS, data):
            if d is not None:
                support.to_excel(
                    writer,
                    COLUMN_LABELS,
                    label,
                    rkm_km,
                    d
                )
            
    # Transverse discharge:
    COLUMN_LABELS = ('start (rkm)',
                     'eind (rkm)',
                    'dwarsstroomdebiet (m3/s)',
                    'max. dwarsstroomsnelheid magnitude(m3/s)',
                    'criterium (m/s)',
                    'overschrijding (0=FALSE,1=TRUE)')
    discharges, crit_values, indices, xy_segments = TransverseDischarge().compute(rkm,
                                           transverse_velocity,
                                           configuration.ship_params.depth,
                                           configuration.ship_params.length,
                                           CRITERIA)
    convert_m_to_km = 1000

    def prepare_data_for_excel(xy_seg, discharge, crit_value):
        x_start = [xy[0][0]/convert_m_to_km for xy in xy_seg]
        x_end = [xy[0][-1]/convert_m_to_km for xy in xy_seg]
        y_max = [max(abs(xy[1])) for xy in xy_seg]
        exceedance = y_max > abs(crit_value)
        return (x_start, x_end, discharge, y_max, crit_value, exceedance)

    data = []
    for i,_ in enumerate(discharges):
        data.append(prepare_data_for_excel(xy_segments[i], discharges[i], crit_values[i]))
    
    with pd.ExcelWriter(outputfiles[1]) as writer:
        for label, d in zip(SHEET_LABELS, data):
            if d is not None:
                support.to_excel(
                    writer,
                    COLUMN_LABELS,
                    label,
                    *d
                )

    plotter = plotting.CrossFlow()
    plotter.create_figure(rkm,
                          transverse_velocity,
                          xy_segments,
                          indices,
                          crit_values,
                          configuration.general.bool_flags['invertxaxis'],
                          figfile)

class TransverseDischarge:
    def prepare_data(self,
                     distance: np.ndarray, 
                     transverse_velocity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Prepare data by inserting array roots and subsequently splitting into blocks."""
        distance_app, transverse_velocity_app = operations.insert_array_roots(distance, transverse_velocity)
        distance_split, transverse_velocity_split = operations.split_into_blocks(distance_app, transverse_velocity_app)
        return distance_split, transverse_velocity_split
    
    def compute(self,
                distance: np.ndarray,
                transverse_velocity: list[np.ndarray],
                ship_depth: float,
                ship_length: float,
                criteria: tuple[float, float]):
        """Computes the transverse discharge from transverse velocity, ship depth and ship length"""
        discharges = []
        crit_values = []
        indices = []
        xy_segments = [] # of shape case, block, ()

        for tv in transverse_velocity:
            distance_split, tv_split = self.prepare_data(distance, tv)
            discharge_case = []
            crit_case = []
            indices_case = []
            xy_segments_case = []

            for xi, yi in zip(distance_split, tv_split):
                if not np.any(yi):
                    continue

                max_integral, max_indices = operations.max_rolling_integral(xi, yi, ship_length)
                discharge = flow.trans_discharge(max_integral, ship_depth)
                discharge_case.append(discharge)

                start_idx, end_idx = max_indices[0], max_indices[-1] + 1
                indices_case.append((start_idx, end_idx))

                xi_segment = xi[start_idx:end_idx]
                yi_segment = yi[start_idx:end_idx]
                xy_segments_case.append((xi_segment, yi_segment))

                crit_case.append(criteria[1] if discharge < 50.0 else criteria[0])

            discharges.append(np.array(discharge_case))
            crit_values.append(np.array(crit_case))
            indices.append(indices_case)
            xy_segments.append(xy_segments_case)

        return discharges, crit_values, indices, xy_segments