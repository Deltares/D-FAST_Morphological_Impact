from typing import NamedTuple
from pathlib import Path
from xarray import DataArray
from xugrid import UgridDataset
import numpy as np
from dfastrbk.src.batch import plotting, dflowfm, geometry
from dfastrbk.src.kernel import froude
from shapely import LineString

def run_1d(uc: list[np.ndarray],
           ucx: list[np.ndarray],
           ucy: list[np.ndarray],
           rkm: np.ndarray, 
           invert_xaxis: bool) -> None:

    velocity_magnitude = []
    velocity_angle = []
    
    for m, x, y in zip(uc,ucx,ucy):
        velocity_magnitude.append(m)
        flow_angle = geometry.vector_angle(x,y)
        velocity_angle.append(flow_angle)

    plotter_1D = plotting.Ice1D()
    plotter_1D.create_figure(rkm,
                             velocity_magnitude,
                             velocity_angle,
                             invert_xaxis)

def run_2d(water_depth: DataArray, 
           flow_velocity: DataArray, 
           water_uplift: bool, 
           bed_change: bool,
           riverkm: LineString):
    froude_number: DataArray = froude.calculate_froude_number(water_depth,flow_velocity)
    froude_number = correct_model_results(froude_number,water_uplift,bed_change)
    plotter_2D = plotting.Ice2D()
    plotter_2D.create_map(froude_number,riverkm)

def run_2d_diff(water_depth: list[DataArray],
                flow_velocity: list[DataArray],
                water_uplift: bool,
                bed_change: bool):
    froude_number = []
    for i, (h, u) in enumerate(zip(water_depth, flow_velocity)):
        froude_number.append(froude.calculate_froude_number(h,u))
        froude_number[i] = correct_model_results(froude_number[i],water_uplift,bed_change)
    plotter_2D = plotting.Ice2D()
    plotter_2D.create_diff_map(froude_number[0],froude_number[1])

def correct_model_results(froude_number: DataArray,
                          water_uplift: bool = False,
                          bed_change: bool = False) -> DataArray:
    if water_uplift and bed_change:
        froude_number = froude.combined_correction(froude_number)
    if water_uplift and not bed_change:
        froude_number = froude.water_uplift(froude_number)
    if bed_change and not water_uplift:
        froude_number = froude.bed_change(froude_number)
    
    return froude_number

