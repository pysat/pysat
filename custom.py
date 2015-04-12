import pandas as pds

class custom(object):
    """
    Class holds a list of functions and arguments to be applied when load called.
    """

    #initialize
    def __init__(self):
        #create a list object to store functions
        self._functions = []
        #type of function stored (add/modify/pass on data)
        self._kind = []
        #arguments to functions
        self._args = []
        #keyword arguments to functions
        self._kwargs = []

    #add a funtion to the list
    def add(self, function, kind='add', at_pos='end',*args, **kwargs):
        """ Add a function to custom processing queue. 
        
        Custom functions are applied automatically to associated
        pysat instrument whenever instrument.load command called.

        Inputs:
            function - name of function or function object
            
            kind - type of custom function
                add : Adds data returned from function to instrument object. 
                      A copy of pysat instrument object supplied to routine. 
                      Allowed returns:
                          {'data':pandas Series/DataFrame, 'units':string/list 
                                of strings, 'long_name':string/list of strings}
                          pandas DataFrame, names of columns used
                          pandas Series, series name required
                          (string/list of strings, numpy array/list of arrays)
                modify : pysat instrument object supplied to routine. Any and all
                         changes to object are retained.
                pass : A copy of pysat object is passed to function. No 
                       data is accepted from return.
                       
            at_pos - insert at position. (default, insert at end).                      
        """

        #if function is a string, execute string to get function object
        if isinstance(function, str):
            #convert string to function object
            function=eval(function)

        if (at_pos == 'end') | (at_pos == len(self._functions)):
            #store function object
            self._functions.append(function)
            self._args.append(args)
            self._kwargs.append(kwargs)
            self._kind.append(kind.lower())
        elif at_pos < len(self._functions):
            #user picked a specific location to insert
            self._functions.insert(at_pos, function)
            self._args.insert(at_pos, args)
            self._kwargs.insert(at_pos, kwargs)
            self._kind.insert(at_pos, kind)
        else:
            raise TypeError('Must enter an index between 0 and %i' % len(self._functions))

    def _apply_all(self, sat):
        '''Apply all of the custom functions to the satellite data object.
        '''
        if len(self._functions) > 0:
            for func, arg, kwarg, kind in zip(self._functions, self._args, self._kwargs, self._kind):
                if len(sat.data) > 0:     #ensure there is data
                    #print 'there is data to operate custom functions on'
                    if kind == 'add':
                        #apply custom function that adds data to the instrument object
                        tempd = sat.copy()
                        newData = func(tempd, *arg, **kwarg)
                        del tempd
                        
                        # not fancy below, but it works
                        if isinstance(newData,dict):
                            if isinstance(newData['data'], pds.DataFrame):
                                sat[newData['data'].columns] = newData
                            elif isinstance(newData['data'], pds.Series):
                                sat[newData['data'].name] = newData
                        elif isinstance(newData, pds.DataFrame):
                            sat[newData.columns] = newData
                        elif isinstance(newData, pds.Series):
                            sat[newData.name] = newData
                        elif hasattr(newData, '__iter__'):
#
#                        
#                        try:
#                            #sat.data = sat.data.join(newData)
#                            sat[newData.columns] = newData
#                            # this doesn't really work
#                            #print 'Added Data'
#                        except AttributeError:
			    # falling back to older behavior if not a DataFrame
			    # unpack tuple/list that was returned instead of DF
                            newName = newData[0]
                            newData = newData[1]

                            if len(newData)>0:
                                # doesn't really check ensure data, there could
                                # be multiple empty arrays returned, [[],[]]
                                if isinstance(newName, str):
                                    # one item to add
                                    #type(newName)==str:   
                                    sat[newName] = newData
                                else:    		
                                    # multiple items
                                    for name, data in zip(newName, newData):
                                        if len(data)>0:        
                                            # fix up the incomplete check from before
                                            sat[name] = data
                    # modifying loaded data
                    if kind == 'modify':
                        t = func(sat,*arg,**kwarg)
			if t is not None:
			    raise ValueError('Modify functions should not return any information via return. Information may only be propagated back by modifying supplied pysat object.')	
                    	#print 'Modified Data using ', func, ' upon ', sat
                    # pass function (function runs, no data allowed back)
                    if kind == 'pass':
                        tempd = sat.copy()
                        t = func(tempd,*arg,**kwarg)
                        del tempd
			if t is not None:
			    raise ValueError('Pass functions should not return any information via return.')	
                        print 'Passed Data'

    def clear(self):
        """Clear custom function list."""
        self._functions=[]
        self._args=[]
        self._kwargs=[]
        self._kind=[]

######################################################
##### END CUSTOM CLASS ##############################
####################################################
