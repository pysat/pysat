import pysat
"""
Creates a constellation from NASA ICON instrumentation
"""


ivm = pysat.Instrument('icon', 'ivm', sat_id='a', tag='level_2',
                       clean_level='clean', update_files=True)
euv = pysat.Instrument('icon', 'euv', sat_id='', tag='level_2',
                       clean_level='clean', update_files=True)
fuv = pysat.Instrument('icon', 'fuv', sat_id='', tag='level_2',
                       clean_level='clean', update_files=True)
mighti_green = pysat.Instrument('icon', 'mighti', sat_id='green',
                                tag='level_2', clean_level='clean',
                                update_files=True)
mighti_red = pysat.Instrument('icon', 'mighti', sat_id='red', tag='level_2',
                              clean_level='clean', update_files=True)

instruments = [ivm, euv, fuv, mighti_green, mighti_red]
