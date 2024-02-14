from abc import ABC
from typing import List


class CelerObject(ABC):
    pass


class CelerDischarge(CelerObject):
    cdisch = tuple[float,float]


class CelerProperties(CelerObject):
    prop_q : List[float]
    prop_c : List[float]