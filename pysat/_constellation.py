
class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    FIXME document this.
    """
    def __init__(self, instruments = None, name = None):
        if instruments and name:
            raise ValueError('When creating a constellation, please specify a '
                             'list of instruments or a name, not both.')
        elif instruments and not hasattr(instruments, '__getitem__'):
            raise ValueError('Constellation: Instruments must be list-like.')
        elif not (name or instruments):
            raise ValueError('Constellation: Cannot create empty constellation.')

        # FIXME
        pass

    def __getitem__(self, **argv):
        return self.instruments.__getitem__(**argv)
    
    def __str__(self):
        # FIXME
        raise NotImplementedError()

    def __repr__(self):
        # FIXME
        raise NotImplementedError()
    
    def add(self, bounds1, label1, bounds2, label2, bin3, label3, 
            data_label):
        # FIXME
        raise NotImplementedError()

    def difference(self, instrument1, instrumet2, data_labels):
        # FIXME
        raise NotImplementedError()



