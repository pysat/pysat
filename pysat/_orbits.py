#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------

import copy
import datetime as dt
import functools
import numpy as np
import pandas as pds
import xarray as xr
import weakref

from pysat import logger


class Orbits(object):
    """Determines orbits on the fly and provides orbital data in .data.

    Parameters
    ----------
    inst : pysat.Instrument
        Instrument object for which the orbits will be determined
    index : str or NoneType
        Name of the data series to use for determing orbit breaks (default=None)
    kind : str
        Kind of orbit, which specifies how orbital breaks are determined.
        Expects one of: 'local time', 'longitude', 'polar', or 'orbit'
        - local time: negative gradients in lt or breaks in inst.data.index
        - longitude: negative gradients or breaks in inst.data.index
        - polar: zero crossings in latitude or breaks in inst.data.index
        - orbit: uses unique values of orbit number
        (default='local time')
    period : np.timedelta64 or NoneType
        length of time for orbital period, used to gauge when a break
        in the datetime index (inst.data.index) is large enough to
        consider it a new orbit

    Attributes
    ----------
    inst : pysat.Instrument
        Instrument object for which the orbits will be determined
    kind : str
        Kind of orbit, which specifies how orbital breaks are determined.
        Expects one of: 'local time', 'longitude', 'polar', or 'orbit'
        - local time : negative gradients in lt or breaks in inst.data.index
        - longitude : negative gradients or breaks in inst.data.index
        - polar : zero crossings in latitude or breaks in inst.data.index
        - orbit : uses unique values of orbit number
        (default='local time')
    orbit_period : pds.Timedelta
        Pandas Timedelta that specifies the orbit period.  Used instead of
        dt.timedelta to enable np.timedelta64 input.
        (default=97 min)
    num : int
        Number of orbits in loaded data
    orbit_index : int
        Index of currently loaded orbit, zero indexed

    Note
    ----
    Determines the locations of orbit breaks in the loaded data in inst.data
    and provides iteration tools and convenient orbit selection via
    inst.orbit[orbit num].

    This class should not be called directly by the user, it uses the interface
    provided by inst.orbits where inst = pysat.Instrument()

    Examples
    --------
    ::

        # Use orbit_info Instrument keyword to pass all Orbit kwargs
        orbit_info = {'index': 'longitude', 'kind': 'longitude'}
        vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b',
                                clean_level=None, orbit_info=orbit_info)

        # Set the instrument bounds
        start = dt.datetime(2009, 1, 1)
        stop = dt.datetime(2009, 1, 10)
        vefi.load(date=start)
        vefi.bounds(start, stop)

        # Iterate over orbits
        for vefi in vefi.orbits:
            print('Next available orbit ', vefi['dB_mer'])

        # Load fifth orbit of first day
        vefi.load(date=start)
        vefi.orbits[5]

        # Less convenient load
        vefi.orbits.load(5)

        # Manually iterate forwards in the orbit
        vefi.orbits.next()

        # Manually iterate backwards in the orbit
        vefi.orbits.prev()

    """

    # -----------------------------------------------------------------------
    # Define the magic methods

    def __init__(self, inst, index=None, kind='local time', period=None):

        # Set the class attributes
        self.inst = weakref.proxy(inst)
        self.kind = kind.lower()

        if period is None:
            period = pds.Timedelta(np.timedelta64(97, 'm'))
        self.orbit_period = pds.Timedelta(period)

        orbit_breaks = None
        if self.kind in ['local time', 'lt']:
            orbit_breaks = 24.0
        elif self.kind in ['longitude', 'long', 'lon']:
            orbit_breaks = 360.0

        if orbit_breaks is None:
            if self.kind == 'polar':
                self._det_breaks = self._polar_breaks
            elif self.kind == 'orbit':
                self._det_breaks = self._orbit_number_breaks
            else:
                raise ValueError('Unknown kind of orbit requested.')
        else:
            self._det_breaks = functools.partial(
                self._equa_breaks, orbit_index_period=orbit_breaks)

        self._orbit_breaks = []
        self.num = 0
        self._current = 0
        self.orbit_index = index

    def __repr__(self):
        """ Print the basic Orbits properties"""
        out_str = "".join(["pysat.Orbits(inst=", self.inst.__repr__(),
                           ", index=", self.orbit_index.__repr__(),
                           ", kind=", self.kind.__repr__(), ", period=",
                           self.orbit_period.__repr__(), ")"])
        return out_str

    def __str__(self):
        """ Descriptively print the basic Obits properties"""
        output_str = 'Orbit Settings\n'
        output_str += '--------------\n'
        output_str += 'Orbit Kind: {:s}\n'.format(self.kind.__repr__())
        output_str += 'Orbit Index: {:s}\n'.format(self.orbit_index.__repr__())
        output_str += 'Orbit Period: {:s}\n'.format(
            self.orbit_period.__repr__())
        output_str += 'Number of Orbits: {:d}\n'.format(self.num)
        output_str += 'Loaded Orbit Number: {:s}\n'.format(
            self._current.__repr__())

        return output_str

    def __eq__(self, other):
        """Perform equality check

        Parameters
        ----------
        other : any
            Other object to compare for equality

        Returns
        -------
        bool
            True if objects are identical, False if they are not

        """

        # Check if other is the same class (Orbits). Exit early if not.
        if not isinstance(other, self.__class__):
            return False

        # If the type is the same then check everything that is attached to
        # the Orbits object. Includes attributes, methods, variables, etc.
        checks = []
        key_check = []
        for key in self.__dict__.keys():
            if key in other.__dict__.keys():
                if key not in ['_full_day_data', 'inst', '_det_breaks']:
                    # Standard equality comparison
                    test = np.all(self.__dict__[key] == other.__dict__[key])
                    checks.append(test)
                    key_check.append(key)

                elif key in ['_full_day_data']:
                    # Compare data
                    if isinstance(self.__dict__[key], pds.DataFrame):
                        try:
                            # Comparisons can error simply for having
                            # different DataFrames
                            check = np.all(self.__dict__[key]
                                           == other.__dict__[key])
                        except ValueError:
                            # If there is an error they aren't the same
                            return False

                        checks.append(check)
                        key_check.append(key)

                    else:
                        # xarray comparison
                        test = xr.Dataset.equals(self.__dict__[key],
                                                 other.__dict__[key])
                        checks.append(test)
                        key_check.append(key)

                elif key == '_det_breaks':
                    # Equality of partial functions does not work well.
                    # Using a string comparison instead. This can also break
                    # if one of the objects is missing some attributes.
                    try:
                        check = str(self._det_breaks) == str(other._det_breaks)
                    except AttributeError:
                        # One object is missing a required attribute
                        return False

                    checks.append(check)
                    key_check.append(key)

            else:
                checks.append(False)
                key_check.append(key)
                return False

        # Confirm that Orbits object `other` doesn't have extra terms
        for key in other.__dict__.keys():
            if key not in self.__dict__.keys():
                return False

        test_data = np.all(checks)

        return test_data

    def __getitem__(self, orbit_key):
        """Enable convenience notation for loading orbit into parent object.

        Parameters
        ----------
        orbit_key : int or None
            Orbit number to get

        Examples
        --------
        ::

            inst.load(date=date)
            inst.orbits[4]
            print('Orbit data ', inst.data)

        Note
        ----
        A day of data must already be loaded.

        """
        if orbit_key < 0:
            self.load(orbit_key)  # Loading for reverse indices
        else:
            self.load(orbit_key + 1)  # Loading for forward indices

    def __iter__(self):
        """Support iteration by orbit.

        Examples
        --------
        ::

            for inst in inst.orbits:
                print('next available orbit ', inst.data)

        Note
        ----
        For each iteration the next available orbit is loaded into
        inst.data.

        Limits of iteration set by setting inst.bounds.

        """
        # Load up the first increment of data
        while self.inst.empty:
            self.inst.next()

        # Make a copy of the Instrument object
        local_inst = self.inst.copy()

        while True:
            try:
                self.next()

                # Ensure that garbage collection doesn't delete self.inst
                # by yielding a copy, without spending time on copying data
                data = self.inst.data
                self.inst.data = self.inst._null_data
                curr_data = self.inst._curr_data
                self.inst._curr_data = self.inst._null_data
                prev_data = self.inst._prev_data
                self.inst._prev_data = self.inst._null_data
                next_data = self.inst._next_data
                self.inst._next_data = self.inst._null_data

                # Account for data on orbit object itself
                full_day_data = self._full_day_data
                self._full_day_data = self.inst._null_data

                local_inst.date = self.inst.date

                # Restore data
                self.inst.data = data
                local_inst.data = data
                self.inst._curr_data = curr_data
                local_inst._curr_data = curr_data
                self.inst._prev_data = prev_data
                local_inst._prev_data = prev_data
                self.inst._next_data = next_data
                local_inst._next_data = next_data

                self._full_day_data = full_day_data
                local_inst.orbits._full_day_data = full_day_data
                local_inst.orbits.num = self.num
                local_inst.orbits._current = self._current
                local_inst.orbits._orbit_breaks = self._orbit_breaks

                yield local_inst
            except StopIteration:
                return

    # -----------------------------------------------------------------------
    # Define the hidden methods

    def _report_current_orbit(self):
        """ Report the current orbit to log at the info level
        """

        # Index appears as zero-indexed, though it is one-indexed
        logger.info('Loaded Orbit: {:d}'.format(self._current - 1))
        return

    def _reset(self):
        """Create null arrays for storing orbit info
        """
        self._orbit_breaks = []
        self.num = 0
        self._current = 0

    def _calc_orbits(self):
        """Prepares data structure for breaking data into orbits

        Raises
        ------
        ValueError
            If the the Instrument bounds are set to load overlapping data sets

        """
        # Check there isn't an overlapping data set from iteration bounds
        estr = ' '.join(('Orbit iteration is not currently supported',
                         'when the pysat.Instrument bounds are',
                         'configured for loading overlapping',
                         'data. Please set the Instrument bounds width',
                         'to be less than or equal to the bounds step ',
                         'increment. See `pysat.Instrument.bounds` for more.'))

        if self.inst._iter_type == 'file':
            if self.inst._iter_step < self.inst._iter_width:
                raise ValueError(estr)
        else:
            # Iterating by date.  We need to check step (frequency string)
            # against width (timedelta)
            step = pds.tseries.frequencies.to_offset(self.inst._iter_step)
            step = dt.timedelta(seconds=step.delta.total_seconds())
            root = dt.datetime(2001, 1, 1)
            if root + step < root + self.inst._iter_width:
                raise ValueError(estr)

        # If the breaks between orbit have not been defined, define them here.
        # Also store the data so that grabbing different orbits does not
        # require reloads of whole dataset
        if len(self._orbit_breaks) == 0:
            # Eetermine orbit breaks
            self._det_breaks()

            # Store a copy of data
            self._full_day_data = self.inst.data.copy()

            # Set current orbit counter to zero (default)
            self._current = 0

    def _equa_breaks(self, orbit_index_period=24.0):
        """Determine where breaks in an equatorial satellite orbit occur.

        Looks for negative gradients in local time (or longitude) as well as
        breaks in UT.

        Parameters
        ----------
        orbit_index_period : float
            The change in value of supplied index parameter for a single orbit
            (default=24.0)

        Raises
        ------
        ValueError
            If the orbit_index attribute is not set to an appropriate value

        """

        if self.orbit_index is None:
            raise ValueError(' '.join(('Orbit properties must be defined at ',
                                       'pysat.Instrument object instantiation.',
                                       'See Instrument docs.')))
        else:
            try:
                self.inst[self.orbit_index]
            except KeyError as err:
                raise ValueError(''.join((str(err), '\n',
                                          'Provided orbit index does not ',
                                          'exist in loaded data')))

        # Get the difference in orbit index around the orbit
        lt_diff = self.inst[self.orbit_index]
        if not self.inst.pandas_format:
            lt_diff = lt_diff.to_pandas()
        lt_diff = lt_diff.diff()

        # Get the typical (median) difference
        typical_lt_diff = np.nanmedian(lt_diff)
        logger.info(''.join(('typical lt diff ', str(typical_lt_diff))))

        # Get the Universal Time difference between data values. Assumes that
        # the time index is in UT.
        ut_vals = pds.Series(self.inst.index)
        ut_diff = ut_vals.diff()

        # Get the locations where the orbit index derivative is less than 0,
        # then do some sanity checks on these locations
        ind, = np.where((lt_diff < -0.2 * typical_lt_diff))
        if len(ind) > 0:
            ind = np.hstack((ind, np.array([len(self.inst[self.orbit_index])])))

            # Look at distance between breaks
            dist = ind[1:] - ind[0:-1]

            # Only keep orbit breaks with a distance greater than 1.  This check
            # is done to ensure robustness
            if len(ind) > 1:
                if min(dist) == 1:
                    logger.info(' '.join(('There are orbit breaks right next',
                                          'to each other')))
                ind = ind[:-1][dist > 1]

            # Check for large positive gradients around the break that would
            # suggest not a true orbit break, but rather bad orbit_index values
            new_ind = []
            for idx in ind:
                tidx, = np.where(lt_diff[(idx - 5):(idx + 6)]
                                 > 10 * typical_lt_diff)

                if len(tidx) != 0:
                    # There are large changes, this suggests a false alarm.
                    # Iterate over samples and check
                    for sub_tidx in tidx:
                        # Look at time change vs local time change
                        if(ut_diff[idx - 5:idx + 6].iloc[sub_tidx]
                           < lt_diff[idx - 5:idx + 6].iloc[sub_tidx]
                           / orbit_index_period * self.orbit_period):
                            # The change in UT is small compared to the change
                            # in the orbit index this is flagged as a false
                            # alarm, or dropped from consideration
                            logger.info(''.join(('Dropping found break ',
                                                 'as false positive.')))
                            pass
                        else:
                            # The change in UT is significant, keep orbit break
                            new_ind.append(idx)
                            break
                else:
                    # There are no large positive gradients, current orbit
                    # break passes the first test
                    new_ind.append(idx)

            # Replace all breaks with those that are 'good'
            ind = np.array(new_ind)

        # Now, assemble some orbit breaks that are not triggered by changes in
        # the orbit index
        #
        # Check if there is a UT break that is larger than orbital period, AKA
        # a time gap
        ut_change_vs_period = (ut_diff > self.orbit_period)

        # Characterize ut change using orbital period
        norm_ut = ut_diff / self.orbit_period

        # Now, look for breaks because the length of time between samples is
        # too large, thus there is no break in slt/mlt/etc, lt_diff is small
        # but UT change is big
        norm_ut_vs_norm_lt = norm_ut.gt(np.abs(lt_diff.values
                                               / orbit_index_period))

        # Indices when one or other flag is true
        ut_ind, = np.where(ut_change_vs_period
                           | (norm_ut_vs_norm_lt & (norm_ut > 0.95)))

        # Combine these UT determined orbit breaks with the orbit index orbit
        # breaks
        if len(ut_ind) > 0:
            ind = np.hstack((ind, ut_ind))
            ind = np.sort(ind)
            ind = np.unique(ind)
            logger.info('Time Gap at locations: {:}'.format(ut_ind))

        # Now that most problems in orbits should have been caught, look at
        # the time difference between orbits (not individual orbits)
        orbit_ut_diff = ut_vals[ind].diff()
        if not self.inst.pandas_format:
            orbit_lt_diff = self.inst[self.orbit_index].to_pandas()[ind].diff()
        else:
            orbit_lt_diff = self.inst[self.orbit_index][ind].diff()

        # Look for time gaps between partial orbits. The full orbital time
        # period is not required between end of one orbit and beginning of next
        # if first orbit is partial.  Also provides another general test of the
        # orbital breaks determined.
        idx, = np.where((orbit_ut_diff / self.orbit_period
                         - orbit_lt_diff.values / orbit_index_period) > 0.97)

        # Pull out breaks that pass the test, need to make sure the first one
        # is always included it gets dropped via the nature of diff
        if len(idx) > 0:
            if idx[0] != 0:
                idx = np.hstack((0, idx))
        else:
            idx = np.array([0])

        # Only keep the good indices
        if len(ind) > 0:
            ind = ind[idx]

            # Create an orbit break index, ensure first element is always 0
            if ind[0] != 0:
                ind = np.hstack((np.array([0]), ind))
        else:
            ind = np.array([0])

        # Set the index of orbit breaks and the number of orbits
        self._orbit_breaks = ind
        self.num = len(ind)

    def _polar_breaks(self):
        """Determine where breaks in a polar orbiting satellite orbit occur.

        Raises
        ------
        ValueError
            If the orbit_index attribute is not set to an appropriate value

        Note
        ----
        Looks for sign changes in latitude (magnetic or geographic) as well as
        breaks in UT.

        """

        if self.orbit_index is None:
            raise ValueError(' '.join(('Orbit properties must be defined at',
                                       'pysat.Instrument object instantiation.',
                                       'See Instrument docs.')))
        else:
            try:
                self.inst[self.orbit_index]
            except KeyError as err:
                raise ValueError(''.join((str(err), '\n',
                                          'Provided orbit index does not ',
                                          'appear to exist in loaded data')))

        # Determine where orbit index goes from positive to negative
        pos = (self.inst[self.orbit_index] >= 0)
        npos = np.logical_not(pos)
        change = ((pos.values[:-1] & npos.values[1:])
                  | (npos.values[:-1] & pos.values[1:]))

        ind, = np.where(change)
        ind += 1

        ut_diff = pds.Series(self.inst.index).diff()
        ut_ind, = np.where(ut_diff / self.orbit_period > 0.95)

        if len(ut_ind) > 0:
            ind = np.unique(np.sort(np.hstack((ind, ut_ind))))

        # Create an orbit break index, ensure first element is always 0
        if len(ind) > 0:
            if ind[0] != 0:
                ind = np.hstack((np.array([0]), ind))
        else:
            ind = np.array([0])

        # Set the index of orbit breaks and the number of orbits
        self._orbit_breaks = ind
        self.num = len(ind)

    def _orbit_number_breaks(self):
        """Find orbital breaks in a dataset with orbit numbers occur.

        Raises
        ------
        ValueError
            If the orbit_index attribute is not set to an appropriate value

        Note
        ----
        Looks for changes in unique values.

        """

        if self.orbit_index is None:
            raise ValueError(' '.join(('Orbit properties must be defined at ',
                                       'pysat.Instrument object instantiation.',
                                       'See Instrument docs.')))
        else:
            try:
                self.inst[self.orbit_index]
            except KeyError as err:
                raise ValueError(''.join((str(err), '\n',
                                          'Provided orbit index does not ',
                                          'appear to exist in loaded data')))

        # Determine where the orbit index changes from one value to the next
        uniq_vals = np.unique(self.inst[self.orbit_index].values)
        orbit_index = []
        for val in uniq_vals:
            idx, = np.where(val == self.inst[self.orbit_index].values)
            orbit_index.append(idx[0])

        # Create orbit break index, ensure first element is always 0
        if len(orbit_index) > 0:
            if orbit_index[0] != 0:
                ind = np.hstack((np.array([0]), orbit_index))
            else:
                ind = orbit_index
        else:
            ind = np.array([0])

        # Set the index of orbit breaks and the number of orbits
        self._orbit_breaks = ind
        self.num = len(ind)

    def _get_basic_orbit(self, orbit_num):
        """Load a particular orbit into .data for loaded day.

        Parameters
        ----------
        orbit_num : int
            orbit number, 1 indexed, negative indexes allowed, -1 last orbit

        Note
        ----
        A day of data must be loaded before this routine functions properly.
        If the last orbit of the day is requested, it will NOT automatically be
        padded with data from the next day.

        """
        # Ensure data exists
        if not self.inst.empty:
            # Ensure proper orbit metadata present
            self._calc_orbits()

            # Set up data access for both pandas and xarray
            self.inst.data = self._full_day_data

            # Pull out the requested orbit
            if orbit_num == -1:
                # Load last orbit data into data
                orb_break = self._orbit_breaks[self.num + orbit_num]
                self.inst.data = self.inst[orb_break:]
                self._current = self.num + orbit_num + 1
            elif orbit_num < 0 and orbit_num >= -self.num:
                # Load backwards index orbit data into data
                self.inst.data = self.inst[
                    self._orbit_breaks[self.num + orbit_num]:
                    self._orbit_breaks[self.num + orbit_num + 1]]
                self._current = self.num + orbit_num + 1
            elif orbit_num < self.num and orbit_num != 0:
                # Load forward indexed orbit data into data
                self.inst.data = self.inst[self._orbit_breaks[orbit_num - 1]:
                                           self._orbit_breaks[orbit_num]]
                self._current = orbit_num
            elif orbit_num == self.num:
                self.inst.data = self.inst[self._orbit_breaks[orbit_num - 1]:]
                self._current = orbit_num
            elif orbit_num == 0:
                raise ValueError(' '.join(('Orbits internally indexed by',
                                           '1, 0 not allowed')))
            else:
                # Gone too far
                self.inst.data = []
                raise ValueError(' '.join(('Requested an orbit past total',
                                           'orbits for day')))
        return

    # -----------------------------------------------------------------------
    # Define the public methods and properties

    def copy(self):
        """Provide a deep copy of object

        Returns
        -------
        Orbits class instance
            Copy of self

        """
        # pysat.Instrument has a link to orbits, so copying the referenced
        # self.inst would lead to infinite recursion.
        inst = self.inst
        self.inst = None

        # Copy everything else
        orbits_copy = copy.deepcopy(self)

        # Both this object and the copy refer back to the same pysat.Instrument
        orbits_copy.inst = inst
        self.inst = inst

        return orbits_copy

    @property
    def current(self):
        """Current orbit number.

        Returns
        -------
        int or NoneType
            None if no orbit data. Otherwise, returns orbit number, beginning
            with zero. The first and last orbit of a day is somewhat ambiguous.
            The first orbit for day n is generally also the last orbit
            on day n - 1. When iterating forward, the orbit will be labeled
            as first (0). When iterating backward, orbit labeled as the last.

        """

        if self._current > 0:
            return self._current - 1
        else:
            return None

    def load(self, orbit_num):
        """Load a particular orbit into .data for loaded day.

        Parameters
        ----------
        orbit_num : int
            orbit number, 1 indexed (1-length or -1 to -length) with sign
            denoting forward or backward indexing

        Raises
        ------
        ValueError
            If index requested lies beyond the number of orbits

        Note
        ----
        A day of data must be loaded before this routine functions properly.
        If the last orbit of the day is requested, it will automatically be
        padded with data from the next day. The orbit counter will be
        reset to 1.

        """
        # Ensure data exits
        if not self.inst.empty:
            # Set up orbit metadata
            self._calc_orbits()

            # Pull out the requested orbit
            if orbit_num < 0:
                # Negative indexing consistent with numpy, -1 last,
                # -2 second to last, etc.
                orbit_num = self.num + 1 + orbit_num

            if orbit_num == self.num:
                # We get here if user asks for last orbit. This cal is first to
                # trap case where there is only one orbit (self.num=1), which
                # needs to be treated differently than a orbit=1 call
                if self.num != 1:
                    # More than one orbit, go back one (simple call) and
                    # then forward doing full logic for breaks across day
                    self._get_basic_orbit(self.num - 1)
                    self.next()
                else:
                    # At most one complete orbit in the file, check if we are
                    # close to beginning or end of day
                    date = self.inst.date
                    delta_start = self.inst.index[-1] - date
                    delta_end = (date + dt.timedelta(days=1)
                                 - self.inst.index[0])

                    if delta_start <= self.orbit_period * 1.05:
                        # We are near the beginning. Load the previous file,
                        # then go forward one orbit
                        self.inst.prev()
                        self.next()
                        if self.inst.index[-1] < date + delta_start:
                            # We could go back a day, iterate over orbit, as
                            # above, and the data we have is the wrong day.
                            # In this case, move forward again.  This happens
                            # when previous day doesn't have data near end of
                            # the day
                            self.next()

                    elif delta_end <= self.orbit_period * 1.05:
                        # Near end; load next file, then go back one orbit
                        self.inst.next()
                        self.prev()
                        if self.inst.index[0] > (date - delta_end
                                                 + dt.timedelta(days=1)):
                            # We could go forward a day, iterate over orbit
                            # as above, and the data we have is the wrong day.
                            # In this case, move back again. This happens when
                            # next day doesn't have data near beginning of the
                            # day
                            self.prev()
                    else:
                        # Not near beginning or end, just get the last orbit
                        # available (only one)
                        self._get_basic_orbit(-1)
            elif orbit_num == 1:
                # User asked for first orbit
                try:
                    # Orbit could start file previous; check for this condition
                    # and store the real date user wants
                    true_date = self.inst.date

                    # Go back a day
                    self.inst.prev()

                    # If and else added because of Instruments that have large
                    # gaps (e.g., C/NOFS).  In this case, prev can return
                    # empty data
                    if not self.inst.empty:
                        # Get last orbit if there is data. This will deal with
                        # orbits across file cleanly
                        self.load(-1)
                    else:
                        # No data, no previous data to account for. Move back
                        # to original data, do simple load of first orbit
                        self.inst.next()
                        self._get_basic_orbit(1)

                    # Check that this orbit should end on the current day
                    delta = true_date - self.inst.index[0]
                    if delta >= self.orbit_period:
                        # The orbit loaded isn't close enough to date to be the
                        # first orbit of the day, move forward
                        self.next()

                except StopIteration:
                    # Check if the first orbit is also the last orbit
                    self._get_basic_orbit(1)
                    self._report_current_orbit()

            elif orbit_num < self.num:
                # Load basic orbit data into data
                self._get_basic_orbit(orbit_num)
                self._report_current_orbit()

            else:
                # Gone too far
                self.inst.data = self.inst._null_data
                raise ValueError(' '.join(('Requested an orbit past total',
                                           'orbits for day')))
        else:
            logger.info(' '.join(('No data loaded in instrument object to',
                                  'determine orbits.')))

    def next(self):
        """Load the next orbit into associated Instrument.data object

        Note
        ----
        Forms complete orbits across day boundaries. If no data loaded
        then the first orbit from the first date of data is returned.

        """

        # Check if data exists
        if not self.inst.empty:
            # Set up orbit metadata
            self._calc_orbits()

            # If current orbit near the last, must be careful
            if self._current == (self.num - 1):
                # Load last orbit data
                self._get_basic_orbit(-1)

                # End of orbit may occur on the next day
                load_next = True
                if self.inst._iter_type == 'date':
                    delta = (self.inst.date - self.inst.index[-1]
                             + pds.Timedelta('1 day'))
                    if delta >= self.orbit_period:
                        # Don't need to load the next day because this orbit
                        # ends more than a orbital period from the next date
                        load_next = False

                if load_next:
                    # The end of the user's desired orbit occurs tomorrow, need
                    # to form a complete orbit save this current orbit, load
                    # the next day, combine data, select the correct orbit
                    temp_orbit_data = self.inst.copy()
                    try:
                        # Loading next day/file clears orbit breaks info
                        self.inst.next()
                        if not self.inst.empty:
                            # Combine this next day's data with previous last
                            # orbit, grab the first one
                            final_val = self.inst.index[0] - dt.timedelta(
                                microseconds=1)
                            self.inst.concat_data(temp_orbit_data[:final_val],
                                                  prepend=True)
                            self._get_basic_orbit(1)
                        else:
                            # No data, go back a day and grab the last orbit.
                            # This is as complete as this orbit can be.
                            self.inst.prev()
                            self._get_basic_orbit(-1)
                    except StopIteration:
                        pass
                    del temp_orbit_data

                self._report_current_orbit()

            elif self._current == (self.num):
                # At the last orbit, need to be careful about getting the next
                # orbit save this current orbit and load the next day
                # temp_orbit_data = self.inst.data.copy()
                temp_orbit_data = self.inst.copy()

                # Load next day, which clears orbit breaks info
                self.inst.next()

                # Combine this next day orbit with previous last orbit to
                # ensure things are correct
                if not self.inst.empty:
                    pad_next = True

                    # Check if data padding is really needed, only works when
                    # loading by date
                    if self.inst._iter_type == 'date':
                        delta = self.inst.date - temp_orbit_data.index[-1]
                        if delta >= self.orbit_period:
                            # The end of the previous orbit is more than an
                            # orbit away from today we don't have to worry
                            # about it
                            pad_next = False
                    if pad_next:
                        # The orbit went across day break, stick old orbit onto
                        # new data and grab second orbit (first is old)
                        self.inst.concat_data(
                            temp_orbit_data[:self.inst.index[0]
                                            - dt.timedelta(microseconds=1)],
                            prepend=True)

                        # Select second orbit of combined data
                        self._get_basic_orbit(2)
                    else:
                        # Padding from the previous orbit wasn't needed, can
                        # just grab the first orbit of loaded data
                        self._get_basic_orbit(1)
                        if self.inst._iter_type == 'date':
                            delta = (self.inst.date + dt.timedelta(days=1)
                                     - self.inst.index[0])

                            if delta < self.orbit_period:
                                # This orbits end occurs on the next day,
                                # though we grabbed the first orbit, missing
                                # data means the first available orbit in the
                                # datais actually the last for the day.
                                # Resetting to the second to last orbit and t
                                # hen callingnext() will get the last orbit,
                                # accounting for tomorrow's data as well.
                                self._current = self.num - 1
                                self.next()
                else:
                    # There is no data for the next day, continue loading data
                    # until there is some.  The `next` method raises
                    # StopIteration when it reaches the end, leaving this
                    # function
                    while self.inst.empty:
                        self.inst.next()
                    self._get_basic_orbit(1)

                del temp_orbit_data
                self._report_current_orbit()

            elif self._current == 0:
                # No current orbit set, grab the first one using the load
                # command to specify the first orbit, which automatically
                # loads prev day if needed to form a complete orbit
                self.load(1)

            elif self._current < (self.num - 1):
                # Since we aren't close to the last orbit, just pull the next
                # orbit
                self._get_basic_orbit(self._current + 1)
                self._report_current_orbit()
            else:
                raise RuntimeError(' '.join(('This is a serious bug. Talk to ',
                                             'someone about this fundamental ',
                                             'failure or open an issue at',
                                             'www.github.com/pysat/pysat')))

        else:
            # There is no data
            while self.inst.empty:
                # Keep going until data is found or next raises stopIteration
                # at the end of the data set, and no more data is available
                self.inst.next()

            # We've found data, grab the next orbit
            self.next()

        return

    def prev(self):
        """Load the previous orbit into associated Instrument.data object

        Note
        ----
        Forms complete orbits across day boundaries. If no data loaded
        then the last orbit of data from the last day is loaded.

        """

        # First, check if data exists
        if not self.inst.empty:
            # Set up orbit metadata
            self._calc_orbits()

            if (self._current > 2) and (self._current <= self.num):
                # If not close to the first orbit, just pull the previous orbit
                #
                # Load orbit and put it into self.inst.data
                self._get_basic_orbit(self._current - 1)
                self._report_current_orbit()
            elif self._current == 2:
                # If current orbit near the first, must be careful
                #
                # First, load prev orbit data
                self._get_basic_orbit(self._current - 1)

                load_prev = True
                if self.inst._iter_type == 'date':
                    delta = self.inst.index[-1] - self.inst.date
                    if delta >= self.orbit_period:
                        # Don't need to load the prev day because this orbit
                        # ends more than a orbital period from start of today's
                        # date
                        load_prev = False

                if load_prev:
                    # Need to save this current orbit and load the prev day
                    temp_orbit_data = self.inst[self.inst.date:]

                    # Load previous day, which clears orbit breaks info
                    try:
                        self.inst.prev()
                        # Combine this next day orbit with previous last orbit
                        if not self.inst.empty:
                            self.inst.concat_data(temp_orbit_data,
                                                  prepend=False)

                            # Select first orbit of combined data
                            self._get_basic_orbit(-1)
                        else:
                            self.inst.next()
                            self._get_basic_orbit(1)
                    except StopIteration:
                        # If loading the first orbit, of first day of data,
                        # you'll end up here as the attempt to make a full
                        # orbit will move the date backwards, and StopIteration
                        # is made. everything is already ok, just move along
                        pass

                    del temp_orbit_data

                self._report_current_orbit()
            elif self._current == 0:
                self.load(-1)
                return
            elif self._current < 2:
                # First, load prev orbit data
                self._get_basic_orbit(1)

                # Need to save this current orbit and load the prev day
                temp_orbit_data = self.inst[self.inst.date:]

                # Load previous day, which clears orbit breaks info
                self.inst.prev()

                # Combine this next day orbit with previous last orbit
                if not self.inst.empty:
                    load_prev = True
                    if self.inst._iter_type == 'date':
                        delta = (self.inst.date - self.inst.index[-1]
                                 + pds.Timedelta('1 day'))
                        if delta >= self.orbit_period:
                            # Don't need to load the prev day because this
                            # orbit ends more than a orbital period from start
                            # of today's date
                            load_prev = False

                    if load_prev:
                        self.inst.concat_data(temp_orbit_data, prepend=False)

                        # Select second to last orbit of combined data
                        self._get_basic_orbit(-2)
                    else:
                        # Padding from the previous is needed
                        self._get_basic_orbit(-1)
                        if self.inst._iter_type == 'date':
                            delta = (self.inst.date - self.inst.index[-1]
                                     + pds.Timedelta('1 day'))
                            if delta < self.orbit_period:
                                self._current = self.num
                                self.prev()
                else:
                    while self.inst.empty:
                        self.inst.prev()
                    self._get_basic_orbit(-1)

                del temp_orbit_data
                self._report_current_orbit()
            else:
                raise RuntimeError(' '.join(('You ended up where nobody should',
                                             'ever be. Talk to someone about',
                                             'this fundamental failure or open',
                                             'an issue at',
                                             'www.github.com/pysat/pysat')))
        else:
            # No data found
            while self.inst.empty:
                # Cycle to more data or raise stopIteration at end of data set
                self.inst.prev()
            self.prev()

        return
