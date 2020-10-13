import importlib


class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    Created as part of a Spring 2018 UTDesign project.

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

        if instruments:
            self.instruments = instruments
        elif name:
            const = importlib.import_module('pysat.constellations.' + name)
            self.instruments = const.instruments
        else:
            self.instruments = []

    def __getitem__(self, *args, **kwargs):
        """
        Look up a member Instrument by index.

        """

        return self.instruments.__getitem__(*args, **kwargs)

    def __repr__(self):
        """ Print the basic Constellation properties

        """

        out_str = "Constellation(instruments={:}) -> {:d} Instruments".format(
            self.instruments, len(self.instruments))
        return out_str

    def __str__(self):
        """ Print names of instruments within constellation

        """

        output_str = 'pysat Constellation object:\n'
        output_str += '---------------------------\n'

        ninst = len(self.instruments)

        if ninst > 0:
            output_str += "\nIndex Platform Name Tag Inst_ID\n"
            output_str += "-------------------------------\n"
            for i, inst in enumerate(self.instruments):
                output_str += "{:d} '{:s}' '{:s}' '{:s}' '{:s}'\n".format(
                    i, inst.platform, inst.name, inst.tag, inst.inst_id)
        else:
            output_str += "No loaded Instruments\n"

        return output_str

    def set_bounds(self, start, stop):
        """ Sets boundaries for all instruments in constellation

        Parameters
        ----------
        start : dt.datetime
            Starting time for Instrument bounds attribute
        stop : dt.datetime
            Ending time for Instrument bounds attribute

        """

        for instrument in self.instruments:
            instrument.bounds = (start, stop)

    def data_mod(self, *args, **kwargs):
        """
        Register a function to modify data of member Instruments.

        The function is not partially applied to modify member data.

        When the Constellation receives a function call to register
        a function for data modification, it passes the call to each
        instrument and registers it in the instrument's pysat.Custom queue.

        (Wraps pysat.Custom.attach; documentation of that function is
        reproduced here.)

        Parameters
        ----------
            function : string or function object
                name of function or function object to be added to queue

            kind : {'add, 'modify', 'pass'}
                - add
                    Adds data returned from fuction to instrument object.
                - modify
                    pysat instrument object supplied to routine. Any and all
                    changes to object are retained.
                - pass
                    A copy of pysat object is passed to function. No
                    data is accepted from return.

            at_pos : string or int
                insert at position. (default, insert at end).
            args
                extra arguments

        Note
        ----
        Allowed `add` function returns:

        - {'data' : pandas Series/DataFrame/array_like,
          'units' : string/array_like of strings,
          'long_name' : string/array_like of strings,
          'name' : string/array_like of strings (iff data array_like)}

        - pandas DataFrame, names of columns are used

        - pandas Series, .name required

        - (string/list of strings, numpy array/list of arrays)

        """

        for instrument in self.instruments:
            instrument.custom.attach(*args, **kwargs)

    def load(self, *args, **kwargs):
        """
        Load instrument data into instrument object.data

        (Wraps pysat.Instrument.load; documentation of that function is
        reproduced here.)

        Parameters
        ----------
        yr : integer
            Year for desired data
        doy : integer
            day of year
        data : datetime object
            date to load
        fname : string
            filename to be loaded
        verifyPad : boolean
            if true, padding data not removed (debug purposes)

        """

        for instrument in self.instruments:
            instrument.load(*args, **kwargs)
