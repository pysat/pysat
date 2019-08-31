"""
pysat.ssnl is a pysat module that provides
the interface to perform seasonal analysis on
data managed by pysat.  These analysis methods
are independent of instrument type.

Main Features
-------------
- Seasonal averaging routine for 1D and 2D data.
- Occurrence probability routines, daily or by orbit.
- Scatterplot of data_label(s) as functions of labelx,y
    over a season.

"""

from . import occur_prob
from . import avg
from . import plot
from ._core import computational_form
