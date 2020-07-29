from __future__ import print_function
from __future__ import absolute_import
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str
import warnings

import pandas as pds
import xarray as xr


class Custom(object):
    """
    Applies a queue of functions when instrument.load called.

    Nano-kernel functionality enables instrument objects that are
    'set and forget'. The functions are always run whenever
    the instrument load routine is called so instrument objects may
    be passed safely to other routines and the data will always
    be processed appropriately.

    Examples
    --------
    ::

        def custom_func(inst, opt_param1=False, opt_param2=False):
            return None
        instrument.custom.add(custom_func, 'modify', opt_param1=True)

        def custom_func2(inst, opt_param1=False, opt_param2=False):
            return data_to_be_added
        instrument.custom.add(custom_func2, 'add', opt_param2=True)
        instrument.load(date=date)
        print(instrument['data_to_be_added'])

    See Also
    --------
    Custom.add

    Note
    ----
    User should interact with Custom through pysat.Instrument instance's
    attribute, instrument.custom
    """

    def __init__(self):
        # create a list object to store functions
        self._functions = []
        # type of function stored (add/modify/pass on data)
        self._kind = []
        # arguments to functions
        self._args = []
        # keyword arguments to functions
        self._kwargs = []

    def add(self, function, kind='add', at_pos='end', *args, **kwargs):
        """Add a function to custom processing queue.

        .. deprecated:: 2.2.0
          `add` will be removed in pysat 3.0.0, it is replaced by
          `attach` to clarify the syntax

        Custom functions are applied automatically to associated
        pysat instrument whenever instrument.load command called.

        Parameters
        ----------
            function : string or function object
                name of function or function object to be added to queue

            kind : {'add', 'modify', 'pass}
                add
                    Adds data returned from function to instrument object.
                    A copy of pysat instrument object supplied to routine.
                modify
                    pysat instrument object supplied to routine. Any and all
                    changes to object are retained.
                pass
                    A copy of pysat object is passed to function. No
                    data is accepted from return.

            at_pos : string or int
                insert at position. (default, insert at end).
            args : extra arguments
                extra arguments are passed to the custom function (once)
            kwargs : extra keyword arguments
                extra keyword args are passed to the custom function (once)

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

        warnings.warn(' '.join(["custom.add is deprecated and will be",
                                "renamed in pysat 3.0.0 as custom.attach"]),
                      DeprecationWarning, stacklevel=2)
        self.attach(function, kind=kind, at_pos=at_pos, *args, **kwargs)
        return

    def attach(self, function, kind='add', at_pos='end', *args, **kwargs):
        """Attach a function to custom processing queue.

        Custom functions are applied automatically to associated
        pysat instrument whenever instrument.load command called.

        Parameters
        ----------
        function : string or function object
            name of function or function object to be added to queue

        kind : {'add', 'modify', 'pass}
            add
                Adds data returned from function to instrument object.
                A copy of pysat instrument object supplied to routine.
            modify
                pysat instrument object supplied to routine. Any and all
                changes to object are retained.
            pass
                A copy of pysat object is passed to function. No
                data is accepted from return.

        at_pos : string or int
            insert at position. (default, insert at end).
        args : extra arguments
            extra arguments are passed to the custom function (once)
        kwargs : extra keyword arguments
            extra keyword args are passed to the custom function (once)

        Note
        ----
        Allowed `attach` function returns:

        - {'data' : pandas Series/DataFrame/array_like,
          'units' : string/array_like of strings,
          'long_name' : string/array_like of strings,
          'name' : string/array_like of strings (iff data array_like)}

        - pandas DataFrame, names of columns are used

        - pandas Series, .name required

        - (string/list of strings, numpy array/list of arrays)
        """

        if isinstance(function, str):
            # convert string to function object
            function = eval(function)

        if (at_pos == 'end') | (at_pos == len(self._functions)):
            # store function object
            self._functions.append(function)
            self._args.append(args)
            self._kwargs.append(kwargs)
            self._kind.append(kind.lower())
        elif at_pos < len(self._functions):
            # user picked a specific location to insert
            self._functions.insert(at_pos, function)
            self._args.insert(at_pos, args)
            self._kwargs.insert(at_pos, kwargs)
            self._kind.insert(at_pos, kind)
        else:
            raise TypeError('Must enter an index between 0 and %i' %
                            len(self._functions))

    def _apply_all(self, sat):
        """
        Apply all of the custom functions to the satellite data object.
        """
        if len(self._functions) > 0:
            for func, arg, kwarg, kind in zip(self._functions, self._args,
                                              self._kwargs, self._kind):
                if not sat.empty:
                    if kind == 'add':
                        # apply custom functions that add data to the
                        # instrument object
                        tempd = sat.copy()
                        newData = func(tempd, *arg, **kwarg)
                        del tempd

                        # process different types of data returned by the
                        # function if a dict is returned, data in 'data'
                        if isinstance(newData, dict):
                            # if DataFrame returned, add Frame to existing
                            # frame
                            if isinstance(newData['data'], pds.DataFrame):
                                sat[newData['data'].columns] = newData
                            # if a series is returned, add it as a column
                            elif isinstance(newData['data'], pds.Series):
                                # look for name attached to series first
                                if newData['data'].name is not None:
                                    sat[newData['data'].name] = newData
                                # look if name is provided as part of dict
                                # returned from function
                                elif 'name' in newData.keys():
                                    name = newData.pop('name')
                                    sat[name] = newData
                                # couldn't find name information
                                else:
                                    raise ValueError('Must assign a name to ' +
                                                     'Series or return a ' +
                                                     '"name" in dictionary.')
                            # xarray returned
                            elif isinstance(newData['data'], xr.DataArray):
                                sat[newData['data'].name] = newData['data']

                            # some kind of iterable was returned
                            elif hasattr(newData['data'], '__iter__'):
                                # look for name in returned dict
                                if 'name' in newData.keys():
                                    name = newData.pop('name')
                                    sat[name] = newData
                                else:
                                    raise ValueError(''.join(('Must include ',
                                                              '"name" in ',
                                                              'returned ',
                                                              'dictionary.')))

                        # bare DataFrame is returned
                        elif isinstance(newData, pds.DataFrame):
                            sat[newData.columns] = newData
                        # bare Series is returned, name must be attached to
                        # Series
                        elif isinstance(newData, pds.Series):
                            sat[newData.name] = newData

                        # xarray returned
                        elif isinstance(newData, xr.DataArray):
                            sat[newData.name] = newData

                        # some kind of iterable returned,
                        # presuming (name, data)
                        # or ([name1,...], [data1,...])
                        elif hasattr(newData, '__iter__'):
                            # falling back to older behavior
                            # unpack tuple/list that was returned
                            newName = newData[0]
                            newData = newData[1]
                            if len(newData) > 0:
                                # doesn't really check ensure data, there could
                                # be multiple empty arrays returned, [[],[]]
                                if isinstance(newName, basestring):
                                    # one item to add
                                    sat[newName] = newData
                                else:
                                    # multiple items
                                    for name, data in zip(newName, newData):
                                        if len(data) > 0:
                                            # fixes up the incomplete check
                                            # from before
                                            sat[name] = data
                        else:
                            raise ValueError(''.join(("kernel doesn't know",
                                                      " what to do with",
                                                      " returned data.")))

                    # modifying loaded data
                    if kind == 'modify':
                        t = func(sat, *arg, **kwarg)
                        if t is not None:
                            raise ValueError(''.join(('Modified functions',
                                                      ' should not return',
                                                      ' any information via',
                                                      ' return. Information ',
                                                      'may only be propagated',
                                                      ' back by modifying ',
                                                      'supplied pysat object.'
                                                      )))

                    # pass function (function runs, no data allowed back)
                    if kind == 'pass':
                        tempd = sat.copy()
                        t = func(tempd, *arg, **kwarg)
                        del tempd
                        if t is not None:
                            raise ValueError(''.join(('Pass functions should',
                                                      ' not return any ',
                                                      'information via ',
                                                      'return.')))

    def clear(self):
        """Clear custom function list."""
        self._functions = []
        self._args = []
        self._kwargs = []
        self._kind = []

#################################################
# END CUSTOM CLASS ##############################
#################################################
