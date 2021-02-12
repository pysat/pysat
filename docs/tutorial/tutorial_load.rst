.. _tutorial-load:

Data Loading
============

The pysat ``load`` method takes care of a lot of the processing details needed
to produce a scientifically useful data set.  The image below provides an
overview of this proceess.

.. image:: ../images/pysat_load_flow_chart.png

	   
Clean Data
----------

Before data is available in .data it passes through an instrument specific
cleaning routine. The amount of cleaning is set by the clean_level keyword,
provided at instantiation. The level defaults to 'clean'.

.. code:: python

   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd',
                           inst_id='f12', clean_level=None)
   dmsp = pysat.Instrument(platform='dmsp', name='ivm', tag='utd',
                           inst_id='f12', clean_level='clean')

Four levels of cleaning may be specified,

===============     ===================================
**clean_level** 	        **Result**
---------------     -----------------------------------
  clean		        Generally good data
  dusty		        Light cleaning, use with care
  dirty		        Minimal cleaning, use with caution
  none		        No cleaning, use at your own risk
===============     ===================================

The user provided cleaning level is can be retrieved or reset from the
Instrument object attribute `clean_level`. The details of the cleaning will
generally vary greatly between instruments.  Many instruments provide only two
levels of data: `clean` or `none`.

Custom Functions
----------------

See :ref:`tutorial_custom`
