import logging
from dfastrbk.src.batch.core import run_analysis, preprocess_1d
from dfastrbk.src.config import Config
from dfastrbk.src.batch.dflowfm import Variables

logging.basicConfig(filename='dfastrbk.log',level=logging.INFO)
logger = logging.getLogger(__name__)

#TODO: make figfiles optional, now depends on SavePlots=True
def run(config_file: str, ships_file: str) -> None:
    """Main entry point for running the analysis."""
    logger.info("Running analysis...")

    configuration = Config(config_file, ships_file)

    variables = Variables(
        h="mesh2d_waterdepth",
        uc="mesh2d_ucmag",
        ucx="mesh2d_ucx",
        ucy="mesh2d_ucy",
        bl="mesh2d_flowelem_bl"
    )

    prof_line_df = None
    riverkm_coords = None
    if configuration.plotsettings.type != '2D':
        prof_line_df, riverkm_coords = preprocess_1d(configuration)

    for section in configuration.keys():
        if "Reference" in configuration.config[section]:
            run_analysis(configuration, section, variables, prof_line_df, riverkm_coords)
            
    logger.info("Finished analysis.")