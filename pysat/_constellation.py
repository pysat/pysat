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

import pysat
from pysat import logger, utils


class Constellation(object):
    """Manage and analyze data from multiple pysat Instruments.

    Parameters
    ----------
    platforms : list or NoneType
        List of strings indicating the desired Instrument platforms. If None
        is specified on initiation, a list will be created to hold the platform
        attributes from each pysat.Instrument object in `instruments`.
        (default=None)
    names : list or NoneType
        List of strings indicating the desired Instrument names. If None
        is specified on initiation, a list will be created to hold the name
        attributes from each pysat.Instrument object in `instruments`.
        (default=None)
    tags : list or NoneType
        List of strings indicating the desired Instrument tags. If None
        is specified on initiation, a list will be created to hold the tag
        attributes from each pysat.Instrument object in `instruments`.
        (default=None)
    inst_ids : list or NoneType
        List of strings indicating the desired Instrument inst_ids. If None
        is specified on initiation, a list will be created to hold the inst_id
        attributes from each pysat.Instrument object in `instruments`.
        (default=None)
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
    platforms
    names
    tags
    inst_ids
    instruments
    index_res
    common_index
    bounds : tuple
        Tuple of two datetime objects or filenames indicating bounds for loading
        data, or a tuple of NoneType objects. Users may provide as a tuple or
        tuple of lists (useful for bounds with gaps). The attribute is always
        stored as a tuple of lists for consistency.
    date : dt.datetime or NoneType
        Date and time for loaded data, None if no data is loaded
    yr : int or NoneType
        Year for loaded data, None if no data is loaded
    doy : int or NoneType
        Day of year for loaded data, None if no data is loaded
    yesterday : dt.datetime
        Date and time for yesterday in UT
    today : dt.datetime
        Date and time for the current day in UT
    tomorrow : dt.datetime
        Date and time for tomorrow in UT
    empty : bool
        Flag that indicates all Instruments do not contain data when True.
    empty_partial : bool
        Flag that indicates at least one Instrument in the Constellation does
        not have data when True.
    variables : list
        List of loaded data variables for all instruments.

    Raises
    ------
    ValueError
        When `instruments` is not list-like or when all inputs to load through
        the registered Instrument list are unknown.
    AttributeError
        When module provided through `const_module` is missing the required
        attribute `instruments`.

    Note
    ----
    Omit `platforms`, `names`, `tags`, `inst_ids`, `instruments`, and
    `const_module` to create an empty constellation.

    """

    # -----------------------------------------------------------------------
    # Define the magic methods

    def __init__(self, platforms=None, names=None, tags=None, inst_ids=None,
                 const_module=None, instruments=None, index_res=None,
                 common_index=True):

        # Initalize the `instruments` attribute to be an empty list before
        # loading using each of the available input methods
        self.instruments = []
        self.yr = None
        self.doy = None

        # Add any registered Instruments that fulfill the provided platforms,
        # names, tags, and inst_ids
        load_from_platform = np.any([flg is not None for flg
                                     in [platforms, names, tags, inst_ids]])

        if load_from_platform:
            # Get a dictionary of the registered Instruments
            reg_inst = utils.available_instruments()

            # Determine which platforms and names are desired. If not specified,
            # use any value that fulfills the other constraints
            load_platforms = [flg for flg in reg_inst.keys()
                              if platforms is None or flg in platforms]
            added_platforms = list()
            added_names = list()
            added_tags = list()
            added_inst_ids = list()

            # Cycle through the each of the possible platforms, names, inst_ids,
            # and tags
            for ptf in load_platforms:
                ptf_names = [flg for flg in reg_inst[ptf].keys()
                             if names is None or flg in names]

                for flg in ptf_names:
                    ptf_inst_ids = [
                        iid
                        for iid in reg_inst[ptf][flg]['inst_ids_tags'].keys()
                        if inst_ids is None or iid in inst_ids]

                    for iid in ptf_inst_ids:
                        for tflg in reg_inst[
                                ptf][flg]['inst_ids_tags'][iid].keys():
                            if tags is None or tflg in tags:
                                # This Instrument has the desired platform,
                                # name, inst_id, and tag
                                self.instruments.append(pysat.Instrument(
                                    platform=ptf, name=flg, tag=tflg,
                                    inst_id=iid))
                                added_platforms.append(ptf)
                                added_names.append(flg)
                                added_tags.append(tflg)
                                added_inst_ids.append(iid)

            # Warn user about unloaded, requested Instruments
            if len(added_platforms) == 0:
                raise ValueError(''.join(['no registered packages match input',
                                          ' from platforms, names, tags, and ',
                                          'inst_ids kwargs']))
            else:
                # Test to see if any of the requested platform/name/tag/inst_id
                # options did not occur in the registered Instruments
                log_msg = []
                for flg_str, added_flg, in_flg in [
                        ("platforms", added_platforms, platforms),
                        ("names", added_names, names),
                        ("tags", added_tags, tags),
                        ("inst_ids", added_inst_ids, inst_ids)]:
                    if in_flg is not None:
                        missed = [flg for flg in in_flg if flg not in added_flg]
                        if len(missed) > 0:
                            log_msg.append(
                                "unable to load some {:s}: {:}".format(
                                    flg_str, missed))

                if len(log_msg) > 0:
                    logger.warning("; ".join(log_msg))

                # Set the Constellation attributes
                self.platforms = added_platforms
                self.names = added_names
                self.tags = added_tags
                self.inst_ids = added_inst_ids
        else:
            # Set the Constellation attributes to be empty lists
            self.platforms = []
            self.names = []
            self.tags = []
            self.inst_ids = []

        inst_len = len(self.instruments)

        # Include Instruments from the constellation module, if it exists
        if const_module is not None:
            if not hasattr(const_module, 'instruments'):
                raise AttributeError("missing required attribute 'instruments'")
            self.instruments.extend(const_module.instruments)

        # Add any Instruments provided in the list
        if instruments is not None:
            test_instruments = np.asarray(instruments)
            if test_instruments.shape == ():
                raise ValueError('instruments argument must be list-like')

            self.instruments.extend(list(instruments))

        # For each Instrument added by `const_module` or `instruments`, extend
        # the platforms/names/tags/inst_ids
        for inst_ind in np.arange(inst_len, len(self.instruments)):
            self.platforms.append(self.instruments[inst_ind].platform)
            self.names.append(self.instruments[inst_ind].name)
            self.tags.append(self.instruments[inst_ind].tag)
            self.inst_ids.append(self.instruments[inst_ind].inst_id)

        # Set the index attributes
        self.index_res = index_res
        self.common_index = common_index

        return

    def __getitem__(self, *args, **kwargs):
        """ Look up a member Instrument by index.
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

        # Define a convenience function for pluralizing words
        def is_plural(num):
            return "s" if num > 1 else ""

        ninst = len(self.instruments)
        nplat = len(self._get_unique_attr_vals("platforms"))
        nname = len(self._get_unique_attr_vals("names"))
        ntag = len(self._get_unique_attr_vals("tags"))
        ninst_id = len(self._get_unique_attr_vals("inst_ids"))

        output_str = 'pysat Constellation object:\n'
        output_str += '---------------------------\n'
        output_str += "{:d} Instrument{:s} with:\n".format(ninst,
                                                           is_plural(ninst))
        output_str += "{:d} unique platform{:s}, ".format(nplat,
                                                          is_plural(nplat))
        output_str += "{:d} unique name{:s}, ".format(nname, is_plural(nname))
        output_str += "{:d} unique tag{:s}, and ".format(ntag, is_plural(ntag))
        output_str += "{:d} unique inst_id{:s}\n".format(ninst_id,
                                                         is_plural(ninst_id))

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
            output_str += '{:s} Instruments have data\n'.format(
                'Some' if self.empty_partial else 'All')
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

    def _get_unique_attr_vals(self, attr):
        """ Get the unique elements of a list-like attribute

        Parameters
        ----------
        attr : str
            String denoting a list-like Constellation attribute name

        Returns
        -------
        uniq_attrs : list
            List of unique attribute values for the requested Constellation
            attribute

        Raises
        ------
        AttributeError
            If the requested attribute is not present
        TypeError
            If the requested attribute is not list-like

        """

        # Test to see if attribute is present
        if not hasattr(self, attr):
            raise AttributeError('Constellation does not have attribute')

        # Test to see if attribute is list-like
        attr_array = np.asarray(getattr(self, attr))
        if attr_array.shape == ():
            raise TypeError('Constellation attribute is not list-like')

        # Get unique attribute values
        uniq_attrs = list(np.unique(attr_array))

        return uniq_attrs

    def _set_inst_attr(self, attr, value):
        """ Set an attribute across all instruments

        Parameters
        ----------
        attr : str
            Instrument attribute
        value
            Appropriate value for the desired attribute

        """

        for instrument in self.instruments:
            setattr(instrument, attr, value)

        return

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

        self._set_inst_attr('bounds', value)
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
        data in all Constellation Instrument.
        """
        return self._empty(all_inst=False)

    @property
    def empty_partial(self):
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

        # Load the data for each instrument
        for instrument in self.instruments:
            instrument.load(*args, **kwargs)

        # Set the year and doy attributes for the constellation and instruments
        self.yr, self.doy = utils.time.getyrdoy(self.date)

        self._set_inst_attr('yr', self.yr)
        self._set_inst_attr('doy', self.doy)

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
