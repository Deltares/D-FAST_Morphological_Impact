from abc import ABC
from typing import List

from dfastmi.io.CelerObject import CelerObject

class ObservableReachList:
    def __init__(self):
        self._list = []
        self._observers = []
    
    def __getitem__(self, index):
        return self._list[index]
    
    def append(self, element):
        self._list.append(element)
        for observer in self._observers:
            observer.notify(element)

    def add_observer(self, observer):
        self._observers.append(observer)


class Reach(ABC):
    name : str
    config_key_index : int
    normal_width : float
    ucritical : float
    qstagnant : float
    parent_branch_name : str

    def __init__(self, reach_name : str = "Reach", reach_config_key_index:int = 1):
        self.name = reach_name
        self.config_key_index = reach_config_key_index


class ReachLegacy(Reach):
    proprate_high : float
    proprate_low : float
    qbankfull : float
    qmin : float
    qfit : tuple[float,float]
    qlevels : List[float]
    dq : tuple[float,float]


class ReachAdvanced(Reach):
    hydro_q : List[float]
    hydro_t : List[float]
    auto_time : bool
    qfit : tuple[float,float]

    use_tide : bool
    tide_boundary_condition : List[float]

    celer_form : int
    celer_object : CelerObject = None    
