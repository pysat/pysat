
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
        return "Constellation({})".format(repr(self.instruments))

    def add(self, bounds1, label1, bounds2, label2, bin3, label3,
            data_label):
        # TODO Implement signal addition.
        raise NotImplementedError()

    def difference(self, instrument1, instrumet2, data_labels):
        # TODO Implement signal difference.
        raise NotImplementedError()
