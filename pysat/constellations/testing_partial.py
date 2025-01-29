#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
#
# Review Status for Classified or Controlled Information by NRL
# -------------------------------------------------------------
# DISTRIBUTION STATEMENT A: Approved for public release. Distribution is
# unlimited.
# ----------------------------------------------------------------------------
"""Create a constellation where not all instruments have loadable data.

Attributes
----------
instruments : list
    List of pysat.Instrument objects

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10),
               pysat.Instrument('pysat', 'testing', tag='no_download',
                                clean_level='clean')]
