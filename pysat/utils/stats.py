"""
pysat.utils.stats - statistical operations in pysat
=========================================

pysat.coords contains a number of coordinate-transformation
functions used throughout the pysat package.
"""

import numpy as np
import warnings


def median1D(self, bin_params, bin_label, data_label):
    """Calculates the median for a series of binned data.

    .. deprecated:: 2.2.0
      `median1D` will be removed in pysat 3.0.0, a
      similar function will be added to pysatSeasons

    Parameters
    ----------
    bin_params : array_like
        Input array defining the bins in which the median is calculated
    bin_label : string
        Name of data parameter which the bins cover
    data_level : string
        Name of data parameter to take the median of in each bin

    Returns
    -------
    medians : array_like
        The median data value in each bin

    """

    warnings.warn(' '.join(["utils.stats.median1D is deprecated and will be",
                            "removed in pysat 3.0.0. Please use",
                            "ssnl.avg.median1D instead"]),
                  DeprecationWarning, stacklevel=2)

    bins = np.arange(bin_params[0], bin_params[1] + bin_params[2],
                     bin_params[2])
    medians = 0. * bins[0:-1]
    ind = np.digitize(self.data[bin_label], bins)

    for i in range(bins.size-1):
        index, = np.where(ind == (i + 1))
        if len(index) > 0:
            idx = self.data.index[index.astype(int)]
            medians[i] = self.data.loc[idx, data_label].median()

    return medians


def nan_circmean(samples, high=2.0*np.pi, low=0.0, axis=None):
    """NaN insensitive version of scipy's circular mean routine

    .. deprecated:: 2.1.0
      `nan_circmean` will be removed in pysat 3.0.0, this functionality has
      been added to scipy 1.4

    Parameters
    -----------
    samples : array_like
        Input array
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    circmean : float
        Circular mean

    """

    warnings.warn(' '.join(["utils.stats.nan_circmean is deprecated and will",
                            "be removed in a future version. This function is",
                            "part of the scipy 1.4.0 milestones and will be",
                            "migrated there."]),
                  DeprecationWarning, stacklevel=2)

    samples = np.asarray(samples)
    samples = samples[~np.isnan(samples)]
    if samples.size == 0:
        return np.nan

    # Ensure the samples are in radians
    ang = (samples - low) * 2.0 * np.pi / (high - low)

    # Calculate the means of the sine and cosine, as well as the length
    # of their unit vector
    ssum = np.sin(ang).sum(axis=axis)
    csum = np.cos(ang).sum(axis=axis)
    res = np.arctan2(ssum, csum)

    # Bring the range of the result between 0 and 2 pi
    mask = res < 0.0

    if mask.ndim > 0:
        res[mask] += 2.0 * np.pi
    elif mask:
        res += 2.0 * np.pi

    # Calculate the circular standard deviation
    circmean = res * (high - low) / (2.0 * np.pi) + low
    return circmean


def nan_circstd(samples, high=2.0*np.pi, low=0.0, axis=None):
    """NaN insensitive version of scipy's circular standard deviation routine

    .. deprecated:: 2.1.0
      `nan_circstd` will be removed in pysat 3.0.0, this functionality has
      been added to scipy 1.4

    Parameters
    -----------
    samples : array_like
        Input array
    high: float or int
        Upper boundary for circular standard deviation range (default=2 pi)
    low : float or int
        Lower boundary for circular standard deviation range (default=0)
    axis : int or NoneType
        Axis along which standard deviations are computed.  The default is to
        compute the standard deviation of the flattened array

    Returns
    --------
    circstd : float
        Circular standard deviation

    """

    warnings.warn(' '.join(["utils.stats.nan_circstd is deprecated and will",
                            "be removed in a future version. This function is",
                            "part of the scipy 1.4.0 milestones and will be",
                            "migrated there."]),
                  DeprecationWarning, stacklevel=2)

    samples = np.asarray(samples)
    samples = samples[~np.isnan(samples)]
    if samples.size == 0:
        return np.nan

    # Ensure the samples are in radians
    ang = (samples - low) * 2.0 * np.pi / (high - low)

    # Calculate the means of the sine and cosine, as well as the length
    # of their unit vector
    smean = np.sin(ang).mean(axis=axis)
    cmean = np.cos(ang).mean(axis=axis)
    rmean = np.sqrt(smean**2 + cmean**2)

    # Calculate the circular standard deviation
    circstd = (high - low) * np.sqrt(-2.0 * np.log(rmean)) / (2.0 * np.pi)
    return circstd
