
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

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return self.data.ix[key[0], key[1]]
        else:
            return self.data[key]
