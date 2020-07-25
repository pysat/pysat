# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
"""
Instrument independent seasonal averaging routine. Supports averaging
1D and 2D data.
"""

import pysat
import numpy as np
import pandas as pds
import collections
import warnings


def median1D(const, bin1, label1, data_label, auto_bin=True, returnData=False):
    """Return a 1D median of data_label over a season and label1

    .. deprecated:: 2.2.0
      `median1D` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Parameters
    ----------
    const: Constellation or Instrument
        Constellation or Instrument object
    bin1: (array-like)
        List holding [min, max, number of bins] or array-like containing
        bin edges
    label1: (string)
        data column name that the binning will be performed over (i.e., lat)
    data_label: (list-like )
        contains strings identifying data product(s) to be averaged
    auto_bin: if True, function will create bins from the min, max and
              number of bins. If false, bin edges must be manually entered
    returnData : (boolean)
        Return data in output dictionary as well as statistics

    Returns
    -------
    median : dictionary
        1D median accessed by data_label as a function of label1
        over the season delineated by bounds of passed instrument objects.
        Also includes 'count' and 'avg_abs_dev' as well as the values of
        the bin edges in 'bin_x'

    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    # const is either an Instrument or a Constellation, and we want to
    #  iterate over it.
    # If it's a Constellation, then we can do that as is, but if it's
    #  an Instrument, we just have to put that Instrument into something
    #  that will yeild that Instrument, like a list.
    if isinstance(const, pysat.Instrument):
        const = [const]
    elif not isinstance(const, pysat.Constellation):
        raise ValueError("Parameter must be an Instrument or a Constellation.")

    # create bins
    # seems to create the boundaries used for sorting into bins
    if auto_bin:
        binx = np.linspace(bin1[0], bin1[1], bin1[2]+1)
    else:
        binx = np.array(bin1)

    # how many bins are used
    numx = len(binx)-1
    # how many different data products
    numz = len(data_label)

    # create array to store all values before taking median
    # the indices of the bins/data products? used for looping.
    xarr = np.arange(numx)
    zarr = np.arange(numz)
    # 3d array:  stores the data that is sorted into each bin? - in a deque
    ans = [[collections.deque() for i in xarr] for k in zarr]

    for inst in const:
        # do loop to iterate over instrument season
        # probably iterates by date but that all depends on the
        # configuration of that particular instrument.
        # either way, it iterates over the instrument, loading successive
        # data between start and end bounds
        for inst in inst:
            # collect data in bins for averaging
            if len(inst.data) != 0:
                # sort the data into bins (x) based on label 1
                # (stores bin indexes in xind)
                xind = np.digitize(inst.data[label1], binx) - 1
                # for each possible x index
                for xi in xarr:
                    # get the indicies of those pieces of data in that bin
                    xindex, = np.where(xind == xi)
                    if len(xindex) > 0:
                        # for each data product label zk
                        for zk in zarr:
                            # take the data (already filtered by x), select the
                            # data, put it in a list, and extend the deque
                            idata = inst.data.iloc[xindex]
                            ans[zk][xi].extend(idata[data_label[zk]].tolist())

    # Calculate the 1D median
    return _calc_1d_median(ans, data_label, binx, xarr, zarr, numx, numz,
                           returnData)


def median2D(const, bin1, label1, bin2, label2, data_label,
             returnData=False, auto_bin=True):
    """Return a 2D average of data_label over a season and label1, label2.

    .. deprecated:: 2.2.0
      `median2D` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Parameters
    ----------
        const: Constellation or Instrument
        bin#: [min, max, number of bins], or array-like containing bin edges
        label#: string
            identifies data product for bin#
        data_label: list-like
            contains strings identifying data product(s) to be averaged
        auto_bin: if True, function will create bins from the min, max and
                  number of bins. If false, bin edges must be manually entered

    Returns
    -------
    median : dictionary
        2D median accessed by data_label as a function of label1 and label2
        over the season delineated by bounds of passed instrument objects.
        Also includes 'count' and 'avg_abs_dev' as well as the values of
        the bin edges in 'bin_x' and 'bin_y'.

    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    # const is either an Instrument or a Constellation, and we want to
    #  iterate over it.
    # If it's a Constellation, then we can do that as is, but if it's
    #  an Instrument, we just have to put that Instrument into something
    #  that will yeild that Instrument, like a list.
    if isinstance(const, pysat.Instrument):
        const = [const]
    elif not isinstance(const, pysat.Constellation):
        raise ValueError("Parameter must be an Instrument or a Constellation.")

    # create bins
    # seems to create the boundaries used for sorting into bins
    if auto_bin:
        binx = np.linspace(bin1[0], bin1[1], bin1[2]+1)
        biny = np.linspace(bin2[0], bin2[1], bin2[2]+1)
    else:
        binx = np.array(bin1)
        biny = np.array(bin2)

    # how many bins are used
    numx = len(binx)-1
    numy = len(biny)-1
    # how many different data products
    numz = len(data_label)

    # create array to store all values before taking median
    # the indices of the bins/data products? used for looping.
    yarr = np.arange(numy)
    xarr = np.arange(numx)
    zarr = np.arange(numz)
    # 3d array:  stores the data that is sorted into each bin? - in a deque
    ans = [[[collections.deque() for i in xarr] for j in yarr] for k in zarr]

    for inst in const:
        # do loop to iterate over instrument season
        # probably iterates by date but that all depends on the
        # configuration of that particular instrument.
        # either way, it iterates over the instrument, loading successive
        # data between start and end bounds
        for inst in inst:
            # collect data in bins for averaging
            if len(inst.data) != 0:
                # sort the data into bins (x) based on label 1
                # (stores bin indexes in xind)
                xind = np.digitize(inst.data[label1], binx)-1
                # for each possible x index
                for xi in xarr:
                    # get the indicies of those pieces of data in that bin
                    xindex, = np.where(xind == xi)
                    if len(xindex) > 0:
                        # look up the data along y (label2) at that set of
                        # indices (a given x)
                        yData = inst.data.iloc[xindex]
                        # digitize that, to sort data into bins along y
                        # (label2) (get bin indexes)
                        yind = np.digitize(yData[label2], biny)-1
                        # for each possible y index
                        for yj in yarr:
                            # select data with this y index (and we already
                            # filtered for this x index)
                            yindex, = np.where(yind == yj)
                            if len(yindex) > 0:
                                # for each data product label zk
                                for zk in zarr:
                                    # take the data (already filtered by x)
                                    # filter it by y and
                                    # select the data product, put it in a
                                    # list, and extend the deque
                                    indlab = yData.columns.get_loc(data_label[zk])
                                    ans[zk][yj][xi].extend(yData.iloc[yindex,
                                                                      indlab].tolist())

    return _calc_2d_median(ans, data_label, binx, biny, xarr, yarr, zarr,
                           numx, numy, numz, returnData)


def _calc_2d_median(ans, data_label, binx, biny, xarr, yarr, zarr, numx,
                    numy, numz, returnData=False):

    # set up output arrays
    medianAns = [[[None for i in xarr] for j in yarr] for k in zarr]
    countAns = [[[None for i in xarr] for j in yarr] for k in zarr]
    devAns = [[[None for i in xarr] for j in yarr] for k in zarr]

    # all of the loading and storing data is done
    # determine what kind of data is stored
    # if just numbers, then use numpy arrays to store data
    # if the data is a more generalized object, use lists to store data
    # need to find first bin with data
    dataType = [None for i in np.arange(numz)]
    # for each data product label, find the first nonempty bin
    # and select its type
    for zk in zarr:
        breakNow = False
        for yj in yarr:
            for xi in xarr:
                if len(ans[zk][yj][xi]) > 0:
                    dataType[zk] = type(ans[zk][yj][xi][0])
                    breakNow = True
                    break
            if breakNow:
                break

    # determine if normal number objects are being used or if there
    # are more complicated objects
    objArray = [False] * len(zarr)
    for i, thing in enumerate(dataType):
        if thing == pds.core.series.Series:
            objArray[i] = 'S'
        elif thing == pds.core.frame.DataFrame:
            objArray[i] = 'F'
        else:
            # other, simple scalaRs
            objArray[i] = 'R'

    objArray = np.array(objArray)

    # if some pandas data series are returned in average, return a list
    objidx, = np.where(objArray == 'S')
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            for yj in yarr:
                for xi in xarr:
                    if len(ans[zk][yj][xi]) > 0:
                        ans[zk][yj][xi] = list(ans[zk][yj][xi])
                        medianAns[zk][yj][xi] = \
                            pds.DataFrame(ans[zk][yj][xi]).median(axis=0)
                        countAns[zk][yj][xi] = len(ans[zk][yj][xi])
                        devAns[zk][yj][xi] = \
                            pds.DataFrame([abs(temp - medianAns[zk][yj][xi])
                                           for temp in
                                           ans[zk][yj][xi]]).median(axis=0)

    # if some pandas DataFrames are returned in average, return a list
    objidx, = np.where(objArray == 'F')
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            for yj in yarr:
                for xi in xarr:
                    if len(ans[zk][yj][xi]) > 0:
                        ans[zk][yj][xi] = list(ans[zk][yj][xi])
                        countAns[zk][yj][xi] = len(ans[zk][yj][xi])
                        test = pds.Panel.from_dict(dict([(i, temp)
                                                   for i, temp in
                                                   enumerate(ans[zk][yj][xi])]))
                        medianAns[zk][yj][xi] = test.median(axis=0)
                        devAns[zk][yj][xi] = \
                            (test.subtract(medianAns[zk][yj][xi],
                                           axis=0)).abs().median(axis=0,
                                                                 skipna=True)

    objidx, = np.where(objArray == 'R')
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            medianAns[zk] = np.zeros((numy, numx))*np.nan
            countAns[zk] = np.zeros((numy, numx))*np.nan
            devAns[zk] = np.zeros((numy, numx))*np.nan
            for yj in yarr:
                for xi in xarr:
                    # convert deque storing data into numpy array
                    ans[zk][yj][xi] = np.array(ans[zk][yj][xi])
                    # filter out an NaNs in the arrays
                    idx, = np.where(np.isfinite(ans[zk][yj][xi]))
                    ans[zk][yj][xi] = (ans[zk][yj][xi])[idx]
                    # perform median averaging
                    if len(idx) > 0:
                        medianAns[zk][yj, xi] = np.median(ans[zk][yj][xi])
                        countAns[zk][yj, xi] = len(ans[zk][yj][xi])
                        devAns[zk][yj, xi] = np.median(abs(ans[zk][yj][xi] -
                                                       medianAns[zk][yj, xi]))

    # prepare output
    output = {}
    for i, label in enumerate(data_label):
        output[label] = {'median': medianAns[i],
                         'count': countAns[i],
                         'avg_abs_dev': devAns[i],
                         'bin_x': binx,
                         'bin_y': biny}

        if returnData:
            output[label]['data'] = ans[i]

    return output


# simple averaging through multiple iterations

def mean_by_day(inst, data_label):
    """Mean of data_label by day over Instrument.bounds

    .. deprecated:: 2.2.0
      `mean_by_day` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Parameters
    ----------
    data_label : string
        string identifying data product to be averaged

    Returns
    -------
    mean : pandas Series
        simple mean of data_label indexed by day

    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    return _core_mean(inst, data_label, by_day=True)


def mean_by_orbit(inst, data_label):
    """Mean of data_label by orbit over Instrument.bounds

    .. deprecated:: 2.2.0
      `mean_by_orbit` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Parameters
    ----------
    data_label : string
        string identifying data product to be averaged

    Returns
    -------
    mean : pandas Series
        simple mean of data_label indexed by start of each orbit

    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    return _core_mean(inst, data_label, by_orbit=True)


def mean_by_file(inst, data_label):
    """Mean of data_label by orbit over Instrument.bounds

    .. deprecated:: 2.2.0
      `mean_by_file` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Parameters
    ----------
    data_label : string
        string identifying data product to be averaged

    Returns
    -------
    mean : pandas Series
        simple mean of data_label indexed by start of each file

    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    return _core_mean(inst, data_label, by_file=True)


def _core_mean(inst, data_label, by_orbit=False, by_day=False, by_file=False):

    if by_orbit:
        iterator = inst.orbits
    elif by_day or by_file:
        iterator = inst
    else:
        raise ValueError('A choice must be made, by day, file, or orbit')

    # create empty series to hold result
    mean_val = pds.Series()
    # iterate over season, calculate the mean
    for inst in iterator:
        if not inst.data.empty:
            # compute mean absolute using pandas functions and store
            # data could be an image, or lower dimension, account for 2D
            # and lower
            data = inst[data_label]
            data.dropna(inplace=True)

            if by_orbit or by_file:
                date = inst.data.index[0]
            else:
                date = inst.date
            # perform average
            mean_val[date] = \
                pysat.ssnl.computational_form(data).mean(axis=0,
                                                         skipna=True)

    del iterator
    return mean_val


def _calc_1d_median(ans, data_label, binx, xarr, zarr, numx, numz,
                    returnData=False):
    """Calculate the 1D median

    Parameters
    ----------

    Returns
    ------

    Notes
    -----
    This is an overcomplicated way of doing this.  Try and simplify later

    """

    # set up output arrays
    medianAns = [[None for i in xarr] for k in zarr]
    countAns = [[None for i in xarr] for k in zarr]
    devAns = [[None for i in xarr] for k in zarr]

    # all of the loading and storing data is done
    # determine what kind of data is stored
    # if just numbers, then use numpy arrays to store data
    # if the data is a more generalized object, use lists to store data
    # need to find first bin with data
    dataType = [None for i in np.arange(numz)]
    # for each data product label, find the first nonempty bin
    # and select its type
    for zk in zarr:
        for xi in xarr:
            if len(ans[zk][xi]) > 0:
                dataType[zk] = type(ans[zk][xi][0])
                break

    # determine if normal number objects are being used or if there
    # are more complicated objects
    objArray = [False] * len(zarr)
    for i, thing in enumerate(dataType):
        if thing == pds.core.series.Series:
            objArray[i] = 'S'
        elif thing == pds.core.frame.DataFrame:
            objArray[i] = 'F'
        else:
            # other, simple scalaRs
            objArray[i] = 'R'

    objArray = np.array(objArray)

    # if some pandas data series are returned in average, return a list
    objidx, = np.where(objArray == 'S')
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            for xi in xarr:
                if len(ans[zk][xi]) > 0:
                    ans[zk][xi] = list(ans[zk][xi])
                    medianAns[zk][xi] = pds.DataFrame(ans[zk][xi]).median(axis=0)
                    countAns[zk][xi] = len(ans[zk][xi])
                    devAns[zk][xi] = pds.DataFrame([abs(temp
                                                        - medianAns[zk][xi]) \
                                    for temp in ans[zk][xi] ]).median(axis=0)

    # if some pandas DataFrames are returned in average, return a list
    objidx, = np.where(objArray == 'F')
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            for xi in xarr:
                if len(ans[zk][xi]) > 0:
                    ans[zk][xi] = list(ans[zk][xi])
                    countAns[zk][xi] = len(ans[zk][xi])
                    test = pds.Panel.from_dict(dict([(i, temp) for i, temp \
                                                    in enumerate(ans[zk][xi])]))
                    medianAns[zk][xi] = test.median(axis=0)
                    devAns[zk][xi] = \
                        (test.subtract(medianAns[zk][xi],
                                       axis=0)).abs().median(axis=0,
                                                             skipna=True)

    objidx, = np.where(objArray == 'R')
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            medianAns[zk] = np.full(numx, fill_value=np.nan)
            countAns[zk] = np.full(numx, fill_value=np.nan)
            devAns[zk] = np.full(numx, fill_value=np.nan)
            for xi in xarr:
                # convert deque storing data into numpy array
                ans[zk][xi] = np.array(ans[zk][xi])
                # filter out an NaNs in the arrays
                idx, = np.where(np.isfinite(ans[zk][xi]))
                ans[zk][xi] = (ans[zk][xi])[idx]
                # perform median averaging
                if len(idx) > 0:
                    medianAns[zk][xi] = np.median(ans[zk][xi])
                    countAns[zk][xi] = len(ans[zk][xi])
                    devAns[zk][xi] = np.median(abs(ans[zk][xi] -
                                                   medianAns[zk][xi]))

    # prepare output
    output = {}
    for i, label in enumerate(data_label):
        output[label] = {'median': medianAns[i],
                         'count': countAns[i],
                         'avg_abs_dev': devAns[i],
                         'bin_x': binx}

        if returnData:
            output[label]['data'] = ans[i]

    return output
