from pathlib import Path
import xarray as xr
from xarray import DataArray
import numpy as np
from shapely import LineString
from dfastrbk.src.batch import plotting, geometry
from dfastrbk.src.kernel import froude
from dfastrbk.src.config import Config
from dfastrbk.src.batch import support
from dfastmi.batch.PlotOptions import PlotOptions

def run_1d(uc: list[np.ndarray],
           ucx: list[np.ndarray],
           ucy: list[np.ndarray],
           profile_angles: np.ndarray,
           rkm: np.ndarray,
           configuration: Config,
           figfile: Path,
           outputfile: Path) -> None:
    
    COLUMN_LABELS = ('afstand (rkm)',
                     'stroomsnelheid (m/s)',
                     'stromingshoek (graden)',
                     'profiellijn (graden)',
                     'stromingshoek t.o.v. profiellijn (graden)')
    
    velocity_magnitude = []
    velocity_angle = []
    angle_diff = []
    
    for m, x, y in zip(uc,ucx,ucy):
        velocity_magnitude.append(m)
        flow_angle = geometry.vector_angle(x,y)
        velocity_angle.append(flow_angle)

    # shortest angular difference
    angle_diff = [(angles - profile_angles + 180) % 360 - 180
                      for angles in velocity_angle]
    angle_diff = [np.where(angles > 90, angles - 180, angles) for angles in angle_diff]
    angle_diff = [np.where(angles < -90, angles + 180, angles) for angles in angle_diff]

    support.to_csv(outputfile,
                   COLUMN_LABELS,
                   rkm / 1000,
                   velocity_magnitude[0],
                   velocity_angle[0],
                   profile_angles,
                   angle_diff[0])
    

    plotting.Ice1D().create_figure(rkm,
                             velocity_magnitude,
                             angle_diff,
                             configuration,
                             figfile)

def run_2d(
    water_depth: list[DataArray],
    flow_velocity: list[DataArray],
    water_uplift: bool,
    bed_change: bool,
    riverkm: LineString,
    plotoptions: PlotOptions,
    filenames: list[Path]
):
    froude_number = []
    for idx, (h, u) in enumerate(zip(water_depth, flow_velocity)):
        fr = froude.calculate_froude_number(h, u)
        fr = correct_model_results(fr, water_uplift, bed_change)
        froude_number.append(fr)
        plotting.Ice2D().create_map(fr, riverkm, filenames[idx])

    if len(froude_number)>0:
        plotting.Ice2D().create_diff_map(froude_number[0], 
                                         froude_number[1], 
                                         riverkm,
                                         filenames[2])

def correct_model_results(froude_number: DataArray,
                          water_depth: DataArray,
                          water_uplift: bool = False,
                          bed_change: bool = False,
                          bed_change_file: Path | None = None) -> DataArray:
    if bed_change:
        if bed_change_file is None:
            raise ValueError("No bed change file specified in configuration.")
        bedlevel_change = get_bedlevel_change(bed_change_file)
        froude_number = froude.bed_change(froude_number,bedlevel_change,water_depth)
    if water_uplift:
        froude_number = froude.water_uplift(froude_number)
    return froude_number

def get_bedlevel_change(file: Path):
    ds = xr.open_dataset(file)
    dfast_name = 'avgdzb'
    data_vars = list(ds.data_vars)
    if dfast_name in data_vars:
        return ds[dfast_name]
    
    if len(data_vars) == 1:
        return ds[data_vars[0]]

    raise IOError(f"NetCDF file must contain {dfast_name} or exactly one variable.")