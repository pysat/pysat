#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
""" Class for Instrument constellations

Note
----
Started as part of a Spring 2018 UTDesign project.
Updated by AGB, May 2021, NRL

"""

import datetime as dt
import numpy as np
import pandas as pds

from pysat import utils


class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    Parameters
    ----------
    const_module : module or NoneType
        Name of a pysat constellation module (default=None)
    instruments : list-like or NoneType
        A list of pysat Instruments to include in the Constellation
        (default=None)
    index_res : float or NoneType
        Output index resolution in seconds or None to determine from
        Constellation instruments (default=None)
    common_index : bool
        True to include times where all instruments have data, False to
        use the maximum time range from the Constellation (default=True)

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

    def __init__(self, const_module=None, instruments=None, index_res=None,
                 common_index=True):
        """
        Constructs a Constellation given a list of instruments or the name of
        a file with a pre-defined constellation.

        Parameters
        ----------
        const_module : module or NoneType
            Name of a pysat constellation module (default=None)
        instruments : list-like or NoneType
            A list of pysat Instruments to include in the Constellation
            (default=None)
        index_res : float or NoneType
            Output index resolution in seconds or None to determine from
            Constellation instruments (default=None)
        common_index : bool
            True to include times where all instruments have data, False to
            use the maximum time range from the Constellation (default=True)

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

        # Set the index attributes
        self.index_res = index_res
        self.common_index = common_index

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
                           "{:}, index_res=".format(self.instruments),
                           self.index_res.__repr__(), ", common_index=",
                           self.common_index.__repr__(), ")"])
        return out_str

    def __str__(self):
        """ Print names of instruments within constellation

        """

        ninst = len(self.instruments)

        output_str = 'pysat Constellation object:\n'
        output_str += '---------------------------\n'
        output_str += "{:d} Instruments\n".format(ninst)

        if ninst > 0:
            output_str += "\nIndex Platform Name Tag Inst_ID\n"
            output_str += "-------------------------------\n"
            for i, inst in enumerate(self.instruments):
                output_str += "{:d} '{:s}' '{:s}' '{:s}' '{:s}'\n".format(
                    i, inst.platform, inst.name, inst.tag, inst.inst_id)
        else:
            output_str += "No assigned Instruments\n"

        # Display loaded data
        output_str += '\n\nLoaded Data Statistics\n'
        output_str += '----------------------\n'
        if not self.empty:
            output_str += 'Date: ' + self.date.strftime('%d %B %Y') + '\n'
            output_str += '{:s}time range: '.format(
                "Common " if self.common_index else "Full ")
            output_str += self.index[0].strftime('%d %B %Y %H:%M:%S')
            output_str += ' --- '
            output_str += self.index[-1].strftime('%d %B %Y %H:%M:%S\n')
            output_str += 'Number of variables: {:d}\n'.format(
                len(self.variables))

            output_str += '\nVariable Names:\n'
            output_str += utils._core.fmt_output_in_cols(self.variables)
        else:
            output_str += 'No loaded data.\n'

        return output_str

    # -----------------------------------------------------------------------
    # Define all hidden methods

    def _empty(self, all_inst=True):
        """Boolean flag reflecting lack of data

        Parameters
        ----------
        all_inst : bool
            Require all instruments to have data for the empty flag to be
            False, if True.  If False, the empty flag will be False if any
            instrument has data. (default=True)

        Returns
        -------
        eflag : bool
            True if there is no Instrument data, False if there is data
            in at least one/all Instruments.

        """
        eflags = [inst.empty for inst in self.instruments]

        if len(eflags) == 0:
            eflag = True
        elif all_inst:
            eflag = np.any(eflags)
        else:
            eflag = np.all(eflags)

        return eflag

    def _index(self):
        """Returns a common time index for the loaded data

        Returns
        -------
        cindex : pds.Series
            Series containing a common time index for the Instrument data

        """
        if len(self.instruments) == 0 or self.empty:
            cindex = pds.Index([])
        else:
            stime = None
            etime = None
            out_res = None

            for inst in self.instruments:
                if stime is None:
                    # Initialize the start and stop time
                    stime = inst.index[0]
                    etime = inst.index[-1]

                    # If desired, determine the resolution
                    if self.index_res is None:
                        if inst.index.freq is None:
                            out_res = utils.time.calc_res(inst.index)
                        else:
                            out_res = utils.time.freq_to_res(inst.index.freq)
                else:
                    # Adjust the start and stop time as appropriate
                    if self.common_index:
                        if stime < inst.index[0]:
                            stime = inst.index[0]
                        if etime > inst.index[-1]:
                            etime = inst.index[-1]
                    else:
                        if stime > inst.index[0]:
                            stime = inst.index[0]
                        if etime < inst.index[-1]:
                            etime = inst.index[-1]

                    # If desired, determine the resolution
                    if self.index_res is None:
                        if inst.index.freq is None:
                            new_res = utils.time.calc_res(inst.index)
                        else:
                            new_res = utils.time.freq_to_res(inst.index.freq)

                        if new_res < out_res:
                            out_res = new_res

            # If a resolution in seconds was supplied, calculate the frequency
            if self.index_res is not None:
                out_res = pds.DateOffset(seconds=self.index_res)
            else:
                out_res = pds.DateOffset(seconds=out_res)

            # Construct the common index
            cindex = pds.date_range(stime, etime, freq=out_res)

        return cindex

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

    @property
    def date(self):
        """Date for loaded data."""
        if len(self.index) > 0:
            return utils.time.filter_datetime_input(self.index[0])
        else:
            return None

    @property
    def empty(self):
        """Boolean flag reflecting lack of data, True if there is no Instrument
        data in any Constellation Instrument.
        """
        return self._empty(all_inst=True)

    @property
    def index(self):
        """Returns time index of loaded data."""
        return self._index()

    def today(self):
        """Returns UTC date for today, see pysat.Instrument for details."""
        return utils.time.today()

    def tomorrow(self):
        """Returns UTC date for tomorrow, see pysat.Instrument for details."""
        return self.today() + dt.timedelta(days=1)

    def yesterday(self):
        """Returns UTC date for yesterday, see pysat.Instrument for details."""
        return self.today() - dt.timedelta(days=1)

    @property
    def variables(self):
        """Returns a list of uniquely named variables from all the loaded data.
        """
        # Determine which instrument variables share the same name
        data_vars = dict()
        for inst in self.instruments:
            for dvar in inst.variables:
                if dvar in data_vars.keys():
                    data_vars[dvar] += 1
                else:
                    data_vars[dvar] = 1

        # Distinguish shared names by Instrument platform, name, tag, inst_id
        var_list = []
        for inst in self.instruments:
            inst_str = '_'.join([attr for attr in [inst.platform, inst.name,
                                                   inst.tag, inst.inst_id]
                                 if len(attr) > 0])
            for dvar in inst.variables:
                var_list.append('_'.join([dvar, inst_str])
                                if data_vars[dvar] > 1 else dvar)
        return var_list

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

    def download(self, *args, **kwargs):
        """ Download instrument data into Instrument object.data

        Parameters
        ----------
        *args : list reference
            References a list of input arguments
        **kwargs : dict reference
            References a dict of input keyword arguments

        See Also
        ---------
        Instrument.download : base method for loading Instrument data

        Note
        ----
        If individual instruments require specific kwargs that differ from
        other instruments, define that in the individual instrument rather
        than this method.

        """

        for instrument in self.instruments:
            instrument.download(*args, **kwargs)

        return
