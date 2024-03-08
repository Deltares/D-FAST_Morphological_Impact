import numpy


def distance_to_chainage(sline: numpy.ndarray, kline: numpy.ndarray, spnt: numpy.ndarray) -> numpy.ndarray:
    """
    Interpolate a quantity 'chainage' along a line to a given set of points.

    Arguments
    ---------
    sline : numpy.ndarray
        Array of length M containing the distance along a line. Distance should be monotoneously increasing.
    kline : numpy.ndarray
        Array of length M containing the chainage along a line.
    spnt : numpy.ndarray
        Array of length N containing the location of points measured as distance along the same line.

    Results
    -------
    kpnt : numpy.ndarray
        Array of length N containing the location of points expressed as chainage.
    """
    M = len(sline)
    N = len(spnt)

    # make sure that spnt is sorted
    isort = numpy.argsort(spnt)
    unsort = numpy.argsort(isort)
    spnt_sorted = spnt[isort]

    kpnt = numpy.zeros(N)
    j = 0
    for i in range(N):
        s = spnt_sorted[i]
        while j < M:
            if sline[j] < s:
                j = j+1
            else:
                break
        if j == 0:
            # distance is less than the distance of the first point, snap to it
            kpnt[i] = kline[0]
        elif j == M:
            # distance is larger than the distance of all the points on the line, snap to the last point
            kpnt[i] = kline[-1]
        else:
            # somewhere in the middle, average the chainage values
            a = (s - sline[j-1]) / (sline[j] - sline[j-1])
            kpnt[i] = (1-a) * kline[j-1] + a * kline[j]

    return kpnt[unsort]


def distance_along_line(xyline: numpy.ndarray)-> numpy.ndarray:
    """
    Compute distance coordinate along the specified line

    Arguments
    ---------
    xyline : numpy.ndarray
        Array of size M x 2 containing the x,y data of a line.

    Results
    -------
    sline : numpy.ndarray
        Array of length M containing the distance along the line.
    """

    # compute distance coordinate along the line
    ds = numpy.sqrt(((xyline[1:] - xyline[:-1])**2).sum(axis=1))
    sline = numpy.cumsum(numpy.concatenate([numpy.zeros(1),ds]))

    return sline