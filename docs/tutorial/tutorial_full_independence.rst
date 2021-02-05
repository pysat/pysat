Iteration and Instrument Independent Analysis
---------------------------------------------

The combination of iteration and instrument independence supports
generalizing the ``daily_mean`` method introduced earlier in the tutorial
into two functions, one that averages by day, the other by orbit.
Strictly speaking, the previous daily_mean method already does this with 
the right input, as shown

.. code:: python

   mean_daily_val = daily_mean(vefi, 'dB_mer')
   mean_orbit_val = daily_mean(vefi.orbits, 'dB_mer')

However, the output of the by_orbit attempt gets rewritten for most orbits
since the output from daily_mean is stored by date. Though this could be fixed
by supplying an instrument object iterator in one case and an orbit iterator in
the other, but this would be inconsistent.  We also don't want to maintain two
code bases that do almost the same thing.

So instead, let's create three functions, two of which simply call a hidden
third.

**Iteration Independence**

.. code:: python

   def daily_mean(inst, data_label):
       """Mean of data_label by day/file over Instrument.bounds"""
       return _core_mean(inst, data_label, by_day=True)

   def by_orbit_mean(inst, data_label):
       """Mean of data_label by orbit over Instrument.bounds"""
       return _core_mean(inst, data_label, by_orbit=True)

   def _core_mean(inst, data_label, by_orbit=False, by_day=False):

       if by_orbit:
           iterator = inst.orbits
       elif by_day:
           iterator = inst
       else:
           raise ValueError('A choice must be made, by day/file, or by orbit')
       if by_orbit and by_day:
           raise ValueError('A choice must be made, by day/file, or by orbit')

       # create empty series to hold result
       mean_val = pandas.Series()
       # iterate over season, calculate the mean
       for inst in iterator:
           if not inst.empty:
               # compute mean absolute using pandas functions and store
               # data could be an image, or lower dimension,
               # account for 2D and lower
               data = inst[data_label]
               data.dropna(inplace=True)

               if by_orbit:
                   date = inst.data.index[0]
               else:
                   date = inst.date

               data = pysat.ssnl.computational_form(data)
               mean_val[date] = data.abs().mean(axis=0, skipna=True)

       del iterator
       return mean_val

The addition of a few more lines to the daily_mean function could add support 
for averages by orbit, or by day, for any platform with data 3D or less. The 
date issue and the type of iteration are solved with simple if else checks. 
The code doesn't really deviate from the first solution of simply passing in 
vefi.orbits except for the fact that the .orbits switch is 'hidden' in the 
code. NaN values are also dropped from the data. If the first element is a NaN,
it isn't handled by the simple instance check.

A name change and a couple more dummy functions would separate out the orbit vs
daily iteration clearly, without having multiple codebases. Iteration by file
and by date are handled by the same Instrument iterator and controlled by the
settings in Instrument.bounds. A by_file_mean was not created because bounds
could be set by date and then by_file_mean applied. Of course this could set
up to produce an error. However, the settings on Instrument.bounds controls
the iteration type between files and dates, so we maintain this view with the
expressed calls. Similarly, the orbit iteration is a separate iterator, with a
separate call. This technique above is used by other seasonal analysis routines
in pysat.

You may notice that the mean call could also easily be replaced by a median, or
even a mode. We might also want to return the standard deviation, or appropriate
measure. Perhaps another level of generalization is needed?
