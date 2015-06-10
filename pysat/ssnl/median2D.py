# -*- coding: utf-8 -*-
"""
Instrument independent seasonal averaging routine. Supports averaging
1D and 2D data.
"""

import pysat
import numpy as np
import pandas as pds
import collections

def median2D(inst, bin1, label1, bin2, label2, data_label, start=None, stop=None, returnBins=False, returnData=False):
    """Return a 2D average of data_label over a season.

    Arguments:
        bin#: [min, max, number of bins]
        label#: string identifying data product for bin#
        data_label: list containing strings identifying data product(s) to be 
                    averaged

    Summary:
        Returns a 2D average of data_label as a function of label1 and label2 
        over the season delineated by bounds of passed instrument objects.
    
    """
    
    
    #create bins
    binx = np.linspace(bin1[0], bin1[1], bin1[2]+1)
    biny = np.linspace(bin2[0], bin2[1], bin2[2]+1)

    numx = len(binx)-1
    numy = len(biny)-1
    numz = len(data_label)

    #create array to store all values before taking median
    yarr = np.arange(numy)
    xarr = np.arange(numx)
    zarr = np.arange(numz)
    ans = [ [ [collections.deque() for i in xarr] for j in yarr] for k in zarr]

    #set up output arrays
    medianAns = [ [ [ None for i in xarr] for j in yarr] for k in zarr]
    countAns = [ [ [ None for i in xarr] for j in yarr] for k in zarr]
    devAns = [ [ [ None for i in xarr] for j in yarr] for k in zarr]    

    # do loop to iterate over instrument season
    for inst in inst:
        #collect data in bins for averaging
        if len(inst.data) != 0:
            xind = np.digitize(inst.data[label1], binx)-1
            for xi in xarr:
                xindex, = np.where(xind==xi)
                if len(xindex)>0:
                    yData = inst.data.iloc[xindex]
                    yind = np.digitize(yData[label2], biny)-1
                    for yj in yarr:
                        yindex, = np.where(yind==yj)
                        if len(yindex)>0:
                            for zk in zarr:
                                #print 'extend'
                                ans[zk][yj][xi].extend( yData.ix[yindex,data_label[zk]].tolist() )


    #all of the loading and storing data is done
    #determine what kind of data is stored
    #if just numbers, then use numpy arrays to store data
    #if the data is a more generalized object, use lists to store data
    #need to find first bin with data
    dataType = [None for i in np.arange(numz)]
    for zk in zarr:
        breakNow=False
        for yj in yarr:
            for xi in xarr:
                print len(ans[zk][yj][xi])
                if len(ans[zk][yj][xi]) > 0:
                    #print ans[zk][yj][xi]
                    dataType[zk] = type(ans[zk][yj][xi][0]) 
                    breakNow = True
                    break 
            if breakNow:
                break
 
      
    #determine if normal number objects are being used or if there are more complicated objects
    objArray = np.zeros(len(zarr))
    objArray = [False]*len(zarr)
    #objArray[:] = False
    for (i,thing) in enumerate(dataType):
         print 'type ', thing
         if thing == pds.core.series.Series:
            objArray[i] = 'Series'
         if thing == pds.core.frame.DataFrame:
            objArray[i] = 'Frame'
    print 'objArray ', objArray 
    objArray = np.array(objArray) 
    # if some pandas data series are returned in average, return a list
    objidx, = np.where(objArray == 'Series')
    if len(objidx) > 0:
        print 'Series'
        for zk in zarr[objidx]:
            for yj in yarr:
                for xi in xarr:
                    if len(ans[zk][yj][xi]) > 0:
                        ans[zk][yj][xi] = list(ans[zk][yj][xi])
                        medianAns[zk][yj][xi] =  pds.DataFrame(ans[zk][yj][xi] ).median(axis=0)
                        countAns[zk][yj][xi] = len(ans[zk][yj][xi])
                        devAns[zk][yj][xi] = pds.DataFrame([abs(temp) - medianAns[zk][yj][xi] for temp in ans[zk][yj][xi] ] ).median(axis=0)
                                                                    
    # if some pandas DataFrames are returned in average, return a list
    objidx, = np.where(objArray == 'Frame')
    if len(objidx) > 0:
        print 'Frame'
        for zk in zarr[objidx]:
            for yj in yarr:
                for xi in xarr:                    
                    if len(ans[zk][yj][xi]) > 0:
                        ans[zk][yj][xi] = list(ans[zk][yj][xi])
                        countAns[zk][yj][xi] = len(ans[zk][yj][xi])
                        test = pds.Panel.from_dict(dict([(i,temp) for i,temp in enumerate(ans[zk][yj][xi]) ]) )
                        medianAns[zk][yj][xi] = test.median(axis=0)
                        devAns[zk][yj][xi] = (test.subtract(medianAns[zk][yj][xi], axis=0)).abs().median(axis=0, skipna=True)
                                                                                                      
    objidx, = np.where(objArray == False)
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            medianAns[zk] = np.zeros((numy, numx))*np.nan
            countAns[zk] = np.zeros((numy, numx))*np.nan
            devAns[zk] = np.zeros((numy, numx))*np.nan
            for yj in yarr:
                for xi in xarr:
                    #convert deque storing data into numpy array
                    ans[zk][yj][xi] = np.array(ans[zk][yj][xi])
                    #filter out an NaNs in the arrays
                    idx, = np.where(np.isfinite(ans[zk][yj][xi]))
                    ans[zk][yj][xi] = (ans[zk][yj][xi])[idx]
                    #perform median averaging
                    if len(idx) > 0:
                        medianAns[zk][yj,xi] = np.median(ans[zk][yj][xi])
                        countAns[zk][yj,xi] = len(ans[zk][yj][xi])
                        devAns[zk][yj,xi] = np.median(abs(ans[zk][yj][xi] - medianAns[zk][yj,xi]))
    
    #if returnData:
    #    return medianAns, devAns, countAns, binx, biny, ans
    #elif returnBins:
    #    return medianAns, devAns, countAns, binx, biny
    #else:
    #    return medianAns, devAns, countAns
    
    output = {}
    for i,label in enumerate(data_label):
        output[label] = {'median': medianAns[i], 
                        'count':countAns[i],
                        'avg_abs_dev':devAns[i]}

        if returnData:
            output[label]['data'] = ans[i]
            returnBins = True
        if returnBins:
            output[label]['binx'] = binx
            output[label]['biny'] = biny
    return output   


def old_median2D(inst, start, stop, bin1, label1, bin2, label2, data_label, returnBins=False, returnData=False):
    """Return a 2D average of data_label over a season.

    Arguments:
        Start: Start Date(s) - datetime object
        Stop: Stop Date(s) - datetime object
        binx: [min, max, number of bins]
        labelx: string identifying data product for binx
        data_label: string identifying data product to be averaged

    Summary:
        Returns a 2D average of data_label as a function of label1 and label2 over the season delineated by start and stop datetime objects."""
    #create bins
    binx = linspace(bin1[0], bin1[1], bin1[2]+1)
    biny = linspace(bin2[0], bin2[1], bin2[2]+1)

    numx = len(binx)-1
    numy = len(biny)-1
    numz = len(data_label)

    #create array to store all values before taking median
    yarr = np.arange(numy)
    xarr = np.arange(numx)
    zarr = np.arange(numz)
    ans = [ [ [np.array([]) for i in xarr] for j in yarr] for k in zarr]



    # do loop to iterate over given days
    # start data in start, end day in stop
    season = pysat.getDateArray(start, stop, freq='D')
    for i,date in enumerate(season):

        inst.getData(date=date)

        #bin data for averaging
        if len(inst.data) != 0:
            xind = np.digitize(inst.data[label1], binx)-1
            for xi in xarr:
                xindex, = np.where(xind==xi)
                if len(xindex)>0:
                    yData = inst.data.ix[xindex]
                    yind = np.digitize(yData[label2], biny)-1
                    for yj in yarr:
                        yindex, = np.where(yind==yj)
                        if len(yindex)>0:
                            for zk in zarr:
                                ans[zk][yj][xi] = hstack([ans[zk][yj][xi],yData.ix[yindex,data_label[zk]] ])

    #all of the loading and storing data is done
    #now, iterate through the and elements and generate median
    medianAns = zeros((numz, numy, numx))*np.nan#2d numpy array
    countAns = zeros((numz, numy, numx))*np.nan
    devAns = zeros((numz, numy, numx))*np.nan
    #print numx, numy
    #print xarr
    for zk in zarr:
        for yj in yarr:
            for xi in xarr:
                #print xi,yj
                #filter out an NaNs in the arrays
                idx, = np.where(np.isfinite(ans[zk][yj][xi]))
                ans[zk][yj][xi] = (ans[zk][yj][xi])[idx]
                #perform median averaging
                if len(idx) > 0:
                    medianAns[zk,yj,xi] = median(ans[zk][yj][xi])
                    countAns[zk,yj,xi] = len(ans[zk][yj][xi])
                    devAns[zk,yj,xi] = median(abs(ans[zk][yj][xi] - medianAns[zk,yj,xi]))
    
    if returnData:
        return medianAns, devAns, countAns, binx, biny, ans
    if returnBins:
        #return medianAns, devAns, countAns, binx[0:-1]+(binx[1]-binx[0])/2., biny[0:-1]+(biny[1]-biny[0])/2.
        return medianAns, devAns, countAns, binx, biny
    else:
        return medianAns, devAns, countAns



def alternateMedian2D(inst, start, stop, bin1, label1, bin2, label2, data_label, returnBins=False, returnData=False):
    """Return a 2D average of data_label over a season.

    Arguments:
        Start: Start Date(s) - datetime object
        Stop: Stop Date(s) - datetime object
        binx: [min, max, number of bins]
        labelx: string identifying data product for binx
        data_label: list containing strings identifying data product(s) to be averaged

    Summary:
        Returns a 2D average of data_label as a function of label1 and label2 over the season delineated by start and stop datetime objects."""
    #create bins
    binx = linspace(bin1[0], bin1[1], bin1[2]+1)
    biny = linspace(bin2[0], bin2[1], bin2[2]+1)

    numx = len(binx)-1
    numy = len(biny)-1
    numz = len(data_label)

    #create array to store all values before taking median
    yarr = np.arange(numy)
    xarr = np.arange(numx)
    zarr = np.arange(numz)
    ans = [ [ [[] for i in xarr] for j in yarr] for k in zarr]

    #set up output arrays
    medianAns = [ [ [ None for i in xarr] for j in yarr] for k in zarr]
    countAns = [ [ [ None for i in xarr] for j in yarr] for k in zarr]
    devAns = [ [ [ None for i in xarr] for j in yarr] for k in zarr]    

    # do loop to iterate over given days
    # start data in start, end day in stop
    season = pysat.getDateArray(start, stop, freq='D')
    for i,date in enumerate(season):

        #load data
        inst.getData(date=date)

        #collect data in bins for averaging
        if len(inst.data) != 0:
            xind = np.digitize(inst.data[label1], binx)-1
            for xi in xarr:
                xindex, = np.where(xind==xi)
                if len(xindex)>0:
                    yData = inst.data.ix[xindex]
                    yind = np.digitize(yData[label2], biny)-1
                    for yj in yarr:
                        yindex, = np.where(yind==yj)
                        if len(yindex)>0:
                            for zk in zarr:
                                ans[zk][yj][xi] += yData.ix[yindex,data_label[zk]].tolist() 

        #method below works but it is slower than the more verbose code above
        ##determine index numbers for each of the datasets that define the bins
        #subData = inst.data[data_label]
        #xidx = np.digitize(inst.data[label1], binx)-1
        #yidx = np.digitize(inst.data[label2], biny)-1
        #
        ##group all data by the bins
        #subGroup = subData.groupby([xidx, yidx])
        #
        ##if there is actual data, do stuff
        #if len(subGroup.groups) > 0:
        #    for zk in zarr:
        #        for (name, group) in subGroup:
        #            ans[zk][name[1]][name[0]] += group[data_label[zk]].tolist()      


    #all of the loading and storing data is done
    #now, iterate through the elements and generate median    
    
    
    #determine what kind of data is stored
    #if just numbers, then use numpy arrays to store data
    #if the data is a more generalized object, use lists to store data
    #need to find first bin with data
    dataType = [None for i in arange(numz)]
    for zk in zarr:
        breakNow=False
        for yj in yarr:
            for xi in xarr:
                if len(ans[zk][yj][xi]) > 0:
                    dataType[zk] = type(ans[zk][yj][xi][0]) 
                    breakNow = True
                    break 
            if breakNow:
                break
        #if breakNow:
        #    break   
      
    #determine if normal number objects are being used or if there are more complicated objects
    objArray = np.zeros(len(zarr))
    objArray[:] = False
    for (i,thing) in enumerate(dataType):
        print thing
        if thing == pds.core.series.Series:
            objArray[i] = True
      
    #if some pandas data series are returned in average, return a list
    objidx, = where(objArray == True)
    #objidx = np.arange(numz)
    if len(objidx) > 0:
        #print 'Found some Series objects!'
        #print 'Just outside outer object loop'
        #print zarr, objidx, zarr[objidx], objArray
        for zk in zarr[objidx]:
            #print 'Entering outermost object loop'
            for yj in yarr:
                for xi in xarr:
                    if len(ans[zk][yj][xi]) > 0:
                        medianAns[zk][yj][xi] =  pds.DataFrame(ans[zk][yj][xi] ).median(axis=0)
                        countAns[zk][yj][xi] = len(ans[zk][yj][xi])
                        devAns[zk][yj][xi] = pds.DataFrame([abs(temp) - medianAns[zk][yj][xi] for temp in ans[zk][yj][xi] ] ).median(axis=0)
                                                                    
                                                                                                                                       

    objidx, = where(objArray == False)
    if len(objidx) > 0:
        for zk in zarr[objidx]:
            medianAns[zk] = zeros((numy, numx))*np.nan
            countAns[zk] = zeros((numy, numx))*np.nan
            devAns[zk] = zeros((numy, numx))*np.nan
            for yj in yarr:
                for xi in xarr:
                    #convert lists storing data into numpy array
                    ans[zk][yj][xi] = np.array(ans[zk][yj][xi])
                    #filter out an NaNs in the arrays
                    idx, = np.where(np.isfinite(ans[zk][yj][xi]))
                    ans[zk][yj][xi] = (ans[zk][yj][xi])[idx]
                    #perform median averaging
                    if len(idx) > 0:
                        medianAns[zk][yj,xi] = median(ans[zk][yj][xi])
                        countAns[zk][yj,xi] = len(ans[zk][yj][xi])
                        devAns[zk][yj,xi] = median(abs(ans[zk][yj][xi] - medianAns[zk][yj,xi]))
    
    if returnData:
        return medianAns, devAns, countAns, binx, biny, ans
    elif returnBins:
        return medianAns, devAns, countAns, binx, biny
    else:
        return medianAns, devAns, countAns



