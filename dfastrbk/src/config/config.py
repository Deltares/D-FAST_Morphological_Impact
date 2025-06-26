from pathlib import Path
from configparser import ConfigParser
from dfastrbk.src.batch.support import get_abs_path
from dfastio import xyc

class Ship:
    def __init__(self, reach: str):
        self.ship_file = Path(r'dfastrbk/src/ship_dimensions.ini')
        self.config = ConfigParser()
        self.config.read(self.ship_file)
        self.length: float = float(self.config[reach]['Length'])
        self.depth: float = float(self.config[reach]['Depth'])

class Config:
    def __init__(self, case: str, section: str):
        self.case = case
        self.section = section
        self.load_configuration()

    #TODO: implement D-FAST MI output file class
    def load_configuration(self):
        #TODO: replace by dfastmi configuration
        self.config_dir = Path(f'dfastrbk/examples/{self.case}')
        self.config_file = get_abs_path(self.config_dir,'config.ini')
        self.config_parser = ConfigParser()
        self.config = self.read_config_file(self.config_file)
        
        self.riverkm_file = get_abs_path(self.config_dir, self.config['General']['RiverKM'])
        self.riverkm = xyc.models.XYCModel.read(self.riverkm_file, num_columns=3,delimiter="	")

        self.profiles_file = get_abs_path(self.config_dir, self.config['General']['ProfileLines'])
        self.reach = self.set_reach()
        self.branch = self.set_branch()
        self.output_files = []
        self.output_files.append(get_abs_path(self.config_dir,
                                              self.config[self.section]['Reference']))
        if 'WithIntervention' in self.config_parser[self.section]:
            self.output_files.append(get_abs_path(self.config_dir,
                                                  self.config[self.section]['WithIntervention']))
        
        if 'BoundingBox' in self.config:
            self.bbox = []
            for key in self.config_parser['BoundingBox']:
                self.bbox.append(float(self.config['BoundingBox'][key]))
        
        self.invert_xaxis: bool = self.config.getboolean('General', 'InvertXAxis')
        self.water_uplift_correction: bool = self.config.getboolean('General','WaterUpliftCorrection')
        self.bed_change_correction: bool = self.config.getboolean('General','BedChangeCorrection')
        self.ship_params = Ship(self.reach)

    def get_config_file(self) -> Path:
        return self.config_file

    def read_config_file(self, config_file: Path) -> ConfigParser:
        self.config_parser.read(config_file)
        return self.config_parser

    def set_branch(self) -> str:
        return self.config_parser['General']['Branch']

    def set_reach(self) -> str:
        return self.config_parser['General']['Reach']
    
