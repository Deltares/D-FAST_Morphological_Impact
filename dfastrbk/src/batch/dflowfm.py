from collections import OrderedDict
from typing import NamedTuple
from pathlib import Path
import numpy as np
import xugrid as xu
from shapely import LineString
from xugrid import UgridDataset
import pandas as pd
from pandas import DataFrame
from dfastrbk.src.batch import geometry
from dfastrbk.src.config import Config, get_output_files

VARN_FACE_X_BND = 'mesh2d_face_x_bnd'
VARN_FACE_Y_BND = 'mesh2d_face_y_bnd'

class Variables(NamedTuple):
    """Class of relevant variables.
    h: water depth
    uc: flow velocity magnitude
    ucx: flow velocity, x-component
    ucy: flow velocity, y-componentn
    bl: bed level"""
    h: str
    uc: str
    ucx: str
    ucy: str
    bl: str

def load_simulation_data(configuration: Config, section: str) -> list[UgridDataset]:
    """Load and preprocess simulation datasets."""
    datasets = []
    output_files = get_output_files(configuration.config, 
                                    configuration.configdir, 
                                    section)
    for file in output_files:
        ds = xu.open_dataset(file)

        if configuration.general.bbox is not None:
            x_slice = slice(configuration.general.bbox[0], configuration.general.bbox[1])
            y_slice = slice(configuration.general.bbox[2], configuration.general.bbox[3])
            ds = ds.ugrid.sel(x=x_slice, y=y_slice)

        ds = extract_variables(ds)
        datasets.append(ds)
    return datasets

def extract_variables(ds: UgridDataset) -> UgridDataset:
    """Extract and standardize variable names from dataset."""
    if 'time' in ds.coords:
        ds = ds.isel(time=-1)
    else:
        ds['mesh2d_waterdepth'] = ds['mesh2d_last001'] - ds['mesh2d_flowelem_bl']
        ds['mesh2d_ucmag'] = ds['mesh2d_last002']
        ds['mesh2d_ucx'] = ds['mesh2d_last003']
        ds['mesh2d_ucy'] = ds['mesh2d_last004']
    return ds

def get_profile_data(profile_dataset: UgridDataset,
                      variable_name: str,
                      face_idx) -> dict:
    profile_data = profile_dataset[variable_name].values[face_idx]
    return profile_data

def slice_ugrid(simulation_data: UgridDataset,
               profile_coords: np.ndarray,
               riverkm_coords: np.ndarray) -> tuple[UgridDataset, np.ndarray, np.ndarray, np.ndarray]:
    
    edge_coords = extract_edge_coords(simulation_data, VARN_FACE_X_BND, VARN_FACE_Y_BND)
    rkm, segment_idx, face_idx = slice_mesh_with_polyline(edge_coords, profile_coords, riverkm_coords)
    return simulation_data, rkm, segment_idx, face_idx

def read_profile_lines(profiles_file: Path) -> DataFrame:
    profile_lines = geometry.ProfileLines(profiles_file)
    prof_line_df = profile_lines.read_file()
    prof_line_df['angle'] = profile_lines.get_angles()
    return prof_line_df

def intersect_linestring(simulation_data: UgridDataset, 
                         profile: LineString) -> UgridDataset:
    """Returns only the data on faces intersected by the profile line"""
    return simulation_data.ugrid.intersect_linestring(profile)

def extract_edge_coords(profile_data: UgridDataset,
                        varn_face_x_bnd: str,
                        varn_face_y_bnd: str) -> np.ndarray:
    x_bnd = profile_data[varn_face_x_bnd].values
    y_bnd = profile_data[varn_face_y_bnd].values
    return np.stack((x_bnd, y_bnd), axis=-1)

def slice_mesh_with_polyline(edge_coords: np.ndarray, 
                             profile_coords: np.ndarray,
                             xykm_coords: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Slices mesh edges with a profile line and returns for each intersection point:
        pkm: projected value of xykm, found by interpolation
        segment_idx: index of segment of profile line
        face_idx: index of mesh face"""
    intersects, face_indices = find_intersects(edge_coords, profile_coords)
    assert len(intersects) != 0, "No intersects found between profile line(s) and simulation data. Expand the bounding box, or change the profile line(s)"
    
    profile_distances, segment_indices = calculate_intersect_distance(profile_coords, intersects)
    pkm, segment_idx, face_idx = _order_intersection_points(intersects,
                                                profile_distances,
                                                segment_indices,
                                                face_indices,
                                                xykm_coords)
    return pkm, segment_idx, face_idx
    
def find_intersects(edge_coords: np.ndarray, 
                    line_coords: np.ndarray) -> tuple[np.ndarray,np.ndarray]:

    """	Find intersection points between mesh edges and a line.
    Parameters:
    edge_coords: coordinates of the mesh edges (nfaces,nedges,2)
    line_coords: coordinates of the profile line (N,2)
    
    Returns:
    intersects: coordinates of the intersection points (N,2)
    face_idx: indices of the mesh faces where the intersection occurs (N,1)"""
    intersects = [] # coordinates of intersection points
    face_idx = [] # index of the face where the intersection occurs
    nfaces = edge_coords.shape[0] # number of faces/cells
    nedges = edge_coords.shape[1] # number of edges, i.e. rectangle or triangle
    b = LineString(line_coords)

    for i in range(nfaces):
        for j in range(nedges):
            next_j = (j + 1) % nedges
            a1 = edge_coords[i,j,:]
            a2 = edge_coords[i,next_j,:]

            a = LineString([a1, a2])

            try:
                intersect = a.intersection(b)
                if not intersect.is_empty:
                    intersects.append(intersect)
                    face_idx.extend([i] * len(intersect.geoms) if intersect.geom_type == 'MultiPoint' else [i])
            except: # if no intersection is found
                pass

    intersects = geometry.extract_coordinates(intersects)
    face_idx = np.asarray(face_idx)
    #pd.DataFrame(np.column_stack((intersects[:,0],intersects[:,1],face_idx))).to_csv('intersects.csv')
    return intersects, face_idx

def calculate_intersect_distance(line_coords: np.ndarray, 
                                  intersects: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    """ 
    Returns:
    profile_distances: distance of intersection points along line.
    segment_idx: indices of the line segments where the intersection occurs (N,1)"""
    profile_distances, segment_idx = geometry.find_distances_to_points(line_coords, intersects)
    return profile_distances, segment_idx

#TODO: "fix" ordering
def _order_intersection_points(intersects: np.ndarray,
               profile_distances: np.ndarray,
               segment_idx: np.ndarray,
               face_idx: np.ndarray,
               river_km: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Correctly orders the intersection points between a UGRID mesh and profile line.

    Parameters:
    intersects: Intersection points.
    profile_distances: Distances along the profile line.
    segment_idx: Segment indices of the profile line.
    face_idx: Face indices of mesh.
    river_km: x,y coordinates of river kilometers (rkm)

    Returns:
    tuple[np.ndarray, np.ndarray, np.ndarray]: Grouped rkm, segment indices, and face indices."""

    # 1. Sort along profile line
    sorted_data = [sort_a_by_b(a, profile_distances) for a in [intersects, segment_idx, face_idx]]
    intersects, segment_idx, face_idx = sorted_data

    # 2. Group face indices
    face_idx, group_idx = group_duplicates(face_idx)
    segment_idx = segment_idx[group_idx]
    intersects = intersects[group_idx]

    # 3. Convert to rkm, in metres
    rkm = convert_to_rkm(intersects, river_km, 1000)

    # 4. Ensure the overall direction is downstream (so the first rkm < last rkm)
    if rkm[0] > rkm[-1]:
        rkm               = rkm[::-1]
        segment_idx = segment_idx[::-1]
        face_idx    = face_idx[::-1]

    # 5. strictly increasing sequence of rkm
    mask = np.empty_like(rkm, dtype=bool)
    mask[0] = True
    last_r = rkm[0]

    for i in range(1, len(rkm)):
        if rkm[i] >= last_r:
            mask[i] = True
            last_r = rkm[i]
        else:
            mask[i] = False

    rkm_ordered = rkm[mask]
    segment_idx_ordered = segment_idx[mask]
    face_idx_ordered = face_idx[mask]

    # now this should be guaranteed non‐decreasing (strictly increasing)
    assert np.all(np.diff(rkm_ordered) >= 0)

    return rkm_ordered, segment_idx_ordered, face_idx_ordered

# def _lis_strict_indices(a: np.ndarray) -> list[int]:
#     """
#     Returns the indices of a longest strictly non-decreasing subsequence (LIS) in `a`.
#     """
#     n = len(a)
#     # dp[i] = length of LIS ending at i
#     dp = np.ones(n, dtype=int)
#     # prev[i] = index of the previous element in that LIS (or -1 if none)
#     prev = -np.ones(n, dtype=int)

#     for i in range(n):
#         for j in range(i):
#             if a[j] <= a[i] and dp[j] + 1 > dp[i]:
#                 dp[i] = dp[j] + 1
#                 prev[i] = j

#     # find end of the best subsequence
#     i = int(np.argmax(dp))
#     # backtrack
#     seq = []
#     while i >= 0:
#         seq.append(i)
#         i = prev[i]
#     return list(reversed(seq))

def sort_a_by_b(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Sorts the array `a` by the argsort of `b`.

    Parameters:
    a (np.ndarray): Array to be sorted.
    b (np.ndarray): Array to sort by.

    Returns:
    np.ndarray: Sorted array `a`.
    """
    sort_idx = np.argsort(b)
    return np.take_along_axis(a, sort_idx[:, np.newaxis], axis=0) if a.ndim > 1 else a[sort_idx]

def group_duplicates(array: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Groups duplicates in an array, preserving insertion order of first occurrences"""
    groups = OrderedDict()
    for idx, val in enumerate(array):
        if val not in groups:
            groups[val] = []
        groups[val].append(idx)

    group_indices = np.array([idx for indices in groups.values() for idx in indices])
    grouped_array = array[group_indices]
    return grouped_array, group_indices

def convert_to_rkm(intersects, river_km, conversion_factor = 1):
    """Converts an array of points to the corresponding rkm values
    
    Parameters:
    intersects: intersection points
    river_km: chainage values
    conversion_factor: optional, to convert km to another unit (default = 1)"""
    rkm = geometry.project_km_on_line(intersects, river_km) * conversion_factor
    return rkm


