#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
""" Created as part of a Spring 2018 UTDesign project.
"""

import numpy as np


class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    Parameters
    ----------
    const_module : string
        Name of a pysat constellation module
    instruments : list-like
        A list of pysat Instruments to include in the Constellation

    Attributes
    ----------
    instruments : list
        A list of pysat Instruments that make up the Constellation
    bounds : (datetime/filename/None, datetime/filename/None)
        bounds for loading data, supply array_like for a season with gaps.
        Users may provide as a tuple or tuple of lists, but the attribute is
        stored as a tuple of lists for consistency

    """

    # -----------------------------------------------------------------------
    # Define the magic methods

    def __init__(self, const_module=None, instruments=None):
        """
        Constructs a Constellation given a list of instruments or the name of
        a file with a pre-defined constellation.

        Parameters
        ----------
        const_module : string
            Name of a pysat constellation module
        instruments : list-like
            A list of pysat Instruments to include in the Constellation

        Raises
        ------
        ValueError
            When `instruments` is not list-like

        Note
        ----
        Omit `instruments` and `const_module` to create an empty constellation.

        """

        # Include Instruments from the constellation module, if it exists
        if const_module is not None:
            if not hasattr(const_module, 'instruments'):
                raise AttributeError("missing required attribute 'instruments'")
            self.instruments = const_module.instruments
        else:
            self.instruments = []

        # Add any Instruments provided in the list
        if instruments is not None:
            test_instruments = np.asarray(instruments)
            if test_instruments.shape == ():
                raise ValueError('instruments argument must be list-like')

            self.instruments.extend(list(instruments))

        return

    def __getitem__(self, *args, **kwargs):
        """
        Look up a member Instrument by index.

        """

        return self.instruments.__getitem__(*args, **kwargs)

    def __repr__(self):
        """ Print the basic Constellation properties

        """

        out_str = "".join(["pysat.Constellation(instruments=",
                           "{:})".format(self.instruments)])
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

    # -----------------------------------------------------------------------
    # Define the public methods and properties

    @property
    def bounds(self):
        return self.instruments[0].bounds

    @bounds.setter
    def bounds(self, value=None):
        """ Sets boundaries for all Instruments in Constellation

        Parameters
        ----------
        value : tuple or NoneType
            Tuple containing starting time and ending time for Instrument
            bounds attribute or None (default=None)

        """

        for instrument in self.instruments:
            instrument.bounds = value

        return

    def custom_attach(self, *args, **kwargs):
        """Register a function to modify data of member Instruments.

        Parameters
        ----------
        *args : list reference
            References a list of input arguments
        **kwargs : dict reference
            References a dict of input keyword arguments

        See Also
        ---------
        Instrument.custom_attach : base method for attaching custom functions

        """

        for instrument in self.instruments:
            instrument.custom_attach(*args, **kwargs)

        return

    def custom_clear(self):
        """Clear the custom function list

        See Also
        ---------
        Instrument.custom_clear : base method for clearing custom functions

        """

        for instrument in self.instruments:
            instrument.custom_clear()

        return

    def load(self, *args, **kwargs):
        """ Load instrument data into Instrument object.data

        Parameters
        ----------
        *args : list reference
            References a list of input arguments
        **kwargs : dict reference
            References a dict of input keyword arguments

        See Also
        ---------
        Instrument.load : base method for loading Instrument data

        """

        for instrument in self.instruments:
            instrument.load(*args, **kwargs)

        return
