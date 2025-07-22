from pathlib import Path
import numpy as np
from xugrid import UgridDataset
from tqdm import tqdm
from pandas import DataFrame

from dfastrbk.src.batch.dflowfm import load_simulation_data, Variables
from dfastrbk.src.config import Config
from dfastrbk.src.batch import cross_flow, ice, dflowfm
from dfastrbk.src.batch.plotting import Plot2D, construct_figure_filename

def run_analysis(configuration: Config, 
                 section: str,
                 variables: Variables,
                 prof_line_df: DataFrame | None,
                 riverkm_coords: np.ndarray | None):
    simulation_data = load_simulation_data(configuration, section)

    plot_actions = {
    '1D': lambda: run_1d_analysis(configuration,
                                    section, 
                                    simulation_data, 
                                    variables, 
                                    prof_line_df,
                                    riverkm_coords),
    '2D': lambda: run_2d_analysis(configuration, 
                                    section,
                                    simulation_data, 
                                    variables),
    }
    plot_actions['both'] = lambda: (plot_actions['1D'], plot_actions['2D'])

    try:
        plot_actions[configuration.plotsettings.type]()
    except KeyError as exc:
        raise ValueError(f"Unknown plot type {configuration.plotsettings.type}.") from exc

def preprocess_1d(configuration: Config) -> tuple[DataFrame, np.ndarray]:
    prof_line_df = dflowfm.read_profile_lines(Path(configuration.general.profiles_file))
    riverkm_coords = np.array(configuration.general.riverkm.coords)
    return prof_line_df, riverkm_coords
    
def run_1d_analysis(configuration: Config, 
                    section: str,
                    simulation_data: list[UgridDataset], 
                    variables: Variables,
                    prof_line_df: DataFrame,
                    riverkm_coords: np.ndarray):
    """Run 1D profile analysis and plotting."""

    for geom_idx, profile_line in enumerate(tqdm(prof_line_df.geometry, desc="geometry", position=0, leave=True)):
        profile_coords = np.array(profile_line.coords)
        profile_index = str(prof_line_df.iloc[geom_idx].name)
        profile_data = {var: [] for var in variables._fields}

        for data in tqdm(simulation_data, desc="simulation data", position=0, leave=True):
            sliced, rkm, isegment, iface = dflowfm.slice_ugrid(
                data, profile_coords, riverkm_coords
            )
            angles = np.array(prof_line_df['angle'].iloc[geom_idx][isegment])
            for var, name in variables._asdict().items():
                profile_data[var].append(dflowfm.get_profile_data(sliced, name, iface))

        save_1d_figures(configuration, section, profile_index, profile_data, angles, rkm)
        
        bedlevel = simulation_data[-1][variables.bl].where(lambda x: x != 999)
        figfile = construct_figure_filename(configuration.plotsettings.options.figure_save_directory,
                                            f"profile{profile_index}_location",
                                            configuration.plotsettings.options.plot_extension)
        Plot2D().plot_profile_line(profile_line, bedlevel, riverkm_coords, figfile)

def save_1d_figures(configuration: Config,
                    section: str,
                    profile_index: str,
                    profile_data: dict,
                    angles: np.ndarray,
                    rkm: np.ndarray):
    """Generate and save 1D figures."""
    figdir = configuration.plotsettings.options.figure_save_directory
    figext = configuration.plotsettings.options.plot_extension
    outputdir = configuration.outputdir

    base = f"{section}_profile{profile_index}_velocity_angle"
    figfile = construct_figure_filename(figdir, base, figext)
    outputfile = (outputdir/ base).with_suffix('.csv')
    ice.run_1d(profile_data["uc"], profile_data["ucx"], profile_data["ucy"], angles, rkm, configuration, figfile, outputfile)

    base = f"{section}_profile{profile_index}_transverse_flow"
    figfile = construct_figure_filename(figdir, base, figext)
    outputfile = (outputdir / base).with_suffix('.csv')
    cross_flow.run(profile_data["ucx"], profile_data["ucy"], angles, rkm, configuration, figfile, outputfile)

def run_2d_analysis(configuration: Config, 
                    section: str,
                    simulation_data: list[UgridDataset], 
                    variables: Variables):
    """Run 2D Froude number analysis and plotting."""
    labels = ("reference", "intervention","difference")

    water_depth = [ds[variables.h] for ds in simulation_data]
    flow_velocity = [ds[variables.uc] for ds in simulation_data]

    #TODO: this is already done in ice.run_2d
    waterupliftcorrection = configuration.general.bool_flags['waterupliftcorrection']
    bedchangecorrection = configuration.general.bool_flags['bedchangecorrection']

    suffix = ''
    if waterupliftcorrection:
        suffix = suffix + '_wateruplift'
    if bedchangecorrection:
        suffix = suffix + '_bedchange'
        
    figfiles = [construct_figure_filename(configuration.plotsettings.options.figure_save_directory,
                                            f"{section}_{label}_Froude{suffix}",
                                            configuration.plotsettings.options.plot_extension) for label in labels]
    #TODO: make riverkm optional
    ice.run_2d(
        water_depth,
        flow_velocity,
        configuration,
        figfiles
    )
