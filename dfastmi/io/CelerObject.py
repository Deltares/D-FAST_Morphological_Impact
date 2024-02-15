from abc import ABC, abstractmethod
from typing import List


class CelerObject(ABC):
    @abstractmethod
    def validate(self):
        pass
    


class CelerDischarge(CelerObject):
    cdisch = tuple[float,float]
    
    def validate(self):
        if self.cdisch == (0.0, 0.0):            
            # raise Exception(
            #             'The parameter "CelerQ" must be specified for branch "{}", reach "{}" since "CelerForm" is set to 2.'.format(
            #                 branch,
            #                 reach,
            #             )
            #         )
            return
    


class CelerProperties(CelerObject):
    prop_q : List[float]
    prop_c : List[float]

    def validate(self):
        return super().validate()