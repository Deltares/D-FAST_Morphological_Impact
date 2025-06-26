from collections import OrderedDict
from typing import Tuple
from pathlib import Path
import numpy as np
from shapely import LineString
from xugrid import UgridDataset
from pandas import DataFrame
from dfastrbk.src.batch import geometry

varn_face_x_bnd = 'mesh2d_face_x_bnd'
varn_face_y_bnd = 'mesh2d_face_y_bnd'

def slice_simulation_data(simulation_data: UgridDataset, 
                          profiles_file: Path,
                          riverkm: LineString) -> Tuple:
    #TODO: decouple profile_data from [rkm, segment_idx and face_idx] 
    # such that for multiple simulations with the same grid, only one grid can be sliced

    # Step 1: Return profile line(s) as dataframe
    prof_line_df = read_profile_lines(profiles_file)

    # Step 2: Intersect simulation data with profile line(s)
    geom_idx = 0 #TODO: loop over geom_idx
    profile_linestring = prof_line_df.geometry[geom_idx]
    profile_data = intersect_linestring(simulation_data, profile_linestring)
    
    # Step 3: Convert to river km
    profile_coords = prof_line_df.get_coordinates(index_parts=True).loc[geom_idx].to_numpy()
    edge_coords = extract_edge_coords(profile_data)
    xykm_coords = np.array(riverkm.coords)
    rkm, segment_idx, face_idx = slice_mesh_with_polyline(edge_coords, profile_coords, xykm_coords)
    
    return profile_data, prof_line_df, rkm, segment_idx, face_idx

def read_profile_lines(profiles_file: Path) -> DataFrame:
    profile_lines = geometry.ProfileLines(profiles_file)
    prof_line_df = profile_lines.read_file()
    prof_line_df['angle'] = profile_lines.get_angles()
    return prof_line_df

def intersect_linestring(simulation_data: UgridDataset, profile_linestring) -> UgridDataset:
    return simulation_data.ugrid.intersect_linestring(profile_linestring)

def extract_edge_coords(profile_data: UgridDataset) -> np.ndarray:
    x_bnd = profile_data[varn_face_x_bnd].values
    y_bnd = profile_data[varn_face_y_bnd].values
    return np.unique(np.stack((x_bnd, y_bnd), axis=-1), axis=0)

def slice_mesh_with_polyline(edge_coords: np.ndarray, 
                             profile_coords: np.ndarray,
                             xykm_coords: np.ndarray):
    intersects, face_indices = find_intersects(edge_coords, profile_coords)
    assert len(intersects) != 0, "No intersects found between profile line(s) and simulation data. Expand the bounding box, or change the profile line(s)"
    
    profile_distances, segment_indices = calculate_intersect_distance(profile_coords, intersects)
    rkm, segment_idx, face_idx = _order_intersection_points(intersects,
                                                profile_distances,
                                                segment_indices,
                                                face_indices,
                                                xykm_coords)
    return rkm, segment_idx, face_idx
    
def find_intersects(edge_coords: np.ndarray, line_coords: np.ndarray) -> tuple[np.ndarray, 
                                                                                np.ndarray]:

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
    intersects (np.ndarray): Intersection points.
    profile_distances (np.ndarray): Distances along the profile line.
    segment_idx (np.ndarray): Segment indices of the profile line.
    face_idx (np.ndarray): Face indices of mesh.
    river_km (np.ndarray): x,y coordinates of river kilometers (rkm)

    Returns:
    tuple[np.ndarray, np.ndarray, np.ndarray]: Grouped rkm, segment indices, and face indices."""

    # 1. Sort along profile line
    sorted_data = [sort_a_by_b(d, profile_distances) for d in [intersects, segment_idx, face_idx]]
    intersects_sorted, segment_idx_sorted, face_idx_sorted = sorted_data

    # 2. Group face indices
    face_idx_grouped, group_idx = group_duplicates(face_idx_sorted)
    segment_idx_grouped = segment_idx_sorted[group_idx]
    intersects_grouped = intersects_sorted[group_idx]

    # 3. Convert to rkm, in metres
    rkm = convert_to_rkm(intersects_grouped, river_km, 1000)

    # 4. Ensure the overall direction is downstream (so the first rkm < last rkm)
    if rkm[0] > rkm[-1]:
        rkm               = rkm[::-1]
        segment_idx_grouped = segment_idx_grouped[::-1]
        face_idx_grouped    = face_idx_grouped[::-1]

    # 5. Take the longest strictly increasing subsequence of rkm
    lis_idx = _lis_strict_indices(rkm)

    rkm_ordered         = rkm[lis_idx]
    segment_idx_ordered = segment_idx_grouped[lis_idx]
    face_idx_ordered    = face_idx_grouped[lis_idx]

    # now this is guaranteed non‐decreasing (strictly increasing)
    assert np.all(np.diff(rkm_ordered) >= 0)

    return rkm_ordered, segment_idx_ordered, face_idx_ordered

def _lis_strict_indices(a: np.ndarray) -> list[int]:
    """
    Returns the indices of a longest strictly non-decreasing subsequence (LIS) in `a`.
    O(n^2) dynamic programming, fine for n ~ 10^3.
    """
    n = len(a)
    # dp[i] = length of LIS ending at i
    dp = np.ones(n, dtype=int)
    # prev[i] = index of the previous element in that LIS (or -1 if none)
    prev = -np.ones(n, dtype=int)

    for i in range(n):
        for j in range(i):
            if a[j] <= a[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j

    # find end of the best subsequence
    i = int(np.argmax(dp))
    # backtrack
    seq = []
    while i >= 0:
        seq.append(i)
        i = prev[i]
    return list(reversed(seq))

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


