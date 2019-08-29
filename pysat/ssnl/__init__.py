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

from . import occur_prob  # noqa: 401
from . import avg  # noqa: 401
from . import plot  # noqa: 401
from ._core import computational_form  # noqa: 401
