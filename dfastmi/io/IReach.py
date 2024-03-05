from abc import ABC, abstractmethod


class IReach(ABC):
    normal_width : float
    ucritical : float
    qstagnant : float

    """Interface for Reach information"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the Reach"""

    @property
    @abstractmethod
    def config_key_index(self) -> int:
        """Index number of the Reach in the branch"""