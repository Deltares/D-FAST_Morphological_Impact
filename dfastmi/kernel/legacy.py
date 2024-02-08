import math
from dfastmi.kernel.typehints import Vector, BoolVector

def estimate_sedimentation_length(
    rsigma: Vector,
    applyQ: BoolVector,
    nwidth: float,
) -> float:
    """
    This routine computes the sedimentation length in metres.
    (Legacy of version 1.0.0)

    Arguments
    ---------
    rsigma : Vector
        A tuple of relaxation factors, one for each period.
    applyQ : BoolVector
        A tuple of 3 flags indicating whether each value should be used or not.
    nwidth : float
        Normal river width (from rivers configuration file).

    Returns
    -------
    L : float
        The expected yearly impacted sedimentation length.
    """
    logrsig = [0.0] * len(rsigma)
    for i in range(len(rsigma)):
        if applyQ[i]:
            logrsig[i] = math.log(rsigma[i])
    length = -sum(logrsig)
    
    return 2.0 * nwidth * length