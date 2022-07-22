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

    def eval_iter_list(self, start, stop, dates=False, freq=None):
        """Evaluate successful generation of iter_list for `self.testInst`.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            Start date for generating iter_list.
        stop : dt.datetime or list of dt.datetime
            start date for generating iter_list.
        dates : bool
            If True, checks each date.  If False, checks against the _iter_list
            (default=False)
        freq : int or NoneType
            Frequency in days.  If None, use pandas default. (default=None)

        """

        kwargs = {'freq': '{:}D'.format(freq)} if freq else {}

        if isinstance(start, dt.datetime):
            out = pds.date_range(start, stop, **kwargs).tolist()
        else:
            out = list()
            for (istart, istop) in zip(start, stop):
                out.extend(pds.date_range(istart, istop, **kwargs).tolist())
        if dates:
            dates = []
            for inst in self.testInst:
                dates.append(inst.date)
            pysat.utils.testing.assert_lists_equal(dates, out)
        else:
            pysat.utils.testing.assert_lists_equal(self.testInst._iter_list,
                                                   out)
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
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
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
            step = '{:}D'.format(step)
            width = dt.timedelta(days=width)
            self.testInst.bounds = (starts, stops, step, width)
        else:
            # Convert start and stop to filenames.
            start_files = [self.generate_fname(date) for date in starts]
            stop_files = [self.generate_fname(date) for date in stops]
            self.testInst.bounds = (start_files, stop_files, step, width)

        # Iterate until we run out of bounds
        dates = []
        time_range = []
        if for_loop:
            # Iterate via for loop option
            for inst in self.testInst:
                dates.append(inst.date)
                time_range.append((inst.index[0],
                                   inst.index[-1]))
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
        if isinstance(step, int):
            step = str(step) + 'D'
        if isinstance(width, int):
            width = dt.timedelta(days=width)

        out = []
        for start, stop in zip(starts, stops):
            tdate = stop - width + dt.timedelta(days=1)
            out.extend(pds.date_range(start, tdate, freq=step).tolist())
        if reverse:
            # Ensure time order is consistent for verify methods.
            out = out[::-1]
        pysat.utils.testing.assert_lists_equal(dates, out)

        output = {}
        output['expected_times'] = out
        output['observed_times'] = time_range
        output['starts'] = starts
        output['stops'] = stops
        output['width'] = width
        output['step'] = step
        return output

    def verify_iteration(self, out, reverse=False, inclusive=True):
        """Verify loaded dates for iteration, forward or backward.

        Parameters
        ----------
        reverse : bool
            If True, use move backwards through the list. If False, move
            forwards. (default=False)
        inclusive : bool
            If True, check that end of bounds is included in iterated dates.
            If False, check that end of bounds is excluded from iterated dates.
            (default=True)

        """

        # Inclusive checks require shifting some expected dates by 1.
        delta_inc = dt.timedelta(days=1) if inclusive else dt.timedelta(days=0)

        # Verify range of loaded data for each iteration step.
        for i, trange in enumerate(out['observed_times']):
            # Determine the current range.
            b_range = 0
            while out['expected_times'][i] > out['stops'][b_range]:
                b_range += 1

            # Check that loaded range is correct.
            assert trange[0] == out['expected_times'][i], \
                "Loaded start time is not correct"

            check = out['expected_times'][i] + out['width']
            check -= dt.timedelta(days=1)
            assert trange[1] > check, "End time lower than expected"

            check = out['stops'][b_range] + delta_inc
            assert trange[1] < check, "End time higher than expected"

            if reverse:
                end_of_range = out['stops'][b_range] + dt.timedelta(days=1)
                assert trange[1] < end_of_range, "End time higher than expected"
                if i == 0:
                    # Check that first load is before end of bounds.
                    check = out['stops'][b_range] - out['width']
                    check += dt.timedelta(days=1)

                    if inclusive:
                        assert trange[0] == check, \
                            "Incorrect start time"
                        assert trange[1] > out['stops'][b_range], \
                            "Stop time lower than expected"
                    else:
                        assert trange[0] < check, \
                            "Start time higher than expected"

                    check = out['stops'][b_range] + delta_inc
                    assert trange[1] < check, \
                        "Stop time higher than expected"
                elif i == (len(out['observed_times']) - 1):
                    # Check that last load is at start of bounds.
                    assert trange[0] == out['starts'][b_range], \
                        "Loaded start time is not correct"
                    assert trange[1] > out['starts'][b_range], \
                        "End time lower than expected"
                    assert trange[1] < out['starts'][b_range] + out['width'], \
                        "End time higher than expected"

        return

    @pytest.mark.parametrize("operator", [('next'), ('prev')])
    def test_file_load_empty_iteration(self, operator):
        """Ensure empty iteration list is fine via day iteration.

        Parameters
        ----------
        operator : str
            Name of iterator to use.

        """

        self.testInst.bounds = (None, None, '10000D',
                                dt.timedelta(days=10000))
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
        self.testInst.bounds = (start, stop, 'M')
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='M').tolist())
        return

    def test_iterate_bounds_with_frequency(self):
        """Test iterating bounds with non-default step."""

        start = self.ref_time
        stop = self.ref_time + dt.timedelta(days=15)
        self.testInst.bounds = (start, stop, '2D')
        self.eval_iter_list(start, stop, dates=True, freq=2)
        return

    def test_set_bounds_with_frequency_and_width(self):
        """Set date bounds with step/width > 1."""

        start = self.ref_time
        stop = self.ref_time + pds.DateOffset(months=11, days=25)
        stop = stop.to_pydatetime()
        self.testInst.bounds = (start, stop, '10D', dt.timedelta(days=10))
        assert np.all(self.testInst._iter_list
                      == pds.date_range(start, stop, freq='10D').tolist())
        return

    # TODO(#863): Remove hardwired dates and streamline here and below
    # TODO(#902): Combine inclusive and exclusive tests via parametrize
    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [(dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 3), 2, 2),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 4), 2, 3),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 5), 3, 1),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 17), 5, 1)])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_bounds_with_frequency_and_width(self, starts, stops, step,
                                                     width, by_date):
        """Test iterate via date with mixed step/width, excludes stop date.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            for_loop=True,
                                            by_date=by_date)
        self.verify_iteration(out, reverse=False, inclusive=False)

        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [(dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 4), 2, 2),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 4), 3, 1),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 4), 1, 4),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 5), 4, 1),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 5), 2, 3),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 5), 3, 2)])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_bounds_with_frequency_and_width_incl(self, starts, stops,
                                                          step, width, by_date):
        """Test iterate via date with mixed step/width, includes stop date.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            for_loop=True, by_date=by_date)
        self.verify_iteration(out, reverse=False, inclusive=True)

        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [(dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10), 2, 2),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 9), 4, 1),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 11), 1, 3),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 11), 1, 11)])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_with_frequency_and_width_incl(self, starts, stops, step,
                                                   width, reverse, by_date):
        """Test iteration via date step/width >1, includes stop date.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        reverse : bool
            If True, iterate backwards.  If False, iterate forwards.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            reverse=reverse, by_date=by_date)
        self.verify_iteration(out, reverse=reverse, inclusive=True)

        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [(dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 11), 2, 2),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 12), 2, 3),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 13), 3, 2),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 3), 4, 2),
         (dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 12), 2, 1)])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_with_frequency_and_width(self, starts, stops, step, width,
                                              reverse, by_date):
        """Test iteration with step and width excluding stop date.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        reverse : bool
            If True, iterate backwards.  If False, iterate forwards.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            reverse=reverse, by_date=by_date)
        self.verify_iteration(out, reverse=reverse, inclusive=False)

        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 4), dt.datetime(2009, 1, 13)], 2, 2),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 7), dt.datetime(2009, 1, 16)], 3, 1),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 6), dt.datetime(2009, 1, 15)], 2, 4)])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_season_frequency_and_width_incl(self, starts, stops, step,
                                                     width, reverse, by_date):
        """Test iteration via date season step/width > 1, include stop date.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        reverse : bool
            If True, iterate backwards.  If False, iterate forwards.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            reverse=reverse, by_date=by_date)
        self.verify_iteration(out, reverse=reverse, inclusive=True)

        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 3), dt.datetime(2009, 1, 12)], 2, 2),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 6), dt.datetime(2009, 1, 15)], 3, 1),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 7), dt.datetime(2009, 1, 16)], 2, 4)])
    @pytest.mark.parametrize("reverse", [True, False])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_season_frequency_and_width(self, starts, stops, step,
                                                width, reverse, by_date):
        """Test iteration via date season step/width>1, exclude stop date.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        reverse : bool
            If True, iterate backwards.  If False, iterate forwards.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            reverse=reverse, by_date=by_date)
        self.verify_iteration(out, reverse=reverse, inclusive=False)

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
                               'Too many input arguments.')])
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

        with pytest.raises(ValueError) as verr:
            self.testInst.bounds = new_bounds
        assert str(verr).find(errmsg) >= 0
        return

    def test_set_bounds_string_default_start(self):
        """Test set bounds with default start."""

        self.testInst.bounds = [None, '2009-01-01.nofile']
        assert self.testInst.bounds[0][0] == self.testInst.files[0]
        return

    def test_set_bounds_string_default_stop(self):
        """Test set bounds with default stop."""

        self.testInst.bounds = ['2009-01-01.nofile', None]
        assert self.testInst.bounds[1][0] == self.testInst.files[-1]
        return

    def test_set_bounds_by_default_dates(self):
        """Verify bounds behavior with default date related inputs."""

        start = self.testInst.files.start_date
        stop = self.testInst.files.stop_date
        self.testInst.bounds = (None, None)
        self.eval_iter_list(start, stop)
        self.testInst.bounds = None
        self.eval_iter_list(start, stop)
        self.testInst.bounds = (start, None)
        self.eval_iter_list(start, stop)
        self.testInst.bounds = (None, stop)
        self.eval_iter_list(start, stop)
        return

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2009, 1, 1),
                                             dt.datetime(2009, 1, 15)),
                                            ([dt.datetime(2009, 1, 1),
                                              dt.datetime(2009, 2, 1)],
                                             [dt.datetime(2009, 1, 15),
                                              dt.datetime(2009, 2, 15)])])
    def test_set_bounds_by_date(self, start, stop):
        """Test setting bounds with datetimes over simple range and season.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            The start of the new bounds.
        stop : dt.datetime or list of dt.datetime
            The stop of the new bounds.

        """

        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start, stop)
        return

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2009, 1, 15),
                                             dt.datetime(2009, 1, 1)),
                                            ([dt.datetime(2009, 1, 1),
                                              dt.datetime(2009, 2, 1)],
                                             [dt.datetime(2009, 1, 12),
                                              dt.datetime(2009, 1, 15)])])
    def test_set_bounds_by_date_wrong_order(self, start, stop):
        """Test error if bounds assignment has stop date before start.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            The start of the new bounds.
        stop : dt.datetime or list of dt.datetime
            The stop of the new bounds.

        """

        with pytest.raises(ValueError) as err:
            self.testInst.bounds = (start, stop)
        estr = 'Bounds must be set in increasing'
        assert str(err).find(estr) >= 0
        return

    @pytest.mark.parametrize(
        "start,stop", [(dt.datetime(2009, 1, 1, 1, 10),
                        dt.datetime(2009, 1, 15, 1, 10)),
                       ([dt.datetime(2009, 1, 1, 1, 10),
                         dt.datetime(2009, 2, 1, 1, 10)],
                        [dt.datetime(2009, 1, 15, 1, 10),
                         dt.datetime(2009, 2, 15, 1, 10)])])
    def test_set_bounds_by_date_extra_time(self, start, stop):
        """Test set bounds by date with extra time.

        Note
        ----
        Only the date portion is retained, hours and shorter timespans are
        dropped.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            The start of the new bounds.
        stop : dt.datetime or list of dt.datetime
            The stop of the new bounds.

        """

        self.testInst.bounds = (start, stop)
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
        self.eval_iter_list(start, stop)
        return

    @pytest.mark.parametrize("start,stop", [(dt.datetime(2010, 12, 1),
                                             dt.datetime(2010, 12, 31)),
                                            (dt.datetime(2009, 1, 1),
                                             dt.datetime(2009, 1, 15)),
                                            ([dt.datetime(2009, 1, 1),
                                              dt.datetime(2009, 2, 1)],
                                             [dt.datetime(2009, 1, 15),
                                              dt.datetime(2009, 2, 15)]),
                                            ([dt.datetime(2009, 1, 1, 1, 10),
                                              dt.datetime(2009, 2, 1, 1, 10)],
                                             [dt.datetime(2009, 1, 15, 1, 10),
                                              dt.datetime(2009, 2, 15, 1, 10)])
                                            ])
    def test_iterate_over_bounds_set_by_date(self, start, stop):
        """Test iterate over bounds via single date range.

        Parameters
        ----------
        start : dt.datetime or list of dt.datetime
            The start of the new bounds.
        stop : dt.datetime or list of dt.datetime
            The stop of the new bounds.

        """

        self.testInst.bounds = (start, stop)
        # Filter time inputs.
        start = filter_datetime_input(start)
        stop = filter_datetime_input(stop)
        self.eval_iter_list(start, stop, dates=True)
        return

    def test_iterate_over_default_bounds(self):
        """Test iterate over default bounds."""

        date_range = pds.date_range(self.ref_time,
                                    self.ref_time + dt.timedelta(days=10))
        self.testInst.kwargs['list_files']['file_date_range'] = date_range
        self.testInst.files.refresh()
        self.testInst.bounds = (None, None)
        self.eval_iter_list(date_range[0], date_range[-1], dates=True)
        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 3), dt.datetime(2009, 1, 12)], 2, 2),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 6), dt.datetime(2009, 1, 15)], 3, 1),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 7), dt.datetime(2009, 1, 16)], 2, 4)])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_over_bounds_season_step_width(self, starts, stops, step,
                                                   width, by_date):
        """Test iterate over season, step/width > 1, exclude stop bounds.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            for_loop=True, by_date=by_date)
        self.verify_iteration(out, reverse=False, inclusive=False)

        return

    @pytest.mark.parametrize(
        "starts,stops,step,width",
        [([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 4), dt.datetime(2009, 1, 13)], 2, 2),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 7), dt.datetime(2009, 1, 16)], 3, 1),
         ([dt.datetime(2009, 1, 1), dt.datetime(2009, 1, 10)],
          [dt.datetime(2009, 1, 6), dt.datetime(2009, 1, 15)], 2, 4)])
    @pytest.mark.parametrize("by_date", [True, False])
    def test_iterate_bounds_season_step_width_incl(self, starts, stops, step,
                                                   width, by_date):
        """Test iterate over season, step/width > 1, includes stop bounds.

        Parameters
        ----------
        starts : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        stops : dt.datetime or list of dt.datetime
            The start date for iterations, or dates for iteration over multiple
            segments.
        step : int
            The step size for the iteration bounds.
        width : int
            The width of the iteration bounds.
        by_date : bool
            If True, iterate by date.  If False, iterate by filename.

        """

        out = self.support_iter_evaluations(starts, stops, step, width,
                                            for_loop=True, by_date=by_date)
        self.verify_iteration(out, reverse=False, inclusive=True)

        return

    def test_set_bounds_by_fname(self):
        """Test set bounds by fname."""

        start = '2009-01-01.nofile'
        stop = '2009-01-03.nofile'
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
                          '2009-01-03.nofile'])
        return

    def test_iterate_over_bounds_set_by_fname(self):
        """Test iterate over bounds set by fname."""

        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start_d, stop_d, dates=True)
        return

    @pytest.mark.parametrize("start,stop", [('2009-01-13.nofile',
                                             '2009-01-01.nofile'),
                                            (['2009-01-01.nofile',
                                              '2009-02-03.nofile'],
                                             ['2009-01-03.nofile',
                                              '2009-02-01.nofile'])])
    def test_set_bounds_by_fname_wrong_order(self, start, stop):
        """Test for error if stop file before start file.

        Parameters
        ----------
        start : str or list of strs
            The starting filename(s) for the new bounds.
        stop : str or list of strs
            The stop filename(s) for the new bounds.

        """

        with pytest.raises(ValueError) as err:
            self.testInst.bounds = (start, stop)
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

        start = '2009-01-01.nofile'
        stop = '2009-01-15.nofile'
        start_d = dt.datetime(2009, 1, 1)
        stop_d = dt.datetime(2009, 1, 15)
        self.testInst.bounds = (start, stop)
        dates = []
        loop_next = True
        while loop_next:
            try:
                getattr(self.testInst, operator)()
                dates.append(self.testInst.date)
            except StopIteration:
                loop_next = False
        out = pds.date_range(start_d, stop_d).tolist()
        pysat.utils.testing.assert_lists_equal(dates, out)
        return

    def test_set_bounds_by_fname_season(self):
        """Test set bounds by fname season."""

        start = ['2009-01-01.nofile', '2009-02-01.nofile']
        stop = ['2009-01-03.nofile', '2009-02-03.nofile']
        self.testInst.bounds = (start, stop)
        assert np.all(self.testInst._iter_list
                      == ['2009-01-01.nofile', '2009-01-02.nofile',
                          '2009-01-03.nofile', '2009-02-01.nofile',
                          '2009-02-02.nofile', '2009-02-03.nofile'])
        return

    def test_iterate_over_bounds_set_by_fname_season(self):
        """Test set bounds using multiple filenames."""

        start = ['2009-01-01.nofile', '2009-02-01.nofile']
        stop = ['2009-01-15.nofile', '2009-02-15.nofile']
        start_d = [dt.datetime(2009, 1, 1), dt.datetime(2009, 2, 1)]
        stop_d = [dt.datetime(2009, 1, 15), dt.datetime(2009, 2, 15)]
        self.testInst.bounds = (start, stop)
        self.eval_iter_list(start_d, stop_d, dates=True)
        return

    def test_set_bounds_fname_with_frequency(self):
        """Test set bounds using filenames and non-default step."""

        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2)
        out = pds.date_range(start_date, stop_date, freq='2D').tolist()

        # Convert filenames in list to a date
        for i, item in enumerate(self.testInst._iter_list):
            snip = item.split('.')[0]
            ref_snip = out[i].strftime('%Y-%m-%d')
            assert snip == ref_snip
        return

    def test_iterate_bounds_fname_with_frequency(self):
        """Test iterate over bounds using filenames and non-default step."""

        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2)

        self.eval_iter_list(start_date, stop_date, dates=True, freq=2)
        return

    def test_set_bounds_fname_with_frequency_and_width(self):
        """Test set fname bounds with step/width > 1."""

        start = '2009-01-01.nofile'
        start_date = dt.datetime(2009, 1, 1)
        stop = '2009-01-03.nofile'
        stop_date = dt.datetime(2009, 1, 3)
        self.testInst.bounds = (start, stop, 2, 2)
        out = pds.date_range(start_date, stop_date - dt.timedelta(days=1),
                             freq='2D').tolist()
        # Convert filenames in list to a date
        date_list = []
        for item in self.testInst._iter_list:
            snip = item.split('.')[0]
            date_list.append(dt.datetime.strptime(snip, '%Y-%m-%d'))
        assert np.all(date_list == out)
        return

    def test_iteration_in_list_comprehension(self):
        """Test list comprehensions for length, uniqueness, iteration."""

        self.testInst.bounds = (self.testInst.files.files.index[0],
                                self.testInst.files.files.index[9])
        # Ensure no data to begin
        assert self.testInst.empty

        # Perform comprehension and ensure there are as many as there should be
        insts = [inst for inst in self.testInst]
        assert len(insts) == 10

        # Get list of dates
        dates = pds.Series([inst.date for inst in insts])
        assert dates.is_monotonic_increasing

        # Dates are unique
        assert np.all(np.unique(dates) == dates.values)

        # Iteration instruments are not the same as original
        for inst in insts:
            assert not (inst is self.testInst)

        # Check there is data after iteration
        assert not self.testInst.empty

        return
