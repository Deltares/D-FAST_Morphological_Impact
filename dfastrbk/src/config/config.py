from pathlib import Path
from configparser import ConfigParser
from dfastio import xyc
from dfastrbk.src.batch.support import get_abs_path

class Ship:
    def __init__(self, reach: str, ships_file: str):
        self.config = ConfigParser()
        self.config.read(ships_file)
        self.length: float = float(self.config[reach]['Length'])
        self.depth: float = float(self.config[reach]['Depth'])

class Config:
    def __init__(self, config_file: str, section: str, ships_file: str):
        self.config_file = Path(config_file).resolve()
        self.config_dir = self.config_file.parent
        self.section = section
        self.ships_file = Path(ships_file).resolve()
        self.load_configuration()

    #TODO: implement D-FAST MI output file class
    def load_configuration(self):
        #TODO: replace by dfastmi configuration
        
        self.config_parser = ConfigParser()
        self.config = self.read_config_file(self.config_file)
        
        self.riverkm_file = get_abs_path(self.config_dir, self.config['General']['RiverKM'])
        self.riverkm = xyc.models.XYCModel.read(self.riverkm_file, num_columns=3)

        self.profiles_file = get_abs_path(self.config_dir, self.config['General']['ProfileLines'])
        self.reach = self.set_reach()
        self.branch = self.set_branch()
        self.output_files = []
        self.output_files.append(get_abs_path(self.config_dir,
                                              self.config[self.section]['Reference']))
        
        # Handle optional file input
        with_intervention = self.config_parser[self.section].get('WithIntervention')
        if with_intervention:
            self.output_files.append(get_abs_path(self.config_dir, with_intervention))

        # Parse bounding box if present
        if 'BoundingBox' in self.config:
            self.bbox = [float(self.config['BoundingBox'][key]) for key in self.config_parser['BoundingBox']]

        # Handle boolean flags from 'General' section
        for flag in ['InvertXAxis', 'WaterUpliftCorrection', 'BedChangeCorrection']:
            if flag in self.config:
                setattr(self, flag.lower(), self.config.getboolean('General', flag))


        self.ship_params = Ship(self.reach, self.ships_file)

    def get_config_file(self) -> Path:
        return self.config_file

    def read_config_file(self, config_file: Path) -> ConfigParser:
        self.config_parser.read(config_file)
        return self.config_parser

    def set_branch(self) -> str:
        return self.config_parser['General']['Branch']

    def set_reach(self) -> str:
        return self.config_parser['General']['Reach']
    
