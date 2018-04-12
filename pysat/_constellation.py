import collections
import importlib
import numpy as np
from pysat.ssnl.avg import _calc_2d_median

class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    FIXME document this.
    """
    def __init__(self, instruments=None, name=None):
        """
        Constructs a Constellation given a list of instruments or the name of
        a file with a pre-defined constellation.

        Parameters
        ----------
        instruments : list
            a list of pysat Instruments
        name : string
            Name of a file in pysat/constellations containing a list of 
            instruments. 
        
        Note
        ----
        The name and instruments parameters should not both be set. 
        If neither is given, an empty constellation will be created.
        """
        
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
            const = importlib.import_module('pysat.constellations.'+name)
            self.instruments = const.instruments

    def __getitem__(self, *args, **kwargs):
        return self.instruments.__getitem__(*args, **kwargs)

    def __str__(self):
        """
        Print names of instruments within constellation
        """
        output_str = '\npysat Constellation object:\n'

        for instr in self.instruments:
            output_str += instr.name + '\n'

        return output_str

    def set_bounds(self, start, stop)
        """
        Sets boundaries for all instruments in constellation
        """
        for instrument in self.instruments:
            instrument.bounds = (start, stop)

    def data_mod(self, function, *args, kind='add', at_pos='end', **kwargs):
        for instrument in self.instruments:
            instrument.custom.add(function, *args, kind, at_pos, **kwargs)

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
        data_label : array of strings
            Data label(s) for data product(s) to be averaged.

        Returns
        -------
        median : dictionary

        """
        # TODO document return more
        # TODO insert type checks

        if isinstance(data_label, str):
            data_label = [data_label,]
        elif not isinstance(data_label, collections.Sequence):
            raise ValueError("Please pass data_label as a string or "
                             "collection of strings.")

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
        ans = [[[collections.deque()] for j in yarr] for k in zarr]

        # Filter data by bounds and bin it.
        # Idiom for loading all of the data in an instrument's bounds.
        for inst in self:
            for inst in inst:
                if len(inst.data) != 0:
                    # Select indicies for each piece of data we're interest in.
                    # Not all of this data is in bounds on label3 but we'll
                    #  sort this later.
                    min1, max1 = bounds1
                    min2, max2 = bounds2
                    data1 = inst.data[label1]
                    data2 = inst.data[label2]
                    in_bounds, = np.where((min1 <= data1) & (data1 < max1) &
                                          (min2 <= data2) & (data2 < max2))
                    # Grab the data in bounds on data1, data2.
                    data_considered = inst.data.iloc[in_bounds]

                    y_indexes = np.digitize(data_considered[label3], biny) -1

                    # Iterate over the bins along y
                    for yj in yarr:
                        # Indicies of data in this bin
                        yindex, = np.where(y_indexes == yj)

                        # If there's data in this bin
                        if len(yindex) > 0:

                            # For each data label, add the points.
                            for zk in zarr:
                                ans[zk][yj][0].extend(
                                    data_considered.ix[yindex, data_label[zk]].tolist())

        # Now for the averaging.
        # Let's, try .. packing the answers for the 2d function.
        numx = 1
        xarr = np.arange(numx)
        binx = None

        # TODO modify output
        out_2d = _calc_2d_median(ans, data_label, binx, biny, xarr, yarr, zarr, numx, numy, numz)

        # Transform output
        output = {}
        for i, label in enumerate(data_label):
            median = [r[0] for r in out_2d[label]['median']]
            count  = [r[0] for r in out_2d[label]['count']]
            dev     = [r[0] for r in out_2d[label]['avg_abs_dev']]
            output[label] = {'median':  median,
                             'count':   count,
                             'avg_abs_dev': dev,
                             'bin':     out_2d[label]['bin_y']}
        return output

    def difference(self, instrument1, instrumet2, data_labels):
        # TODO Implement signal difference.
        raise NotImplementedError()
