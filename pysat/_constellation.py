
class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    FIXME document this.
    """
    def __init__(self, instruments=None, name=None):
        if instruments and name:
            raise ValueError('When creating a constellation, please specify '
                             'a list of instruments or a name, not both.')
        elif instruments and not hasattr(instruments, '__getitem__'):
            raise ValueError('Constellation: Instruments must be list-like.')
        elif not (name or instruments):
            raise ValueError('Constellation: Cannot create empty '
                             'constellation.')

        if instruments:
            self.instruments = instruments
        else:
            # TODO Implement constellation lookup by name.
            raise NotImplementedError()

    def __getitem__(self, *args, **kwargs):
        return self.instruments.__getitem__(*args, **kwargs)

    def __str__(self):
        # TODO Implement conversion to string.
        raise NotImplementedError()

    def __repr__(self):
        # TODO Implement __repr__
        raise NotImplementedError()

    def data_mod(self, function, kind='add', at_pos='end', *args, **kwargs):
        for instrument in self.instruments:
            instrument.custom.add(function, kind, at_pos, *args, **kwargs)

    def load(self, *args, **kwargs):
        for instrument in self.instruments:
            instrument.load(*args, **kwargs)

    def add(self, bounds1, label1, bounds2, label2, bin3, label3, 
            data_label):
        """
        Combines signals from multiple instruments within 
        given bounds.

        Parameters
        ----------
        bounds1 : (min, max)
            Bounds for selecting data on the axis of label1
            Data points with label1 in [min, max) will be considered.
        label1 : string
            Data label for bounds1 to act on.
        bounds2 : (min, max)
            Bounds for selecting data on the axis of label2
            Data points with label1 in [min, max) will be considered.
        label2 : string
            Data label for bounds2 to act on.
        bin3 : (min, max, #bins)
            Min and max bounds and number of bins for third axis.
        label3 : string
            Data label for third axis.
        data_label : string
            Data label for data product to be averaged.

        Returns
        -------
        median : dictionary
            
        """
        # XXX double check that we like that name
        # TODO document return more
        # TODO check that Dr Stoneback is ok with bounds [,)

        # TODO insert type checks

        # Modeled after pysat.ssnl.median2D

        # Make bin boundaries.
        # y: values at label3
        # z: *data_labels 
        biny = np.linspace(bin3[0], bin3[1], bin3[2]+1)

        numy = len(biny)-1
        numz = len(data_label)

        # Ranges
        yarr, zarr = map(np.arange, (numy, numz))

        # Store data here.
        ans = [ [collections.deque() for j in yarr] or k in zarr]

        # Filter data by bounds and bin it.
        # Idiom for loading all of the data in an instrument's bounds.
        for inst in inst: 
            if len(inst.data) != 0:
                # Select indicies for each piece of data we're interest in.
                # Not all of this data is in bounds on label3 but we'll 
                #  sort this later.
                min1, max1 = bounds1
                min2, max2 = bounds2
                data1 = inst.data[label1]
                data2 = inst.data[label2]
                in_bounds, = np.where(data1 <= min1 and min1 < data1 and
                                      data2 <= min2 and min2 < data2)
                # Grab the data in bounds on data1, data2.
                data_considered, = inst.data.iloc[inbounds]

                y_indexes = np.digitize(data_considered[label3], biny)

                # Iterate over the bins along y
                for yj in yarr:
                    # Indicies of data in this bin
                    yindex, = np.where(y_indexes==yi)

                    # If there's data in this bin
                    if len(yindex) > 0:

                        # For each data label, add the points.
                        for zk in zarr:
                            # XXX what is .ix
                            ans[yj][zk].extend( data_considered.ix[yindex,data_label[zk]].tolist())

        # Now for the averaging.
        # Let's, try .. packing the answers for the 2d function.
        ans = [ans,]
        numx = 1
        xarr = np.arange(numx)
        binx = None

        # TODO modify output
        return _calc_2d_median(ans, data_label, binx, biny, xarr, yarr, zarr, numx, numy, numz)

        # TODO Implement signal addition.
        raise NotImplementedError()

    def difference(self, instrument1, instrumet2, data_labels):
        # TODO Implement signal difference.
        raise NotImplementedError()
