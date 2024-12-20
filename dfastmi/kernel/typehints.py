from typing import Dict, List, Optional, Tuple, Union

from numpy import ndarray

# Represents a tuple of four floats. The floats represent characteristic discharges (from rivers configuration file).
QLevels = Tuple[float, float, float, float]

# Represents a tuple of two floats. The floats represent characteristic discharge adjustments (from rivers configuration file).
QChange = Tuple[float, float]

# Represents a tuple of three optional floats. The floats can be None if no value is available. The optional floats represent discharges for which simulation results are (expected to be) available.
QRuns = Tuple[Optional[float], Optional[float], Optional[float]]

# Represents a list of floats of variable length.
Vector = List[float]

# Represents a list of booleans of variable lengths.
BoolVector = List[bool]

# Filename dictionary
FilenameDict = Dict[Union[int, str, Tuple[float, str]], str]

# Represents a list of bed level changes. Some entries may be empty, or 0.0.
BedChangeList = List[Optional[Union[float, ndarray]]]
