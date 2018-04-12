
class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.
        print(repr(med1)) #FIXME

    FIXME document this.
    Created as part of a Spring 2018 UTDesign project.
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
        label1 : string
            Data label for bounds1 to act on.
        bounds2 : (min, max)
            Bounds for selecting data on the axis of label2
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

        # TODO Implement signal addition.
        raise NotImplementedError()

    def difference(self, instrument1, instrument2, data_labels):
        """
        Calculates the difference in signals from multiple
        instruments within the given bounds.

        TODO more doc

        Parameters
        ----------
        s1 : Instrument
            Information must already be loaded into the 
            instrument.
        
        s2 : Instrument
            Information must already be loaded into the 
            instrument.

        data_labels : list of tuples of data labels
            The first key is used to access data in s1 
            and the second data in s2.

        bounds : (min_time, max_time, min_lat, max_lat,
                  min_long, max_long, min_alt, max_alt)
        
        translate : dict
            User provides dict translate maps
            ("time", "lat", "long", "alt", "time2", "lat2",
            "long2", "alt2") to their respective data labels
            on their respectives s1, s2. # XXX rewrite
        
        Pseudocode
        ----------
        Check integrity of inputs.

        Let STD_LABELS be the constant tuple:
        ("time", "lat", "long", "alt")
        
        Note: modify so that user can override labels for time,
        lat, long, data for each satelite.
        
        // We only care about the data currently loaded
           into each object.
        
        Let start be the later of the datetime of the
         first piece of data loaded into s1, the first
         piece of data loaded into s2, and the user
         supplied start bound.
        
        Let end be the later of the datetime of the first
         piece of data loaded into s1, the first piece
         of data loaded into s2, and the user supplied
         end bound.

        If start is after end, raise an error.
        
        // Let data be the 2D array of deques holding each piece
        //  of data, sorted into bins by lat/long/alt.
        
        Let s1_data (resp s2_dat) be data from s1.data, s2.data
        filtered by user-provided lat/long/alt bounds, time bounds
        calculated.

        Let data be a dictionary of lists with the keys
        [ dl1 for dl1, dl2 in data_labels ] +
        STD_LABELS + 
        [ lb+"2" for lb in STD_LABELS ]
        
        For each piece of data s1_point in s1_data:
        
            # Hopefully np.where is very good, because this
            #  runs O(n) times.
            # We could try reusing selections, maybe, if needed.
            #  This would probably involve binning.
            Let s2_near be the data from s2.data within certain
             bounds on lat/long/alt/time using 8 statements to
             numpy.where. We can probably get those defaults from
             the user or handy constants / config?
        
            # XXX we could always try a different closest 
            #  pairs algo
        
            Let distance be the numpy array representing the
             distance between s1_point and each point in s2_near.
        
            # S: Difference for others: change this line.
            For each of those, calculate the spatial difference 
             from the s1 using lat/long/alt. If s2_near is 
             empty; break loop.
        
            Let s2_nearest be the point in s2_near corresponding
             to the lowest distance.
        
            Append to data: a point, indexed by the time from
             s1_point, containing the following data:
        
            # note
            Let n be the length of data["time"].
            For each key in data:
                Assert len(data[key]) == n
            End for.
        
            # Create data row to pass to pandas.
            Let row be an empty dict.
            For dl1, dl2 in data_labels:
                Append s1_point[dl1] - s2_nearest[dl2] to data[dl1].
        
            For key in STD_LABELS:
                Append s1_point[translate[key]] to data[key]
                key = key+"2"
                Append s2_nearest[translate[key]] to data[key]
        
        Let data_df be a pandas dataframe created from the data
        in data.
        
        return { 'data': data_df, 'start':start, 'end':end }

        Created as part of a Spring 2018 UTDesign project.
        """
        numPoints1 = instrument1.data[data_labels[0][0]]
        numPoints2 = instrument2.data[data_labels[1][0]]
        for i in range(len(numPoints)):
            #gets instrument1 data point
            s1_point = [instrument1.data[dl[0]][i] for dl in data_labels]
            
            #gets indices of points in instrument2 within the given bounds
            #b = (min, max, label)
            s2_near = np.arange(numPoints2)
            for b in bounds:
                data2 = instrument2.data[b[2]]
                minbound = b[0]
                maxbound = b[1]
                indices = np.where((data2 >= minbound) & (data2 < maxbound))
                s2_near = np.intersect1D(s2_near, indices)

            


        
    
