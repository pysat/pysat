import importlib

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
            const = importlib.import_module('pysat.constellations.'+name)
            self.instruments = const.instruments

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

    def difference(self, instrument1, instrumet2, data_labels):
        # TODO Implement signal difference.
        raise NotImplementedError()
