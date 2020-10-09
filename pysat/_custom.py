import numpy as np
import pandas as pds
import xarray as xr

from pysat import logger


class Custom(object):
    """ Applies a queue of functions when instrument.load called.

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
        instrument.custom.attach(custom_func, 'modify', opt_param1=True)

        def custom_func2(inst, opt_param1=False, opt_param2=False):
            return data_to_be_added
        instrument.custom.attach(custom_func2, 'add', opt_param2=True)
        instrument.load(date=date)
        print(instrument['data_to_be_added'])

    See Also
    --------
    Custom.attach

    Note
    ----
    User should interact with Custom through `pysat.Instrument` instance's
    attribute, `instrument.custom`

    """

    def __init__(self):
        # create hidden lists to store custom functions, their return type,
        # argument input, and keyword argument input
        self._functions = []
        self._kind = []
        self._args = []
        self._kwargs = []

    def __repr__(self):
        out_str = "Custom -> {:d} functions applied".format(
            len(self._functions))
        return out_str

    def __str__(self):
        num_funcs = len(self._functions)
        out_str = "Custom Functions: {:d} applied\n".format(num_funcs)
        if num_funcs > 0:
            for i, func in enumerate(self._functions):
                out_str += "    {:d}: {:}\n".format(i, func.__repr__())
                if len(self._args[i]) > 0:
                    out_str += "     : Args={:}\n".format(self._args[i])
                if len(self._kwargs[i]) > 0:
                    out_str += "     : Kwargs={:}\n".format(self._kwargs[i])

        return out_str

    def attach(self, function, kind='modify', at_pos='end', args=[],
               kwargs={}):
        """Attach a function to custom processing queue.

        Custom functions are applied automatically to associated
        pysat instrument whenever instrument.load command called.

        Parameters
        ----------
        function : string or function object
            name of function or function object to be added to queue
        kind : {'add', 'modify', 'pass}
            - add
                Adds data returned from function to instrument object.
                A copy of pysat instrument object supplied to routine.
            - modify
                pysat instrument object supplied to routine. Any and all
                changes to object are retained.
            - pass
                A copy of pysat object is passed to function. No
                data is accepted from return.
            (default='modify')

        at_pos : string or int
            Accepts string 'end' or a number that will be used to determine
            the insertion order if multiple custom functions are attached
            to an Instrument object. (default='end').
        args : list or tuple
            Ordered arguments following the instrument object input that are
            required by the custom function (default=[])
        kwargs : dict
            Dictionary of keyword arguements required by the custom function
            (default={})

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

        # Test the positioning input
        pos_list = list(np.arange(0, len(self._functions), 1))
        pos_list.append('end')

        if at_pos not in pos_list:
            logger.warning(''.join(['unknown position specified, including ',
                                    'function at end of current list']))
            at_pos = 'end'

        # Convert string to function object, if necessary
        if isinstance(function, str):
            function = eval(function)

        # If the position is 'end' or greater
        if (at_pos == 'end') | (at_pos == len(self._functions)):
            # store function object
            self._functions.append(function)
            self._args.append(args)
            self._kwargs.append(kwargs)
            self._kind.append(kind.lower())
        else:
            # user picked a specific location to insert
            self._functions.insert(at_pos, function)
            self._args.insert(at_pos, args)
            self._kwargs.insert(at_pos, kwargs)
            self._kind.insert(at_pos, kind)

    def _apply_all(self, sat):
        """
        Apply all of the custom functions to the satellite data object.

        Parameters
        ----------
        sat : pysat.Instrument
            Instrument object

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
                                # Look if name is provided as part of dict
                                # returned from function first
                                if 'name' in newData.keys():
                                    name = newData.pop('name')
                                    sat[name] = newData
                                # look for name attached to Series second
                                elif newData['data'].name is not None:
                                    sat[newData['data'].name] = newData
                                # couldn't find name information
                                else:
                                    raise ValueError(
                                        ''.join(['Must assign a name to ',
                                                 'Series or return a ',
                                                 '"name" in dictionary.']))
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
                                if isinstance(newName, str):
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
