"""
Creates a constellation from NASA ICON instrumentation

.. deprecated:: 2.3.0
  This routine has been deprecated in pysat 3.0.0, and will be accessible
  in `pysatNASA.constellations.icon`

"""

import pysat

ivm = pysat.Instrument('icon', 'ivm', sat_id='a', tag='',
                       clean_level='clean', update_files=True)
euv = pysat.Instrument('icon', 'euv', sat_id='', tag='',
                       clean_level='clean', update_files=True)
fuv_day = pysat.Instrument('icon', 'fuv', sat_id='', tag='day',
                           clean_level='clean', update_files=True)
fuv_night = pysat.Instrument('icon', 'fuv', sat_id='', tag='night',
                             clean_level='clean', update_files=True)
mighti_vw_red = pysat.Instrument('icon', 'mighti', sat_id='',
                                 tag='vector_wind_red',
                                 clean_level='clean', update_files=True)
mighti_vw_green = pysat.Instrument('icon', 'mighti', sat_id='',
                                   tag='vector_wind_green',
                                   clean_level='clean', update_files=True)
mighti_temp_a = pysat.Instrument('icon', 'mighti', sat_id='a',
                                 tag='temperature',
                                 clean_level='clean', update_files=True)
mighti_temp_b = pysat.Instrument('icon', 'mighti', sat_id='b',
                                 tag='temperature',
                                 clean_level='clean', update_files=True)

instruments = [ivm, euv, fuv_day, fuv_night, mighti_vw_red, mighti_vw_green,
               mighti_temp_a, mighti_temp_b]
