import numpy as np
import pandas as pds
from pysat import Series, DataFrame

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
    kind : {'local time', 'longitude', 'polar'}
        kind of orbit, determines how orbital breaks are determined
        
        - local time: negative gradients in lt or breaks in inst.data.index
        - longitude: negative gradients or breaks in inst.data.index
        - polar: zero crossings in latitude or breaks in inst.data.index
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
            print 'Next available orbit ', vefi['dB_mer']
                            
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
        #create null arrays for storing orbit info
        if sat is None:
            raise ValueError('Must provide a pysat instrument object when initializing '+ 
                                'orbits class.')
        else:
            #self.sat = weakref.proxy(sat)
            self.sat = sat
            
        if kind is None:
            kind = 'local time'
        else:
            kind = kind.lower()
        
        if period is None:
            period = np.timedelta64(97, 'm')
        self.orbit_period = period

        if (kind == 'local time') or (kind == 'lt'):
            self._detBreaks = self._equaBreaks
        elif (kind == 'longitude') or (kind == 'long'):
            self._detBreaks = self._longBreaks
        elif kind == 'polar':
            self._detBreaks = self._polarBreaks
        else:
            raise ValueError('Unknown kind of orbit requested.')
       
        self._orbit_breaks = []
        self.num = []
        self.current = 0
        self.orbit_index = index

            
    def __getitem__(self, key): 
        """Enable convenience notation for loading orbit into parent object.
        
        Examples
        --------
        ::
        
            inst.load(date=date)
            inst.orbits[4]
            print 'Orbit data ', inst.data
        
        Note
        ----
        A day of data must already be loaded.
            
        """
        
        self.load(key)

    def _reset(self):
        #create null arrays for storing orbit info
        self._orbit_breaks = []
        self.num = None
        self.current = 0

    def _calcOrbits(self):
        """Prepares data structure for breaking data into orbits. Not intended for end user."""
        #if the breaks between orbit have not been defined, define them
        #also, store the data so that grabbing different orbits does not
        #require reloads of whole dataset
        if self._orbit_breaks == []:
                #determine orbit breaks
                self._detBreaks()
                #store a copy of data
                self._fullDayData = self.sat.data.copy()
                #set current orbit counter to zero (default)
                self.current = 0

    def _equaBreaks(self):
        """Determine where breaks in an equatorial satellite orbit occur.
        
        Looks for negative gradients in local time (or longitude) as well as 
        breaks in UT.

	"""
     
        if self.orbit_index is None:
            try:
    	        self.sat['slt']
		self.orbit_index = 'slt'
            except ValueError:
                try:
                    self.sat['mlt']
                    self.orbit_index = 'mlt'
                except ValueError:
                    try:
                        self.sat['glong']
			self.orbit_index = 'glong'
                    except ValueError:
                        raise ValueError('Unable to find a valid index (slt/mlt/glong) for determining orbits.')
        else:
            try:
                self.sat[self.orbit_index]
            except ValueError:
                raise ValueError('Provided orbit index does not exist in loaded data')

        #define derivative function here
        #deriv = lambda x: (x[1] - x[0])/2
        lt_diff = self.sat[self.orbit_index].diff()
        ut_vals = Series(self.sat.data.index)
        ut_diff = ut_vals.diff()
        #locations where derivative is less than 0
        #or, look for breaks because the length of time between samples is too large
        #deriv of datetime index is in naneseconds
        ind, = np.where((lt_diff < -0.1) )
        if len(ind) > 0:
            ind = np.hstack((ind, np.array([ len(self.sat[self.orbit_index]) ]) ))
            #look at distance between breaks
            dist = ind[1:] - ind[0:-1]
            #only keep orbit breaks with a distance greater than 1
            #done for robustness
            if len(ind) > 1:
                if min(dist)==1:
                    print 'There are orbit breaks right next to each other'
                ind = ind[dist>1]
                
            #check for large positive gradients around the break that would
            #suggest not a true orbit break, but rather bad orbit_index values
            new_ind = []
            for idx in ind:
                tidx, = np.where(lt_diff[idx-5:idx+6] > 0.1)

		if len(tidx) != 0:
  		    for tidx in tidx:
      		        #look at time change vs local time change
      		        if ut_diff[idx-5:idx+6].iloc[tidx] < lt_diff[idx-5:idx+6].iloc[tidx]/24.*self.orbit_period :
      		            #change in ut inconsistent with change in local time
      		            #increases in local time require a change in ut	
      		            pass
      		        #print 'Fake Orbit Break.'
      		        else:
      		            new_ind.append(idx)	
      		            break    
		else:
		    new_ind.append(idx)

	    ind = np.array(new_ind)
	    
	    
	    #while this works correctly, when it works correctly it doesn't give
	    #what I need
            ##look at the time change vs lt change for the negative gradients
            #new_ind = []
            #for idx in ind:
            #    diff = lt_diff.iloc[idx]
            #    print 'Checking negative gradient for validity at UT', self.sat.data.index[idx]
            #    print 'MLT values around break ', self.sat[self.orbit_index][idx-3:idx+4]
            #    print 'UT Diff ', ut_diff.iloc[idx]
            #    print 'LT Diff ', diff
            #    print 'Equivalent UT Drift ', np.abs(1. + diff/24.)*self.orbit_period
            #    if ut_diff.iloc[idx] < np.abs(1. + diff/24.)*self.orbit_period:
            #        #for almost 24 hours of local time change, there should be no
            #        # time change (<= 1 second)
            #        print "Negative gradient in MLT doesn't have corresponding UT change"
            #        print "Not a true orbit break (likely)"
            #        pass
            #    else:
            #        new_ind.append(idx)  
            #ind = new_ind        

        
        ##now, look for breaks because the length of time between samples is too large, thus there is no break in slt/mlt/etc
        #ut_val = pds.rolling_apply(self.sat.data.index.values,2,deriv)
        #ut_val has time differences in nanseconds, so orbit_period expressed in nano here
        ut_ind, = np.where((ut_diff > self.orbit_period) | ((ut_diff/self.orbit_period > (np.abs(lt_diff/24.)) ) & (ut_diff/self.orbit_period > 0.95) ))#  & lt_diff.notnull() ))# & (lt_diff != 0)  ) )   #added the or and check after or on 10/20/2014
        if len(ut_ind) > 0:
            #print len(ut_ind), len(ut_diff)
            ind = np.hstack((ind,ut_ind))
            ind = np.sort(ind)
            ind = np.unique(ind)
            print 'Time Gap'
            #print ut_diff[1]/self.orbit_period*24., lt_diff[1], ut_diff[1], 0.97*self.orbit_period
            #print ut_diff.iloc[ut_ind], lt_diff.iloc[ut_ind], np.abs(lt_diff.iloc[ut_ind]/24.), ut_diff[ut_ind]/self.orbit_period
            #print np.abs(lt_diff.iloc[ut_ind]/24.*self.orbit_period)

	#now that most problems in orbits should have been caught, look at 
	#the time difference between orbits
	orbit_ut_diff = ut_vals[ind].diff()
	orbit_lt_diff = self.sat[self.orbit_index][ind].diff()
	#print 'Differences in orbit time before last filter'
	#print ut_vals[ind]
	#print orbit_ut_diff
	#print orbit_lt_diff
	#
	#print 'Scaled Time Difference'
	#print orbit_ut_diff - orbit_lt_diff.values/24.*self.orbit_period
	idx, = np.where((orbit_ut_diff/self.orbit_period - orbit_lt_diff.values/24.) > 0.97)
	idx = np.hstack((0,idx))
	if len(ind) > 0:
	    ind = ind[idx]
	#print 'Differences in orbit time after last filter'
	#print ut_vals[ind].diff()


        # number of orbits
        num_orbits = len(ind)+1
        # create orbitbreak index
        ind=np.hstack((np.array([0]),ind))
        # set index of orbit breaks
        self._orbit_breaks = ind
        # set number of orbits for the day
        self.num = num_orbits


    def _longBreaks(self):
        """
        Determine where breaks in a satellite orbit occur, based upon
        changes in longitude.
        
        Looks for negative gradients in longitude as well as 
        breaks in UT.

	"""
     
        if self.orbit_index is None:
            try:
                self.sat['glong']
		self.orbit_index = 'glong'
            except ValueError:
                raise ValueError(''.join(('Unable to find a valid index',
                    'for determining orbits. Provide one in orbit_index')))
        else:
            try:
                self.sat[self.orbit_index]
            except ValueError:
                raise ValueError('Provided orbit index does not exist in loaded data')

        lt_diff = self.sat[self.orbit_index].diff()
        ut_vals = Series(self.sat.data.index)
        ut_diff = ut_vals.diff()
        # locations where derivative is less than 0
        # or, look for breaks because the length of time between samples is too large
        # deriv of datetime index is in naneseconds
        ind, = np.where((lt_diff < -0.1) )
        if len(ind) > 0:
            ind = np.hstack((ind, np.array([ len(self.sat[self.orbit_index]) ]) ))
            # look at distance between breaks
            dist = ind[1:] - ind[0:-1]
            # only keep orbit breaks with a distance greater than 1
            # done for robustness, though this could rarely introduce a problem
            if len(ind) > 1:
                if min(dist)==1:
                    print 'There are orbit breaks right next to each other'
                ind = ind[dist>1]
                
            # check for large positive gradients around the break that would
            # suggest not a true orbit break, but rather bad orbit_index values
            new_ind = []
            for idx in ind:
                tidx, = np.where(lt_diff[idx-5:idx+6] > 0.1)

		if len(tidx) != 0:
  		    for tidx in tidx:
      		        # look at time change vs longitude change
      		        if ut_diff[idx-5:idx+6].iloc[tidx] < lt_diff[idx-5:idx+6].iloc[tidx]/360.*self.orbit_period :
      		            # change in ut inconsistent with change in local time
      		            # increases in longitude require a change in ut	
      		            pass
      		        #print 'Fake Orbit Break.'
      		        else:
      		            new_ind.append(idx)	
      		            break    
		else:
		    new_ind.append(idx)

	    ind = np.array(new_ind)
	    
        
        # now, look for breaks because the length of time between samples is too large, thus there is no break in slt/mlt/etc
        ut_ind, = np.where(
                        (ut_diff > self.orbit_period) | 
                        ( (ut_diff/self.orbit_period > (np.abs(lt_diff/360.))) & 
                        (ut_diff/self.orbit_period > 0.95) )
                        )
                    #  & lt_diff.notnull() ))# & (lt_diff != 0)  ) )   #added the or and check after or on 10/20/2014
        
        if len(ut_ind) > 0:
            ind = np.hstack((ind,ut_ind))
            ind = np.sort(ind)
            ind = np.unique(ind)
            print 'Time Gap'

	# now that most problems in orbits should have been caught, look at 
	# the time difference between orbits
	orbit_ut_diff = ut_vals[ind].diff()
	orbit_lt_diff = self.sat[self.orbit_index][ind].diff()

	idx, = np.where((orbit_ut_diff/self.orbit_period - orbit_lt_diff.values/360.) > 0.97)
	idx = np.hstack((0,idx))
	if len(ind) > 0:
	    ind = ind[idx]

        # number of orbits
        num_orbits = len(ind)+1
        # create orbitbreak index
        ind=np.hstack((np.array([0]),ind))
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
              'pysat.Instrument object instantiation. See Instrument docs.')
        else:
            try:
                self.sat[self.orbit_index]
            except ValueError:
                raise ValueError('Provided orbit index does not appear to exist in loaded data')

        # determine where orbit index goes from positive to negative
        pos = self.sat[self.orbit_index] >= 0
        npos = -pos 
        change = (pos.values[:-1] & npos.values[1:]) | (npos.values[:-1] & pos.values[1:])

        ind, = np.where(change)
        ind += 1
        if len(ind) > 0:
            ind = np.hstack((ind, np.array([ len(self.sat[self.orbit_index]) ]) ))
            # look at distance between breaks
            dist = ind[1:] - ind[0:-1]
            # only keep orbit breaks with a distance greater than 1
            # done for robustness
            if len(ind) > 1:
                if min(dist)==1:
                    print 'There are orbit breaks right next to each other'
                ind = ind[dist>1]

        ut_diff = Series(self.sat.data.index).diff()
        ut_ind, = np.where( ut_diff/self.orbit_period > 0.95 )
        
        
        if len(ut_ind) > 0:
            ind = np.hstack((ind,ut_ind))
            ind = np.sort(ind)
            ind = np.unique(ind)
            #print 'Time Gap'
        # number of orbits
        num_orbits = len(ind)+1
        # create orbitbreak index
        ind=np.hstack((np.array([0]),ind))
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
        #ensure data exists
        if len(self.sat.data) > 0:
            #ensure proper orbit metadata present
            self._calcOrbits()

            #ensure user is requesting a particular orbit
            if orbit is not None:
                #pull out requested orbit
                if orbit == -1:
                    #load orbit data into data
                    self.sat.data = self._fullDayData[self._orbit_breaks[self.num+orbit]:]
                    self.current = self.num+orbit+1
                elif ((orbit < 0) & (orbit >= -self.num)):
                    #load orbit data into data
                    self.sat.data = self._fullDayData[self._orbit_breaks[self.num+orbit]:self._orbit_breaks[self.num+orbit+1]]
                    self.current = self.num+orbit+1                    
                elif (orbit < self.num) & (orbit != 0):
                    #load orbit data into data
                    self.sat.data = self._fullDayData[self._orbit_breaks[orbit-1]:self._orbit_breaks[orbit]]
                    self.current = orbit
                elif orbit==self.num:
                    self.sat.data = self._fullDayData[self._orbit_breaks[orbit-1]:]
                    self.current = orbit #recent addition, wondering why it wasn't there before, could just be a bug
                elif orbit == 0:
		    raise ValueError('Orbits start at 1, 0 not allowed')	
                else:
                    #gone too far
                    self.sat.data = []
                    raise ValueError('Requested an orbit past total orbits for day')
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
        if len(self.sat.data) > 0: #ensure data exists
            #set up orbit metadata
            self._calcOrbits()
            #ensure user supplied an orbit
            if orbit is not None:
                #pull out requested orbit
                if orbit < 0:
                    #negative indexing consistent with numpy, -1 last, -2 second
                    # to last, etc.
                    orbit = self.num+1+orbit

                if orbit == 1:
                    #change from orig copied from _core, didn't look correct.
      #              self._getBasicOrbit(orbit=2)
		    #self.prev()	
		    try:
			true_date = self.sat.date#.copy()

      		        self.sat.prev()
      		        #if and else added becuase of CINDI turn off 6/5/2013,turn on 10/22/2014
      		        #crashed when starting on 10/22/2014
      		        #prev returned empty data
      		    	if len(self.sat.data) >0:
      		    	    self.load(orbit=-1) 
      		    	else:
      		    	    self.sat.next()
      		    	    self._getBasicOrbit(orbit=1)
                        #check that this orbit should end on the current day
                        delta = pds.to_timedelta(true_date-self.sat.data.index[0])
                        #print 'checking if first orbit should land on requested day'
                        #print self.sat.date, self.sat.data.index[0], delta, delta >= self.orbit_period
                        #print delta - self.orbit_period
                        if delta >= self.orbit_period:
                            #the orbit loaded isn't close enough to date
                            #to be the first orbit of the day, move forward
                            self.next()
		    except StopIteration:
		        #print 'going for basic orbit'
		        self._getBasicOrbit(orbit=1)
		        print 'Loaded Orbit:%i' % self.current
                    #check if the first orbit is also the last orbit
                    
                elif orbit==self.num:
                    #we get here if user asks for last orbit
                    #make sure that orbit data goes across daybreak as needed
                    #load previous orbit
                    if self.num != 1:
                        self._getBasicOrbit(self.num-1)
                        self.next()
                    else:
                        #self.current = 1
                        self._getBasicOrbit(orbit=-1)
                    #request next orbit, this will go across day break nicely
                    #self.next()

                elif orbit < self.num:
                    #load orbit data into data
                    self._getBasicOrbit(orbit)
                    print 'Loaded Orbit:%i' % self.current

                else:
                    #gone too far
                    self.sat.data = []
                    raise Exception('Requested an orbit past total orbits for day')
            else:
                raise Exception('Must set an orbit')
        else:
            print 'No data loaded in instrument object to determine orbits.'
            
    def next(self, *arg, **kwarg):
        """Load the next orbit into .data.

        Note
        ----
        Forms complete orbits across day boundaries. If no data loaded
        then the first orbit from the first date of data is returned.
            
        """

        #first, check if data exists
        if len(self.sat.data) > 0:
            #set up orbit metadata
            self._calcOrbits()

             #if current orbit near the last, must be careful
            if self.current == (self.num - 1 ):
                #first, load last orbit data
                self._getBasicOrbit(orbit=-1)
                #should come up with some kind of check if the next day is needed
                load_next = True
                if self.sat._iter_type == 'date':
                    delta = pds.to_timedelta(self.sat.date - self.sat.data.index[-1]) + np.timedelta64(1, 'D') 
                    #print 'Checking if new load needed ', delta < self.orbit_period
                    if delta > self.orbit_period:
                        #don't need to load the next day
                        #everything is already done
                        #print 'Not loading next day to give last orbit'
                        load_next = False
                #need to save this current orbit and load the next day
                if load_next:
                    temp_orbit_data = self.sat.data.copy() 
                    try:
                        # loading next day/file clears orbit breaks info
                        self.sat.next()
   	                # combine this next day orbit with previous last orbit
                        if len(self.sat.data) > 0:
                            self.sat.data = pds.concat([temp_orbit_data[:self.sat.data.index[0] - pds.DateOffset(microseconds=1)], self.sat.data])
                            self._getBasicOrbit(orbit=1)
                        else:
                            self.sat.prev() 
                            self._getBasicOrbit(orbit=-1)
                    except StopIteration:
                        pass
                    del temp_orbit_data
                print 'Loaded Orbit:%i' % self.current  

            elif self.current == (self.num):
                #self._getBasicOrbit(orbit=-1)
                #need to save this current orbit and load the next day
                temp_orbit_data = self.sat.data.copy() 
                #load next day, which clears orbit breaks info
                self.sat.next() 
                #combine this next day orbit with previous last orbit
                if len(self.sat.data) > 0:
                    #check if data padding is really needed, only works when loading by date
                    pad_next = True
                    if self.sat._iter_type == 'date':
                        delta = pds.to_timedelta(self.sat.date-temp_orbit_data.index[-1])
                        #print 'Checking if new load was needed ', (delta < self.orbit_period)
                        if delta > self.orbit_period:
                            #don't need to load the next day
                            pad_next = False                    
                    if pad_next:
                        self.sat.data = pds.concat([temp_orbit_data[:self.sat.data.index[0] - pds.DateOffset(microseconds=1)], self.sat.data])
                        #select second orbit of combined data
                        self._getBasicOrbit(orbit=2)
		    else:
		        self._getBasicOrbit(orbit=1)
                        if self.sat._iter_type == 'date':
                            delta = pds.to_timedelta(self.sat.date + pds.DateOffset(days=1)-self.sat.data.index[0])
                            #print 'Checking if another new load is needed ', delta < self.orbit_period
 			    if delta < self.orbit_period:
 			        #first orbit is also last orbit which spans to next day
  		                self.current = self.num - 1
  		                self.next()		            

                else:
                    #continue loading data until there is some
                    #nextData raises StopIteration when it reaches the end
                    while len(self.sat.data) == 0:
                        self.sat.next()
                    self._getBasicOrbit(orbit=1)

                #print 'Loaded Orbit:%i' % self.current
                del temp_orbit_data
                print 'Loaded Orbit:%i' % self.current  

           #get next orbit
	    elif self.current == 0:
	        #autoloads prev day if needed to form complete orbit
	        self.load(orbit=1)

            #if not close to the last orbit,just pull the next orbit
            elif self.current < (self.num - 1):
                self._getBasicOrbit(orbit=self.current+1)
                print 'Loaded Orbit:%i' % self.current  

            else:
                raise Exception('You ended up where noone should ever be. Talk to someone about this fundamental failure.')
              
        else: #no data
    	    while len(self.sat.data) == 0:
    	        self.sat.next()#raises stopIteration at end of dataset
            self.next()
        
    def prev(self, *arg, **kwarg):
        """Load the next orbit into .data.

        Note
        ----
        Forms complete orbits across day boundaries. If no data loaded
        then the last orbit of data from the last day is loaded into .data.
            
        """

        #first, check if data exists
        if len(self.sat.data) > 0:
            #set up orbit metadata
            self._calcOrbits()
            #if not close to the first orbit,just pull the previous orbit
  #          if self.current == self.num:
		#print 'max orbit'
  #              self._getBasicOrbit(orbit=-2)    
                #print 'Loaded Orbit:%i' % self.current

	    if (self.current > 2) & (self.current <= self.num):
                 #load orbit and put it into self.sat.data
                self._getBasicOrbit(orbit=self.current-1)
                #print 'Loaded Orbit:%i' % self.current

            #if current orbit near the last, must be careful
            elif self.current == 2:
                #first, load prev orbit data
                self._getBasicOrbit(orbit=self.current-1)
                #need to save this current orbit and load the next day
                temp_orbit_data = self.sat.data[self.sat.date:]
                #load previous day, which clears orbit breaks info

                try:
                    self.sat.prev() 
                    #combine this next day orbit with previous last orbit
                    if len(self.sat.data) > 0:
                        self.sat.data = pds.concat([self.sat.data, temp_orbit_data])
                        #select first orbit of combined data
                        self._getBasicOrbit(orbit=-1)
                    else:
                        self.sat.next()
                        self._getBasicOrbit(orbit=1)
                except StopIteration:
                    #if loading the first orbit, of first day of data, you'll
                    #end up here as the attempt to make a full orbit will 
                    #move the date backwards, and StopIteration is made.
                    #everything is already ok, just move along
                    pass

                #print 'Loaded Orbit:%i' % self.current
                #clear temporary variable
                del temp_orbit_data

            elif self.current < 2:
                #first, load next orbit data
                self._getBasicOrbit(orbit=1)
                #need to save this current orbit and load the next day
                temp_orbit_data = self.sat.data[self.sat.date:]
                #load previous day, which clears orbit breaks info
                self.sat.prev()
                #combine this next day orbit with previous last orbit
                if len(self.sat.data) > 0:
                    self.sat.data = pds.concat([self.sat.data, temp_orbit_data])
                    #select first orbit of combined data
                    self._getBasicOrbit(orbit=-2)

                #print 'Loaded Orbit:%i' % self.current

                #clear temporary variable
                del temp_orbit_data

            else:
                raise Exception('You ended up where noone should ever be. Talk to someone about this fundamental failure.')
            print 'Loaded Orbit:%i' % self.current 
        else:
           #no data
    	    while len(self.sat.data) == 0:
    	        self.sat.prev()#raises stopIteration at end of dataset
            self.prev()    
            
    def __iter__(self):
        """Support iteration by orbit.
        
        For each iteration the next available orbit is loaded into
        inst.data.
        
        Examples
        --------
        ::
        
            for inst in inst.orbits:
                print 'next available orbit ', inst.data
        
	Note
	----
	Limits of iteration set by setting inst.bounds.	
	
        """
        while True:
            self.next()
            yield self.sat
            
   