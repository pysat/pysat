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
"""Create a constellation with 5 testing instruments.

Attributes
----------
instruments : list
    List of pysat.Instrument objects

Note
----
Each instrument has a different sample size to test the common_index

"""
import pysat

instruments = [pysat.Instrument('pysat', 'testing', clean_level='clean',
                                num_samples=10),
               pysat.Instrument('pysat', 'ndtesting', clean_level='clean',
                                num_samples=16),
               pysat.Instrument('pysat', 'testmodel', clean_level='clean',
                                num_samples=18)]
