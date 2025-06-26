from typing import Tuple, List
import numpy as np


# def append_array_roots(x: np.ndarray, y: np.ndarray) -> tuple:
#     """
#     Interpolate arrays and append the roots (zero-crossings)
#     """

#     s = np.abs(np.diff(np.sign(y))).astype(bool)
#     z = x[:-1][s] + np.diff(x)[s]/(np.abs(y[1:][s]/y[:-1][s])+1) # x-position of zero-crossings, found by linear interpolation

#     x_appended = np.concatenate([x,z],axis=0)
#     y_appended = np.concatenate([y,np.zeros(len(z))],axis=0)
#     x_sorted = np.sort(x_appended)
#     sort_idx = np.argsort(x_appended)
#     y_sorted = np.take_along_axis(y_appended,sort_idx,axis=0)
    
#     # # Make sure there are zero crossings at the beginning and end
#     # if (y_appended[0] > almost_zero) | (y_appended[0] < -almost_zero):
#     #     y_appended = np.insert(y_appended,0,0,axis=0) 
#     #     x_appended = np.insert(x_appended,0,x_appended[0],axis=0)
    
#     # if (y_appended[-1] > almost_zero) | (y_appended[-1] < -almost_zero):
#     #     y_appended = np.insert(y_appended,-1,0,axis=0) 
#     #     x_appended = np.insert(x_appended,-1,x_appended[-1],axis=0)

#     return x_sorted, y_sorted

def insert_array_roots(x: np.ndarray, y: np.ndarray) -> tuple:
    """
    Interpolate arrays and append the roots (zero-crossings)
    """
    z = find_roots(x, y)
    # Insert zero-crossings to the original arrays
    idx = x.searchsorted(z)
    x_mod = np.insert(x,idx+1,z) # we add +1 to include the last element of the block
    y_mod = np.insert(y,idx+1,0)

    return x_mod, y_mod

def find_roots(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Finds the x-position of zero-crossings"""
    s = np.abs(np.diff(np.sign(y))).astype(bool)
    return x[:-1][s] + np.diff(x)[s]/(np.abs(y[1:][s]/y[:-1][s])+1)

def split_into_blocks(x: np.ndarray, y: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Splits x and y into blocks, separated by 0 in y."""
    x_split = []
    y_split = []
    zero_ind = np.where(y == 0)[0]

    for i in range(len(zero_ind) - 1):
        start = zero_ind[i]
        end = zero_ind[i + 1] + 1
        x_split.append(x[start:end])
        y_split.append(y[start:end])

    return x_split, y_split

def max_rolling_integral(x: np.ndarray, 
                         y: np.ndarray, 
                         window: float) -> tuple:
    """
    Find the maximum integral within a rolling window of length window.
    """

    max_sum = float('-inf')
    current_sum = 0
    start = 0
    max_start = 0
    max_end = 0
    
    if x[-1] - x[0] < window:
        return np.sum(np.abs(y)), [0, len(y)-1]
    else:
        for i in enumerate(y):
            current_sum += np.sum(np.abs(y[i]))

            while x[i] - x[start] >= window:
                current_sum -= np.sum(np.abs(y[start]))
                start += 1
            
            if current_sum > max_sum:
                max_sum = current_sum
                max_start, max_end = start, i
        
        return max_sum, [max_start, max_end]