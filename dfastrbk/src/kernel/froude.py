"""Performs corrections on the modelled Froude number specific for the discharge of ice """

import numpy as np
from dataclasses import dataclass
from xarray import DataArray

GRAV_CONSTANT = 9.81

def calculate_froude_number(water_depth: DataArray,
                     flow_velocity: DataArray) -> DataArray:
    """Calculates the Froude number from flow velocity and water depth"""
    froude_number = flow_velocity / np.sqrt(GRAV_CONSTANT * water_depth)
    return froude_number

def water_uplift(froude_number: DataArray) -> DataArray:
    """correction from water level uplift due to downstream ice cover"""
    froude_corrected = froude_number / np.sqrt(2)
    return froude_corrected

def bed_change(froude_number: DataArray) -> DataArray:
    """correction from bed level change due to the measure (as calculated by D-FAST-MI)"""
    # requires change in bed level calculated with d-fast-mi
    return froude_number

def combined_correction(froude_number: DataArray) -> DataArray:
    """combined correction"""
    return froude_number