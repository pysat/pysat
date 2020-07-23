from __future__ import print_function
from __future__ import absolute_import

import functools

import numpy as np
import pandas as pds
from pysat import Series
from pysat import logger


class Orbits(object):
    """Determines orbits on the fly and provides orbital data in .data.

    Determines the locations of orbit breaks in the loaded data in inst.data
    and provides iteration tools and convenient orbit selection via
    inst.orbit[orbit num].

    Parameters
    ----------
    sat : pysat.Instrument instance
        instrument object to determine orbits for
    index : string
        name of the data series to use for determing orbit breaks
    kind : {'local time', 'longitude', 'polar', 'orbit'}
        kind of orbit, determines how orbital breaks are determined

        - local time: negative gradients in lt or breaks in inst.data.index
        - longitude: negative gradients or breaks in inst.data.index
        - polar: zero crossings in latitude or breaks in inst.data.index
        - orbit: uses unique values of orbit number
    period : np.timedelta64
        length of time for orbital period, used to gauge when a break
        in the datetime index (inst.data.index) is large enough to
        consider it a new orbit

    Note
    ----
    class should not be called directly by the user, use the interface provided
    by inst.orbits where inst = pysat.Instrument()

    Warning
    -------
    This class is still under development.

    Examples
    --------
    ::

        info = {'index':'longitude', 'kind':'longitude'}
        vefi = pysat.Instrument(platform='cnofs', name='vefi', tag='dc_b',
                                clean_level=None, orbit_info=info)
        start = pysat.datetime(2009,1,1)
        stop = pysat.datetime(2009,1,10)
        vefi.load(date=start)
        vefi.bounds(start, stop)

        # iterate over orbits
        for vefi in vefi.orbits:
            print('Next available orbit ', vefi['dB_mer'])

        # load fifth orbit of first day
        vefi.load(date=start)
        vefi.orbits[5]

        # less convenient load
        vefi.orbits.load(5)

        # manually iterate orbit
        vefi.orbits.next()
        # backwards
        vefi.orbits.prev()
    """

    def __init__(self, sat=None, index=None, kind=None, period=None):
        # create null arrays for storing orbit info
        if sat is None:
            raise ValueError('Must provide a pysat instrument object when ' +
                             'initializing orbits class.')
        else:
            # self.sat = weakref.proxy(sat)
            self.sat = sat

        if kind is None:
            kind = 'local time'
        else:
            kind = kind.lower()

        if period is None:
            period = pds.Timedelta(np.timedelta64(97, 'm'))
        self.orbit_period = pds.Timedelta(period)

        if (kind == 'local time') or (kind == 'lt'):
            self._detBreaks = functools.partial(self._equaBreaks,
                                                orbit_index_period=24.)
        elif (kind == 'longitude') or (kind == 'long'):
            self._detBreaks = functools.partial(self._equaBreaks,
                                                orbit_index_period=360.)
        elif kind == 'polar':
            self._detBreaks = self._polarBreaks
        elif kind == 'orbit':
            self._detBreaks = self._orbitNumberBreaks
        else:
            raise ValueError('Unknown kind of orbit requested.')

        self._orbit_breaks = []
        self.num = 0
        self._current = 0
        self.orbit_index = index

    @property
    def current(self):
        """Current orbit number.

        Returns
        -------
        int or None
            None if no orbit data. Otherwise, returns orbit number, begining
            with zero. The first and last orbit of a day is somewhat ambiguous.
            The first orbit for day n is generally also the last orbit
            on day n - 1. When iterating forward, the orbit will be labeled
            as first (0). When iterating backward, orbit labeled as the last.

        """

        if self._current > 0:
            return self._current - 1
        else:
            return None

    def __getitem__(self, key):
        """Enable convenience notation for loading orbit into parent object.

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
        # hack included so that orbits appear to be zero indexed
        if key < 0:
            self.load(key)
        else:
            self.load(key + 1)

    def _reset(self):
        # create null arrays for storing orbit info
        self._orbit_breaks = []
        self.num = 0
        self._current = 0

    def _calcOrbits(self):
        """Prepares data structure for breaking data into orbits. Not intended
        for end user."""
        # if the breaks between orbit have not been defined, define them
        # also, store the data so that grabbing different orbits does not
        # require reloads of whole dataset
        if len(self._orbit_breaks) == 0:
            # determine orbit breaks
            self._detBreaks()
            # store a copy of data
            self._fullDayData = self.sat.data.copy()
            # set current orbit counter to zero (default)
            self._current = 0

    def _equaBreaks(self, orbit_index_period=24.):
        """Determine where breaks in an equatorial satellite orbit occur.

        Looks for negative gradients in local time (or longitude) as well as
        breaks in UT.

        Parameters
        ----------
        orbit_index_period : float
           The change in value of supplied index parameter for a single orbit
        """

        if self.orbit_index is None:
            raise ValueError('Orbit properties must be defined at ' +
                             'pysat.Instrument object instantiation.' +
                             'See Instrument docs.')
        else:
            try:
                self.sat[self.orbit_index]
            except KeyError as err:
                raise ValueError(''.join((str(err), '\n',
                                          'Provided orbit index does not ',
                                          'exist in loaded data')))
        # get difference in orbit index around the orbit
        lt_diff = self.sat[self.orbit_index]
        if not self.sat.pandas_format:
            lt_diff = lt_diff.to_pandas()
        lt_diff = lt_diff.diff()
        # get typical difference
        typical_lt_diff = np.nanmedian(lt_diff)
        logger.info(''.join(('typical lt diff ', str(typical_lt_diff))))

        # universal time values, from datetime index
        ut_vals = Series(self.sat.index)
        # UT difference
        ut_diff = ut_vals.diff()

        # get locations where orbit index derivative is less than 0
        # then do some basic checks on these locations
        ind, = np.where((lt_diff < -0.2 * typical_lt_diff))
        if len(ind) > 0:
            ind = np.hstack((ind, np.array([len(self.sat[self.orbit_index])])))
            # look at distance between breaks
            dist = ind[1:] - ind[0:-1]
            # only keep orbit breaks with a distance greater than 1
            # done for robustness
            if len(ind) > 1:
                if min(dist) == 1:
                    logger.info('There are orbit breaks right next to each other')
                ind = ind[:-1][dist > 1]

            # check for large positive gradients around the break that would
            # suggest not a true orbit break, but rather bad orbit_index values
            new_ind = []
            for idx in ind:
                tidx, = np.where(lt_diff[(idx - 5):(idx + 6)] > 10 * typical_lt_diff)

                if len(tidx) != 0:
                    # there are large changes, suggests a false alarm
                    # iterate over samples and check
                    for sub_tidx in tidx:
                        # look at time change vs local time change
                        if(ut_diff[idx - 5:idx + 6].iloc[sub_tidx] <
                           lt_diff[idx - 5:idx + 6].iloc[sub_tidx] /
                           orbit_index_period * self.orbit_period):
                            # change in ut is small compared to the change in
                            # the orbit index this is flagged as a false alarm,
                            # or dropped from consideration
                            logger.info(''.join(('Dropping found break ',
                                                 'as false positive.')))
                            pass
                        else:
                            # change in UT is significant, keep orbit break
                            new_ind.append(idx)
                            break
                else:
                    # no large positive gradients, current orbit break passes
                    # the first test
                    new_ind.append(idx)
            # replace all breaks with those that are 'good'
            ind = np.array(new_ind)

        # now, assemble some orbit breaks that are not triggered by changes in
        # the orbit index

        # check if there is a UT break that is larger than orbital period, aka
        # a time gap
        ut_change_vs_period = (ut_diff > self.orbit_period)
        # characterize ut change using orbital period
        norm_ut = ut_diff / self.orbit_period
        # now, look for breaks because the length of time between samples is
        # too large, thus there is no break in slt/mlt/etc, lt_diff is small
        # but UT change is big
        norm_ut_vs_norm_lt = norm_ut.gt(np.abs(lt_diff.values /
                                               orbit_index_period))
        # indices when one or other flag is true
        ut_ind, = np.where(ut_change_vs_period | (norm_ut_vs_norm_lt &
                                                  (norm_ut > 0.95)))
        # added the or and check after or on 10/20/2014
        # & lt_diff.notnull() ))# & (lt_diff != 0)  ) )

        # combine these UT determined orbit breaks with the orbit index orbit
        # breaks
        if len(ut_ind) > 0:
            ind = np.hstack((ind, ut_ind))
            ind = np.sort(ind)
            ind = np.unique(ind)
            logger.info('Time Gap at locations', ut_ind)

        # now that most problems in orbits should have been caught, look at
        # the time difference between orbits (not individual orbits)
        orbit_ut_diff = ut_vals[ind].diff()
        if not self.sat.pandas_format:
            orbit_lt_diff = self.sat[self.orbit_index].to_pandas()[ind].diff()
        else:
            orbit_lt_diff = self.sat[self.orbit_index][ind].diff()
        # look for time gaps between partial orbits. The full orbital time
        # period is not required between end of one orbit and begining of next
        # if first orbit is partial.  Also provides another general test of the
        # orbital breaks determined.
        idx, = np.where((orbit_ut_diff / self.orbit_period -
                         orbit_lt_diff.values / orbit_index_period) > 0.97)
        # pull out breaks that pass the test, need to make sure the first one
        # is always included it gets dropped via the nature of diff
        if len(idx) > 0:
            if idx[0] != 0:
                idx = np.hstack((0, idx))
        else:
            idx = np.array([0])
        # only keep the good indices
        if len(ind) > 0:
            ind = ind[idx]
            # create orbitbreak index, ensure first element is always 0
            if ind[0] != 0:
                ind = np.hstack((np.array([0]), ind))
        else:
            ind = np.array([0])
        # number of orbits
        num_orbits = len(ind)
        # set index of orbit breaks
        self._orbit_breaks = ind
        # set number of orbits for the day
        self.num = num_orbits

    def _polarBreaks(self):
        """Determine where breaks in a polar orbiting satellite orbit occur.

        Looks for sign changes in latitude (magnetic or geographic) as well as
        breaks in UT.
        """

        if self.orbit_index is None:
            raise ValueError('Orbit properties must be defined at ' +
                             'pysat.Instrument object instantiation.' +
                             'See Instrument docs.')
        else:
            try:
                self.sat[self.orbit_index]
            except KeyError as err:
                raise ValueError(''.join((str(err), '\n',
                                          'Provided orbit index does not ',
                                          'appear to exist in loaded data')))

        # determine where orbit index goes from positive to negative
        pos = (self.sat[self.orbit_index] >= 0)
        npos = np.logical_not(pos)
        change = (pos.values[:-1] & npos.values[1:]) | (npos.values[:-1] &
                                                        pos.values[1:])

        ind, = np.where(change)
        ind += 1

        ut_diff = Series(self.sat.index).diff()
        ut_ind, = np.where(ut_diff / self.orbit_period > 0.95)

        if len(ut_ind) > 0:
            ind = np.hstack((ind, ut_ind))
            ind = np.sort(ind)
            ind = np.unique(ind)

        # create orbitbreak index, ensure first element is always 0
        if len(ind) > 0:
            if ind[0] != 0:
                ind = np.hstack((np.array([0]), ind))
        else:
            ind = np.array([0])
        # number of orbits
        num_orbits = len(ind)
        # set index of orbit breaks
        self._orbit_breaks = ind
        # set number of orbits for the day
        self.num = num_orbits

    def _orbitNumberBreaks(self):
        """Determine where orbital breaks in a dataset with orbit numbers
        occur.

        Looks for changes in unique values.

        """

        if self.orbit_index is None:
            raise ValueError('Orbit properties must be defined at ' +
                             'pysat.Instrument object instantiation.' +
                             'See Instrument docs.')
        else:
            try:
                self.sat[self.orbit_index]
            except KeyError as err:
                raise ValueError(''.join((str(err), '\n',
                                          'Provided orbit index does not ',
                                          'appear to exist in loaded data')))

        # determine where the orbit index changes from one value to the next
        uniq_vals = np.unique(self.sat[self.orbit_index].values)
        orbit_index = []
        for val in uniq_vals:
            idx, = np.where(val == self.sat[self.orbit_index].values)
            orbit_index.append(idx[0])

        # create orbitbreak index, ensure first element is always 0
        if len(orbit_index) > 0:
            if orbit_index[0] != 0:
                ind = np.hstack((np.array([0]), orbit_index))
            else:
                ind = orbit_index
        else:
            ind = np.array([0])
        # number of orbits
        num_orbits = len(ind)
        # set index of orbit breaks
        self._orbit_breaks = ind
        # set number of orbits for the day
        self.num = num_orbits

    def _getBasicOrbit(self, orbit=None):
        """Load a particular orbit into .data for loaded day.

        Parameters
        ----------
        orbit : int
            orbit number, 1 indexed, negative indexes allowed, -1 last orbit

        Note
        ----
        A day of data must be loaded before this routine functions properly.
        If the last orbit of the day is requested, it will NOT automatically be
        padded with data from the next day.
        """
        # ensure data exists
        if not self.sat.empty:
            # ensure proper orbit metadata present
            self._calcOrbits()

            # ensure user is requesting a particular orbit
            if orbit is not None:
                # set up data access for both pandas and xarray
                self.sat.data = self._fullDayData
                # pull out requested orbit
                if orbit == -1:
                    # load orbit data into data
                    self.sat.data = self.sat[self._orbit_breaks[self.num +
                                                                orbit]:]
                    self._current = self.num + orbit + 1
                elif ((orbit < 0) & (orbit >= -self.num)):
                    # load orbit data into data
                    self.sat.data = self.sat[self._orbit_breaks[self.num +
                                                                orbit]:
                                             self._orbit_breaks[self.num +
                                                                orbit + 1]]

                    self._current = self.num + orbit + 1
                elif (orbit < self.num) & (orbit != 0):
                    # load orbit data into data
                    self.sat.data = self.sat[self._orbit_breaks[orbit - 1]:
                                             self._orbit_breaks[orbit]]
                    self._current = orbit
                elif orbit == self.num:
                    self.sat.data = self.sat[self._orbit_breaks[orbit - 1]:]
                    # recent addition, wondering why it wasn't there before,
                    # could just be a bug that is now fixed.
                    self._current = orbit
                elif orbit == 0:
                    raise ValueError('Orbits internally indexed by 1, 0 not ' +
                                     'allowed')
                else:
                    # gone too far
                    self.sat.data = []
                    raise ValueError('Requested an orbit past total orbits ' +
                                     'for day')
            else:
                raise ValueError('Must set an orbit')

    def load(self, orbit=None):
        """Load a particular orbit into .data for loaded day.

        Parameters
        ----------
        orbit : int
            orbit number, 1 indexed

        Note
        ----
        A day of data must be loaded before this routine functions properly.
        If the last orbit of the day is requested, it will automatically be
        padded with data from the next day. The orbit counter will be
        reset to 1.
        """
        if not self.sat.empty:  # ensure data exists
            # set up orbit metadata
            self._calcOrbits()
            # ensure user supplied an orbit
            if orbit is not None:
                # pull out requested orbit
                if orbit < 0:
                    # negative indexing consistent with numpy, -1 last,
                    # -2 second to last, etc.
                    orbit = self.num + 1 + orbit

                if orbit == self.num:
                    # we get here if user asks for last orbit
                    # this call is first to trap case where there is only one orbit (self.num=1)
                    # which needs to be treated differently than a orbit=1 call
                    if self.num != 1:
                        # more than one orbit, go back one (simple call)
                        # and then forward doing full logic for breaks across day
                        self._getBasicOrbit(self.num - 1)
                        self.next()
                    else:
                        # only one complete orbit in file, or less                        
                        # check if we are close to begining or end of day
                        date = self.sat.date                        
                        delta_start = self.sat.index[-1] - date
                        delta_end = date + pds.DateOffset(days=1) \
                                    - self.sat.index[0]

                        if delta_start <= self.orbit_period*1.05:
                            # near begining
                            # load previous file, then go forward one orbit
                            self.sat.prev()
                            self.next()
                            if self.sat.index[-1] < date + delta_start:
                                # we could go back a day, iterate over orbit,
                                # as above, and the data we have is the wrong day
                                # In this case, move forward again.
                                # happens when previous day doesn't have data 
                                # near end of the day
                                self.next()
                                
                        elif delta_end <= self.orbit_period*1.05:
                            # near end
                            # load next file, then go back one orbit
                            self.sat.next()
                            self.prev()
                            if self.sat.index[0] > date + pds.DateOffset(days=1) \
                                                   - delta_end:
                                # we could go forward a day, iterate over orbit, 
                                # as above, and the data we have is the wrong day
                                # In this case, move back again.
                                # happens when next day doesn't have data 
                                # near begining of the day
                                self.prev()
                        else:
                            # not near begining or end, just get the last orbit 
                            # available (only one)
                            self._getBasicOrbit(orbit=-1)

                elif orbit == 1:
                    # user asked for first orbit
                    try:
                        # orbit could start file previous
                        # check for this condition
                        # store real date user wants
                        true_date = self.sat.date
                        # go back a day
                        self.sat.prev()
                        # if and else added becuase of CINDI turn off
                        # 6/5/2013, turn on 10/22/2014
                        # crashed when starting on 10/22/2014
                        # prev returned empty data
                        if not self.sat.empty:
                            # get last orbit if there is data
                            # this will deal with orbits across file cleanly
                            self.load(orbit=-1)
                        else:
                            # no data, no previous data to account for
                            # move back to original data, do simple load
                            # of first orbit
                            self.sat.next()
                            self._getBasicOrbit(orbit=1)
                        # check that this orbit should end on the current day
                        delta = true_date - self.sat.index[0]
                        if delta >= self.orbit_period:
                            # the orbit loaded isn't close enough to date
                            # to be the first orbit of the day, move forward
                            self.next()
                    except StopIteration:
                        self._getBasicOrbit(orbit=1)
                        # includes hack to appear to be zero indexed
                        logger.info('Loaded Orbit:%i' % (self._current - 1))
                        # check if the first orbit is also the last orbit

                elif orbit < self.num:
                    # load orbit data into data
                    self._getBasicOrbit(orbit)
                    # includes hack to appear to be zero indexed
                    logger.info('Loaded Orbit:%i' % (self._current - 1))

                else:
                    # gone too far
                    self.sat.data = self.sat._null_data
                    raise Exception('Requested an orbit past total orbits ' +
                                    'for day')
            else:
                raise Exception('Must set an orbit')
        else:
            logger.info('No data loaded in instrument object to determine orbits.')

    def next(self, *arg, **kwarg):
        """Load the next orbit into .data.

        Note
        ----
        Forms complete orbits across day boundaries. If no data loaded
        then the first orbit from the first date of data is returned.
        """

        # first, check if data exists
        if not self.sat.empty:
            # set up orbit metadata
            self._calcOrbits()

            # if current orbit near the last, must be careful
            if self._current == (self.num - 1):
                # first, load last orbit data
                self._getBasicOrbit(orbit=-1)
                # End of orbit may occur on the next day
                load_next = True
                if self.sat._iter_type == 'date':
                    delta = self.sat.date - self.sat.index[-1] \
                            + pds.Timedelta('1 day')
                    if delta >= self.orbit_period:
                        # don't need to load the next day because this orbit
                        # ends more than a orbital period from the next date
                        load_next = False

                if load_next:
                    # the end of the user's desired orbit occurs tomorrow, need
                    # to form a complete orbit save this current orbit, load
                    # the next day, combine data, select the correct orbit
                    temp_orbit_data = self.sat.copy()
                    try:
                        # loading next day/file clears orbit breaks info
                        self.sat.next()
                        if not self.sat.empty:
                            # combine this next day's data with previous last
                            # orbit, grab the first one
                            final_val = self.sat.index[0] \
                                - pds.DateOffset(microseconds=1)
                            self.sat.data = self.sat.concat_data(
                                [temp_orbit_data[:final_val],
                                 self.sat.data])
                            self._getBasicOrbit(orbit=1)
                        else:
                            # no data, go back a day and grab the last orbit.
                            # As complete as orbit can be
                            self.sat.prev()
                            self._getBasicOrbit(orbit=-1)
                    except StopIteration:
                        pass
                    del temp_orbit_data
                # includes hack to appear to be zero indexed
                logger.info('Loaded Orbit:%i' % (self._current - 1))

            elif self._current == (self.num):
                # at the last orbit, need to be careful about getting the next
                # orbit save this current orbit and load the next day
                # temp_orbit_data = self.sat.data.copy()
                temp_orbit_data = self.sat.copy()
                # load next day, which clears orbit breaks info
                self.sat.next()
                # combine this next day orbit with previous last orbit to
                # ensure things are correct
                if not self.sat.empty:
                    pad_next = True
                    # check if data padding is really needed, only works when
                    # loading by date
                    if self.sat._iter_type == 'date':
                        delta = self.sat.date - temp_orbit_data.index[-1]
                        if delta >= self.orbit_period:
                            # the end of the previous orbit is more than an
                            # orbit away from today we don't have to worry
                            # about it
                            pad_next = False
                    if pad_next:
                        # orbit went across day break, stick old orbit onto new
                        # data and grab second orbit (first is old)
                        self.sat.data = self.sat.concat_data(
                            [temp_orbit_data[:self.sat.index[0] -
                                             pds.DateOffset(microseconds=1)],
                             self.sat.data])
                        # select second orbit of combined data
                        self._getBasicOrbit(orbit=2)
                    else:
                        # padding from the previous orbit wasn't needed, can
                        # just grab the first orbit of loaded data
                        self._getBasicOrbit(orbit=1)
                        if self.sat._iter_type == 'date':
                            delta = self.sat.date + pds.DateOffset(days=1) \
                                    - self.sat.index[0]

                            if delta < self.orbit_period:
                                # this orbits end occurs on the next day,
                                # though we grabbed the first orbit, missing
                                # data means the first available orbit in the
                                # datais actually the last for the day.
                                # Resetting to the second to last orbit and t
                                # hen callingnext() will get the last orbit,
                                # accounting for tomorrow's data as well.
                                self._current = self.num - 1
                                self.next()
                else:
                    # no data for the next day
                    # continue loading data until there is some
                    # nextData raises StopIteration when it reaches the end,
                    # leaving this function
                    while self.sat.empty:
                        self.sat.next()
                    self._getBasicOrbit(orbit=1)

                del temp_orbit_data
                # includes hack to appear to be zero indexed
                logger.info('Loaded Orbit:%i' % (self._current - 1))

            elif self._current == 0:
                # no current orbit set, grab the first one
                # using load command to specify the first orbit, which
                # automatically loads prev day if needed to form complete orbit
                self.load(orbit=1)

            elif self._current < (self.num - 1):
                # since we aren't close to the last orbit, just pull the next
                # orbit
                self._getBasicOrbit(orbit=self._current + 1)
                # includes hack to appear to be zero indexed
                logger.info('Loaded Orbit:%i' % (self._current - 1))

            else:
                raise Exception(' '.join(('You ended up where nobody should',
                                          'ever be. Talk to someone about',
                                          'this fundamental failure or open',
                                          'an issue at',
                                          'www.github.com/rstonback/pysat')))

        else:  # no data
            while self.sat.empty:
                # keep going until data is found
                # next raises stopIteration at end of data set, no more data
                # possible
                self.sat.next()
            # we've found data, grab the next orbit
            self.next()

    def prev(self, *arg, **kwarg):
        """Load the previous orbit into .data.

        Note
        ----
        Forms complete orbits across day boundaries. If no data loaded
        then the last orbit of data from the last day is loaded into .data.
        """

        # first, check if data exists
        if not self.sat.empty:
            # set up orbit metadata
            self._calcOrbits()
            # if not close to the first orbit,just pull the previous orbit

            if (self._current > 2) & (self._current <= self.num):
                # load orbit and put it into self.sat.data
                self._getBasicOrbit(orbit=self._current - 1)
                logger.info('Loaded Orbit:%i' % (self._current - 1))

            # if current orbit near the first, must be careful
            elif self._current == 2:
                # first, load prev orbit data
                self._getBasicOrbit(orbit=self._current - 1)

                load_prev = True
                if self.sat._iter_type == 'date':
                    delta = self.sat.index[-1] - self.sat.date
                    if delta >= self.orbit_period:
                        # don't need to load the prev day because this orbit
                        # ends more than a orbital period from start of today's
                        # date
                        load_prev = False

                if load_prev:
                    # need to save this current orbit and load the prev day
                    temp_orbit_data = self.sat[self.sat.date:]
                    # load previous day, which clears orbit breaks info

                    try:
                        self.sat.prev()
                        # combine this next day orbit with previous last orbit
                        if not self.sat.empty:
                            self.sat.data = \
                                self.sat.concat_data([self.sat.data,
                                                      temp_orbit_data])
                            # select first orbit of combined data
                            self._getBasicOrbit(orbit=-1)
                        else:
                            self.sat.next()
                            self._getBasicOrbit(orbit=1)
                    except StopIteration:
                        # if loading the first orbit, of first day of data,
                        # you'll end up here as the attempt to make a full
                        # orbit will move the date backwards, and StopIteration
                        # is made. everything is already ok, just move along
                        pass

                    del temp_orbit_data

                logger.info('Loaded Orbit:%i' % (self._current - 1))

            elif self._current == 0:
                self.load(orbit=-1)
                return

            elif self._current < 2:
                # first, load prev orbit data
                self._getBasicOrbit(orbit=1)
                # need to save this current orbit and load the prev day
                temp_orbit_data = self.sat[self.sat.date:]
                # load previous day, which clears orbit breaks info
                self.sat.prev()
                # combine this next day orbit with previous last orbit

                if not self.sat.empty:
                    load_prev = True
                    if self.sat._iter_type == 'date':
                        delta = self.sat.date - self.sat.index[-1] \
                                + pds.Timedelta('1 day')
                        if delta >= self.orbit_period:
                            # don't need to load the prev day because this
                            # orbit ends more than a orbital period from start
                            # of today's date
                            load_prev = False

                    if load_prev:
                        self.sat.data = self.sat.concat_data([self.sat.data,
                                                              temp_orbit_data])
                        # select second to last orbit of combined data
                        self._getBasicOrbit(orbit=-2)
                    else:
                        # padding from the previous is needed
                        self._getBasicOrbit(orbit=-1)
                        if self.sat._iter_type == 'date':
                            delta = self.sat.date - self.sat.index[-1] \
                                    + pds.Timedelta('1 day')
                            if delta < self.orbit_period:
                                self._current = self.num
                                self.prev()
                else:
                    while self.sat.empty:
                        self.sat.prev()
                    self._getBasicOrbit(orbit=-1)

                del temp_orbit_data
                logger.info('Loaded Orbit:%i' % (self._current - 1))

            else:
                raise Exception(' '.join(('You ended up where nobody should',
                                          'ever be. Talk to someone about',
                                          'this fundamental failure or open',
                                          'an issue at',
                                          'www.github.com/rstonback/pysat')))
            # includes hack to appear to be zero indexed
        else:
            # no data
            while self.sat.empty:
                self.sat.prev()  # raises stopIteration at end of dataset
            self.prev()

    def __iter__(self):
        """Support iteration by orbit.

        For each iteration the next available orbit is loaded into
        inst.data.

        Examples
        --------
        ::

            for inst in inst.orbits:
                print('next available orbit ', inst.data)

        Note
        ----
        Limits of iteration set by setting inst.bounds.
        """
        # load up the first increment of data
        # coupling with Instrument frame is high, but it is already
        # high in a number of areas
        while self.sat.empty:
            self.sat.next()

        while True:
            try:
                self.next()
                yield self.sat
            except StopIteration:
                return
