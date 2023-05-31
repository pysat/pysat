"""Tests for iteration in the pysat Instrument object and methods.

Note
----
Base class stored here, but tests inherited by test_instrument.py

"""

import datetime as dt
import numpy as np

import pandas as pds
import pytest

import pysat
from pysat.utils import testing
from pysat.utils.time import filter_datetime_input


class InstIterationTests(object):
    """Basic tests for `pysat.Instrument` iteration methods.

    Note
    ----
    Inherited by classes in test_instrument.py.  Setup and teardown methods are
    specified there.

    See Also
    --------
    `pysat.tests.test_instrument`

    """

    def generate_fname(self, date):
        """Generate a filename for support of testing iterations.

        Parameters
        ----------
        date : dt.datetime
            A date to be converted to a filename.

        Returns
        -------
        filename : str
            Filename formatted to look like test instrument files.

        """

        fname = '{year:04d}-{month:02d}-{day:02d}.nofile'
        return fname.format(year=date.year, month=date.month, day=date.day)

    def get_fnames_times(self, inds=None):
        """Get file names and times (date only) by index.

        Parameters
        ----------
        inds : list or NoneType
            List of indices to return filename and file time values

        Returns
        -------
        fnames : list
            List of filenames
        ftimes : list
            List of datetimes corresponding to the files

        """

        fnames = list()
        ftimes = list()

        if inds is not None:
            for i in inds:
                fnames.append(self.testInst.files.files[i])
                ftimes.append(filter_datetime_input(pds.to_datetime(
                    self.testInst.files.files.index[i]).to_pydatetime()))

        return fnames, ftimes

    def eval_iter_list(self, start, stop, freq, dates=False):
        """Evaluate successful generation of iter_list for `self.testInst`.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            Start date for generating iter_list.
        stop : dt.datetime or list of dt.datetime
            start date for generating iter_list.
        freq : str
            Frequency string, following pandas conventions
        dates : bool
            If True, checks each date.  If False, checks against the _iter_list
            (default=False)

        """
        # Set the frequency
        kwargs = {'freq': freq}

        if isinstance(start, dt.datetime):
            out = pds.date_range(start, stop, **kwargs).tolist()
        else:
            out = list()
            for (istart, istop) in zip(start, stop):
                out.extend(pds.date_range(istart, istop, **kwargs).tolist())

        if dates:
            file_dates = [filter_datetime_input(ftime)
                          for ftime in self.testInst.files.files.index]
            dates = [inst.date for inst in self.testInst
                     if inst.date in file_dates]
            testing.assert_lists_equal(dates, out)
        else:
            testing.assert_lists_equal(self.testInst._iter_list, out)
        return

    def support_iter_evaluations(self, starts, stops, step, width,
                                 for_loop=False, reverse=False, by_date=True):
        """Support testing of `.next()`/`.prev()` via dates/files.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The end date for iterations, or dates for iteration over multiple
            segments.
        step : int or str
            The step size for the iteration bounds. If int, days are assumed.
        width : int or str
            The width of the iteration bounds. If int, days are assumed.
        for_loop : bool
            If True, iterate via for loop.  If False, iterate via while.
            (default=False)
        reverse : bool
            Direction of iteration.  If True, use `.prev()`. If False, use
            `.next()`.  (default=False)
        by_date : bool
            If True, set bounds by date.  If False, set bounds by filename.
            (default=False)

        """

        # Ensure dates are lists for consistency of later code.
        starts = pysat.utils.listify(starts)
        stops = pysat.utils.listify(stops)

        if by_date:
            # Convert step and width to string and timedelta.
            if type(step) in [int, np.int32, np.int64]:
                step = '{:}D'.format(step)
            if type(width) in [int, np.int32, np.int64]:
                width = dt.timedelta(days=width)
            else:
                width = pds.tseries.frequencies.to_offset(width)

            self.testInst.bounds = (starts, stops, step, width)
        else:
            # Convert start and stop to filenames.
            start_files = [self.generate_fname(date) for date in starts]
            stop_files = [self.generate_fname(date) for date in stops]
            self.testInst.bounds = (start_files, stop_files, step, width)

            # Convert step and width for future use
            if type(step) in [int, np.int32, np.int64]:
                step = '{:}D'.format(step)

            if type(width) in [int, np.int32, np.int64]:
                wstr = '{:d}{:s}'.format(
                    width, self.testInst.files.files.index.freqstr)
                width = pds.tseries.frequencies.to_offset(wstr)

        # Iterate until we run out of bounds
        file_dates = [filter_datetime_input(ftime)
                      for ftime in self.testInst.files.files.index]
        dates = []
        time_range = []
        if for_loop:
            # Iterate via for loop option
            for inst in self.testInst:
                if inst.date in file_dates:
                    dates.append(inst.date)
                    if len(inst.index) > 0:
                        time_range.append((inst.index[0], inst.index[-1]))
                    else:
                        time_range.append(())
        else:
            # Iterate forwards or backwards using `.next()` or `.prev()`
            if reverse:
                iterator = self.testInst.prev
            else:
                iterator = self.testInst.next

            try:
                while True:
                    iterator()
                    dates.append(self.testInst.date)
                    time_range.append((self.testInst.index[0],
                                       self.testInst.index[-1]))
            except StopIteration:
                # Reached the end
                pass

        # Deal with file or date iteration, make file inputs same as date for
        # verification purposes.
        out = []
        foff = pds.tseries.frequencies.to_offset(
            self.testInst.files.files.index.freqstr)
        for start, stop in zip(starts, stops):
            if start in file_dates:
                tdate = stop - width + foff
                out.extend(pds.date_range(start, tdate, freq=step).tolist())

        if reverse:
            # Ensure time order is consistent for verify methods.
            out = out[::-1]
        testing.assert_lists_equal(dates, out)

        # Assign the output
        output = {'expected_times': out, 'observed_times': time_range,
                  'starts': starts, 'stops': stops, 'width': width,
                  'step': step}

        return output

    def verify_iteration(self, out, reverse=False):
        """Verify loaded dates for iteration, forward or backward.

        Parameters
        ----------
        reverse : bool
            If True, use move backwards through the list. If False, move
            forwards. (default=False)

        """

        # Inclusive checks require shifting some expected dates
        check_inc = pds.tseries.frequencies.to_offset(
            self.testInst.files.files.index.freqstr)

        # Arithmetic operations must be performed on datetime objects,
        # not timedelta or DateOffset objects.
        delta_inc = pds.tseries.frequencies.to_offset(
            out['width']) + out['starts'][0] + check_inc - out['starts'][0]

        # Verify range of loaded data for each iteration step.
        for i, trange in enumerate(out['observed_times']):
            # Determine the current range.
            b_range = 0
            while out['expected_times'][i] > out['stops'][b_range]:
                b_range += 1

            # Check that loaded range is correct.
            assert trange[0] == out['expected_times'][i], \
                "Loaded start time is not correct: {:} != {:}".format(
                    trange[0], out['expected_times'][i])

            check = out['expected_times'][i] + out['width'] - check_inc
            assert trange[1] > check, \
                "End time lower than expected: {:} <= {:}".format(
                    trange[1], check)

            check = out['stops'][b_range] + delta_inc
            assert trange[1] < check, \
                "End time higher than expected {:} >= {:}".format(
                    trange[1], check)

            end_of_range = out['stops'][b_range] + dt.timedelta(days=1)
            assert trange[1] < end_of_range, "End time higher than expected"

            if reverse:
                if i == 0:
                    # Check that first load is before end of bounds.
                    check = out['stops'][b_range] - out['width'] + check_inc

                    assert trange[0] <= check, \
                        "Start time is too high: {:} >= {:}: {:}".format(
                            trange[0], check, out)

                    tdate = filter_datetime_input(trange[1])
                    assert tdate <= out['stops'][b_range], \
                        "Stop time higher than expected: {:} > {:}".format(
                            tdate, out['stops'][b_range])

                    check = out['stops'][b_range] + delta_inc
                    assert trange[1] < check, \
                        "Stop time higher than expected: {:} >= {:}".format(
                            trange[1], check)
                elif i == (len(out['observed_times']) - 1):
                    # Check that last load is at start of bounds.
                    assert trange[0] == out['starts'][b_range], \
                        "Loaded start time is wrong: {:} != {:}".format(
                            trange[0], out['starts'][b_range])
                    assert trange[1] > out['starts'][b_range], \
                        "End time lower than expected: {:} <= {:}".format(
                            trange[1], out['starts'][b_range])
                    assert trange[1] < out['starts'][b_range] + out['width'], \
                        "End time higher than expected: {:} <= {:}".format(
                            trange[1], out['starts'][b_range])

        return

    @pytest.mark.parametrize("operator", [('next'), ('prev')])
    def test_file_load_empty_iteration(self, operator):
        """Ensure empty iteration list is fine via day iteration.

        Parameters
        ----------
        operator : str
            Name of iterator to use.

        """

        start_time = self.testInst.files.files.index[-1] + dt.timedelta(days=1)
        end_time = start_time + dt.timedelta(days=1)
        self.testInst.bounds = (start_time, end_time)
        testing.eval_bad_input(getattr(self.testInst, operator), StopIteration,
                               'File list is empty. ')

        return

    @pytest.mark.parametrize("first,second", [('next', 'prev'),
                                              ('prev', 'next')])
    def test_passing_bounds_with_iteration(self, first, second):
        """Test if passing bounds raises StopIteration.

        Parameters
        ----------
        first : str
            Name of first iterator to use.
        second : str
            Name of second iterator to use, should be in the opposite direction.

        """

        # Load first data
        getattr(self.testInst, first)()
        testing.eval_bad_input(getattr(self.testInst, second), StopIteration,
                               "Outside the set date boundaries")
        return

    def test_set_bounds_with_frequency(self):
        """Test setting bounds with non-default step."""

        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=14)
        self.testInst.bounds = (start, stop, 'MS')
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='MS').tolist())
        return

    def test_iterate_bounds_with_frequency(self):
        """Test iterating bounds with non-default step."""

        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=15)
        freq = '2{:s}'.format(self.testInst.files.files.index.freqstr)
        self.testInst.bounds = (start, stop, freq)
        self.eval_iter_list(start, stop, freq, dates=True)
        return

    def test_set_bounds_with_frequency_and_width(self):
        """Set date bounds with step/width > 1."""

        start = self.ref_time
        stop = self.ref_time + pds.DateOffset(months=11, days=25)
        stop = stop.to_pydatetime()
        freq = '2{:s}'.format(self.testInst.files.files.index.freqstr)
        self.testInst.bounds = (start, stop, freq,
                                pds.tseries.frequencies.to_offset(freq))
        testing.assert_lists_equal(self.testInst._iter_list,
                                   pds.date_range(start, stop,
                                                  freq=freq).tolist())
        return

    def test_iterate_index_error(self):
        """Test iterate raises IndexError when there are no dates to iterate."""

        _, ftimes = self.get_fnames_times(inds=[0, 2])
        step = '1{:s}'.format(self.testInst.files.files.index.freqstr)
        width = '4{:s}'.format(self.testInst.files.files.index.freqstr)
        input_args = [*ftimes, step, width]
        input_kwargs = {'for_loop': True, 'by_date': True}

        testing.eval_bad_input(self.support_iter_evaluations, IndexError,
                               "No dates to iterate over", input_args,
                               input_kwargs)
        return

    @pytest.mark.parametrize("file_inds", [([0, 2]), ([0, 3]), ([0, 4])])
    @pytest.mark.parametrize("step,width", [(2, 2), (2, 3), (3, 1)])
    @pytest.mark.parametrize("by_date", [True, False])
    @pytest.mark.parametrize("reverse,for_loop",
                             [(True, False), (False, False), (False, True)])
    def test_iterate_bounds_with_frequency_and_width(self, file_inds, step,
                                                     width, by_date,
                                                     reverse, for_loop):
        """Test iterate via date with mixed step/width.

        Parameters
        ----------
        file_inds : list
            List of indices for the start and stop file times
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.
        reverse : bool
            If True, iterate backwards.  If False, iterate forwards. Only used
            when `for_loop=False`.
        for_loop : bool
            If True, iterate via for loop.  If False, iterate via while.

        """
        # Get the desired file times
        _, ftimes = self.get_fnames_times(inds=file_inds)

        # Convert integer steps/widths to strings, allowing multiple freq types
        step = '{:d}{:s}'.format(step, self.testInst.files.files.index.freqstr)
        if by_date:
            width = '{:d}{:s}'.format(width,
                                      self.testInst.files.files.index.freqstr)

        # Evaluate and verify the iterations
        out = self.support_iter_evaluations(*ftimes, step, width,
                                            for_loop=for_loop, by_date=by_date,
                                            reverse=reverse)
        self.verify_iteration(out, reverse=reverse)

        return

    @pytest.mark.parametrize("start_inds,stop_inds",
                             [([0], [2]), ([0, 3], [1, 4])])
    @pytest.mark.parametrize("step,width", [(2, 2), (5, 1), (3, 2)])
    @pytest.mark.parametrize("by_date", [True, False])
    @pytest.mark.parametrize("reverse,for_loop",
                             [(True, False), (False, False), (False, True)])
    def test_iterate_seasonal_bounds_with_frequency_and_width(
            self, start_inds, stop_inds, step, width, by_date, reverse,
            for_loop):
        """Test iterate via date with mixed step/width.

        Parameters
        ----------
        start_inds : list
            The index(es) corresponding to the start file(s)
        stop_inds : list
            The index(es) corresponding to the stop file(s)
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.
        reverse : bool
            If True, iterate backwards.  If False, iterate forwards. Only used
            when `for_loop=False`.
        for_loop : bool
            If True, iterate via for loop.  If False, iterate via while.

        """
        # Get the desired file times
        _, start_times = self.get_fnames_times(inds=start_inds)
        _, stop_times = self.get_fnames_times(inds=stop_inds)

        # Convert integer steps/widths to strings, allowing multiple freq types
        step = '{:d}{:s}'.format(step, self.testInst.files.files.index.freqstr)
        if by_date:
            width = '{:d}{:s}'.format(width,
                                      self.testInst.files.files.index.freqstr)

        # Evaluate and verify the iterations
        out = self.support_iter_evaluations(start_times, stop_times, step,
                                            width, for_loop=for_loop,
                                            by_date=by_date, reverse=reverse)
        self.verify_iteration(out, reverse=reverse)

        return

    @pytest.mark.parametrize("new_bounds,errmsg",
                             [([dt.datetime(2009, 1, 1)],
                               "Must supply both a start and stop date/file"),
                              ([dt.datetime(2009, 1, 1), '2009-01-01.nofile'],
                               "must all be of the same type"),
                              ([dt.datetime(2009, 1, 1), 1],
                               "must all be of the same type"),
                              ([[dt.datetime(2009, 1, 1)] * 2,
                                '2009-01-01.nofile'],
                               "must have the same number of elements"),
                              ([[dt.datetime(2009, 1, 1)] * 2,
                               [dt.datetime(2009, 1, 1), '2009-01-01.nofile']],
                               "must all be of the same type"),
                              ([dt.datetime(2009, 1, 1),
                                dt.datetime(2009, 1, 1), '1D',
                                dt.timedelta(days=1), False],
                               'Too many input arguments.'),
                              ([1.0, 1.0], 'Input is not a known type')])
    def test_set_bounds_error_message(self, new_bounds, errmsg):
        """Test ValueError when setting bounds with wrong inputs.

        Parameters
        ----------
        new_bounds : list
            Defines new iteration bounds incorrectly.
        err_msg : str
            A string pattern that shoul be raised by defining the bounds as
            in new_bounds.

        """
        # Use pytest evaluation, as properties do not act like functions
        with pytest.raises(ValueError) as verr:
            self.testInst.bounds = new_bounds

        assert str(verr).find(errmsg) >= 0
        return

    @pytest.mark.parametrize("type_ind", [(0), (1)])
    def test_set_bounds_default_start(self, type_ind):
        """Test set bounds with default start.

        Parameters
        ----------
        type_ind : int
            Index where 0 takes the file names and 1 takes the file times

        """

        # Get the desired ending time and file
        fvals = self.get_fnames_times([1])

        # Set the bounds with either the time or the value
        self.testInst.bounds = [None, fvals[type_ind][0]]

        # Get the first time or file and check the bounds iteration type
        if type_ind == 0:
            assert self.testInst._iter_type == "file", "Not iterating by file"
            check = self.testInst.files[0]
        else:
            assert self.testInst._iter_type == "date", "Not iterating by date"
            check = filter_datetime_input(self.testInst.files.files.index[0])

        # Evaluate the bounds starting value
        assert self.testInst.bounds[0][0] == check, "Unexpected starting bound"
        return

    @pytest.mark.parametrize("type_ind", [(0), (1)])
    def test_set_bounds_default_stop(self, type_ind):
        """Test set bounds with default stop.

        Parameters
        ----------
        type_ind : int
            Index where 0 takes the file names and 1 takes the file times

        """
        # Get the desired ending time and file
        fvals = self.get_fnames_times([1])

        # Set the bounds with either the time or the value
        self.testInst.bounds = [fvals[type_ind][0], None]

        # Get the first time or file and check the bounds iteration type
        if type_ind == 0:
            assert self.testInst._iter_type == "file", "Not iterating by file"
            check = self.testInst.files[-1]
        else:
            assert self.testInst._iter_type == "date", "Not iterating by date"
            check = filter_datetime_input(self.testInst.files.files.index[-1])

        assert self.testInst.bounds[1][0] == check, "Unexpeding ending bound"
        return

    @pytest.mark.parametrize("bound_val", [(None, None), None])
    def test_set_bounds_by_default_dates(self, bound_val):
        """Verify bounds behavior with default date related inputs.

        Parameters
        ----------
        bound_val : tuple or NoneType
            Values to set equal to the Instrument.bounds attribute

        """

        self.testInst.bounds = bound_val
        self.eval_iter_list(self.testInst.files.start_date,
                            self.testInst.files.stop_date,
                            self.testInst.files.files.index.freqstr)
        return

    @pytest.mark.parametrize("start_inds,stop_inds",
                             [([0], [2]), ([0, 3], [2, 4])])
    def test_set_bounds_by_date(self, start_inds, stop_inds):
        """Test setting bounds with datetimes over simple range and season.

        Parameters
        ----------
        start_inds : list
            The start indices of the new bounds.
        stop_inds : list
            The stop indices of the new bounds.

        """
        _, start_times = self.get_fnames_times(start_inds)
        _, stop_times = self.get_fnames_times(stop_inds)

        self.testInst.bounds = (start_times, stop_times)
        self.eval_iter_list(start_times, stop_times,
                            self.testInst.files.files.index.freqstr)
        return

    @pytest.mark.parametrize("start_inds,stop_inds", [([1], [0]),
                                                      ([0, 2], [1, 1])])
    def test_set_bounds_by_date_wrong_order(self, start_inds, stop_inds):
        """Test error if bounds assignment has stop date before start.

        Parameters
        ----------
        start_inds : list
            The start indices of the new bounds.
        stop_inds : list
            The stop indices of the new bounds.

        """
        _, start_times = self.get_fnames_times(start_inds)
        _, stop_times = self.get_fnames_times(stop_inds)

        # Use pytest evaluation, as properties do not act like functions
        with pytest.raises(ValueError) as verr:
            self.testInst.bounds = (start_times, stop_times)

        assert str(verr).find('Bounds must be set in increasing') >= 0
        return

    @pytest.mark.parametrize("start_inds,stop_inds",
                             [([0], [2]), ([0, 1], [1, 2])])
    @pytest.mark.parametrize("set_date", [True, False])
    def test_set_bounds_by_date_extra_time(self, start_inds, stop_inds,
                                           set_date):
        """Test set bounds by date with extra time.

        Parameters
        ----------
        start_inds : list
            The start indices of the new bounds.
        stop_inds : list
            The stop indices of the new bounds.
        set_date : bool
            Set by date or not

        Note
        ----
        Only the date portion is retained, hours and shorter timespans are
        dropped.

        """
        # Set the bounds
        _, start_times = self.get_fnames_times(start_inds)
        start_times = [stime + dt.timedelta(seconds=3650)
                       for stime in start_times]
        _, stop_times = self.get_fnames_times(stop_inds)
        stop_times = [stime + dt.timedelta(seconds=3650)
                      for stime in stop_times]
        self.testInst.bounds = (start_times, stop_times)

        # Evaluate the results
        start = filter_datetime_input(start_times)
        stop = filter_datetime_input(stop_times)

        self.eval_iter_list(
            start, stop, self.testInst.files.files.index.freqstr,
            dates=set_date)
        return

    @pytest.mark.parametrize("start_inds,stop_inds",
                             [([[0], [1]]), ([[1], [2]]), ([0, 3], [1, 4])])
    def test_iterate_over_bounds_set_by_date(self, start_inds, stop_inds):
        """Test iterate over bounds via single date range.

        Parameters
        ----------
        start_inds : list
            The start indices of the new bounds.
        stop_inds : list
            The stop indices of the new bounds.

        """
        _, start_times = self.get_fnames_times(start_inds)
        _, stop_times = self.get_fnames_times(stop_inds)

        self.testInst.bounds = (start_times, stop_times)

        # Filter time inputs.
        start = filter_datetime_input(start_times)
        stop = filter_datetime_input(stop_times)
        self.eval_iter_list(start, stop,
                            self.testInst.files.files.index.freqstr, dates=True)

        return

    def test_iterate_over_default_bounds(self):
        """Test iterate over default bounds."""

        # Establish a date range
        date_range = pds.date_range(
            self.ref_time, self.ref_time + pds.tseries.frequencies.to_offset(
                '3{:s}'.format(self.testInst.files.files.index.freqstr)),
            freq=self.testInst.files.files.index.freqstr)

        # Update the list of files
        self.testInst.kwargs['list_files']['file_date_range'] = date_range
        self.testInst.files.refresh()
        self.testInst.bounds = (None, None)

        self.eval_iter_list(date_range[0], date_range[-1], date_range.freqstr,
                            dates=True)
        return

    def test_iterate_over_bounds_set_by_fname(self):
        """Test iterate over bounds set by fname."""

        fnames, ftimes = self.get_fnames_times(inds=[0, 2])
        self.testInst.bounds = tuple(fnames)
        self.eval_iter_list(*ftimes, self.testInst.files.files.index.freqstr,
                            dates=True)

        return

    @pytest.mark.parametrize("start_inds,stop_inds",
                             [([2], [0]), ([0, 2], [1, 1])])
    def test_set_bounds_by_fname_wrong_order(self, start_inds, stop_inds):
        """Test for error if stop file before start file.

        Parameters
        ----------
        start_inds : list
            The index(es) corresponding to the start file(s)
        stop_inds : list
            The index(es) corresponding to the stop file(s)

        """
        start_names, _ = self.get_fnames_times(inds=start_inds)
        stop_names, _ = self.get_fnames_times(inds=stop_inds)

        # If this is a length one list, convert to a string
        if len(start_names) == 1:
            start_names = start_names[0]

        if len(stop_names) == 1:
            stop_names = stop_names[0]

        # Evaluate the error raised and its message
        with pytest.raises(ValueError) as err:
            self.testInst.bounds = (start_names, stop_names)

        estr = 'Bounds must be in increasing date'
        assert str(err).find(estr) >= 0

        return

    @pytest.mark.parametrize("operator", ['next', 'prev'])
    def test_iterate_over_bounds_set_by_fname_via_attr(self, operator):
        """Test iterate over bounds set by fname via operators.

        Parameters
        ----------
        operator : str
            Name of iterator to use.

        """
        fnames, ftimes = self.get_fnames_times(inds=[0, 1])

        self.testInst.bounds = tuple(fnames)
        dates = []
        loop_next = True
        while loop_next:
            try:
                getattr(self.testInst, operator)()
                dates.append(self.testInst.date)
            except StopIteration:
                loop_next = False
        out = pds.date_range(*ftimes,
                             freq=self.testInst.files.files.index.freq).tolist()
        testing.assert_lists_equal(dates, out)
        return

    def test_set_bounds_by_fname_season(self):
        """Test set bounds by fname season."""
        fnames, _ = self.get_fnames_times(inds=[0, 4, 2, 5])
        start = [fnames[0], fnames[1]]
        stop = [fnames[2], fnames[3]]

        check_list = self.testInst.files.files[0:6].tolist()
        check_list.pop(3)
        self.testInst.bounds = (start, stop)
        testing.assert_lists_equal(self.testInst._iter_list, check_list)
        return

    def test_iterate_over_bounds_set_by_fname_season(self):
        """Test set bounds using multiple filenames."""
        fnames, ftimes = self.get_fnames_times(inds=[0, 4, 2, 5])

        start = [fnames[0], fnames[1]]
        stop = [fnames[2], fnames[3]]
        start_d = [ftimes[0], ftimes[1]]
        stop_d = [ftimes[2], ftimes[3]]
        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start_d, stop_d,
                            self.testInst.files.files.index.freqstr, dates=True)

        return

    def test_set_bounds_fname_with_frequency(self):
        """Test set bounds using filenames and non-default step."""

        fnames, ftimes = self.get_fnames_times(inds=[0, 2])
        self.testInst.bounds = (*fnames, 2)
        freq = '2{:s}'.format(self.testInst.files.files.index.freqstr)
        out = pds.date_range(*ftimes, freq=freq).tolist()

        # Convert filenames in list to a date
        for i, item in enumerate(self.testInst._iter_list):
            snip = item.split('.')[0]
            ref_snip = out[i].strftime('%Y-%m-%d')
            assert snip == ref_snip
        return

    def test_iterate_bounds_fname_with_frequency(self):
        """Test iterate over bounds using filenames and non-default step."""

        fnames, ftimes = self.get_fnames_times(inds=[0, 2])
        freq = '2{:s}'.format(self.testInst.files.files.index.freqstr)
        self.testInst.bounds = (*fnames, 2)

        self.eval_iter_list(*ftimes, freq, dates=True)
        return

    def test_set_bounds_fname_with_frequency_and_width(self):
        """Test set fname bounds with step/width > 1."""

        fnames, ftimes = self.get_fnames_times(inds=[0, 2])
        freq = '2{:s}'.format(self.testInst.files.files.index.freqstr)
        self.testInst.bounds = (*fnames, 2, 2)
        out = pds.date_range(filter_datetime_input(ftimes[0]),
                             filter_datetime_input(ftimes[1]
                                                   - dt.timedelta(days=1)),
                             freq=freq).tolist()

        # Convert filenames in list to a date
        date_list = []
        for item in self.testInst._iter_list:
            snip = item.split('.')[0]
            date_list.append(dt.datetime.strptime(snip, '%Y-%m-%d'))

        # Evaluate the date components of the files and bounds
        testing.assert_lists_equal(date_list, out)
        return

    def test_iteration_in_list_comprehension(self):
        """Test list comprehensions for length, uniqueness, iteration."""
        if self.testInst.files.files.index.shape[0] >= 10:
            last_ind = 9
        else:
            last_ind = self.testInst.files.files.index.shape[0] - 1

        self.testInst.bounds = (self.testInst.files.files.index[0],
                                self.testInst.files.files.index[last_ind])
        # Ensure no data to begin
        assert self.testInst.empty

        # Perform comprehension and ensure there are as many as there should be
        file_dates = [filter_datetime_input(ftime)
                      for ftime in self.testInst.files.files.index]
        insts = [inst for inst in self.testInst if inst.date in file_dates]
        assert len(insts) == last_ind + 1, \
            'Found {:d} Instruments instead of {:d}'.format(len(insts),
                                                            last_ind + 1)

        # Get list of dates
        dates = pds.Series([inst.date for inst in insts])
        assert dates.is_monotonic_increasing

        # Dates are unique
        testing.assert_lists_equal(np.unique(dates), dates.values)

        # Iteration instruments are not the same as original
        for inst in insts:
            assert not (inst is self.testInst)

        # Check there is data after iteration
        assert not self.testInst.empty

        return
