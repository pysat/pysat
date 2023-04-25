Citations in the pysat ecosystem
================================

When referring to this software package, please cite the original paper by
Stoneback et al [2018] `<https://ntrs.nasa.gov/citations/20190002337>`_
as well as the package `<https://doi.org/10.5281/zenodo.1199703>`_. Note that
this DOI will always point to the latest version of the code.  A list of DOIs
for all versions can be found at the Zenodo page above.

Example for citation in BibTex for a generalized version:

.. code::

  @misc{pysatcode,
    author       = {Stoneback, R.A. and
                    Klenzing, J.H. and
                    Burrell, A.G. and
                    Spence, C. and
                    Depew, M. and
                    Hargrave, N. and
		    Smith, J. and
                    von Bose, V. and
		    Pembroke, A. and
		    Iyer, G. and
                    Luis, S.},
    title        = {Python Satellite Data Analysis Toolkit (pysat) vX.Y.Z},
    year         = 2021,
    doi          = {10.5281/zenodo.1199703},
    url          = {https://doi.org/10.5281/zenodo.1199703}
  }

A simplified implementation of the citation.

.. include:: ../pysat/citation.txt
   :literal:

Citing the publication:

.. code::

  @article{Stoneback2018,
    author    = {Stoneback, R. A. and
                 Burrell, A. G. and
                 Klenzing, J. and
                 Depew, M. D.},
    doi       = {10.1029/2018JA025297},
    issn      = {21699402},
    journal   = {Journal of Geophysical Research: Space Physics},
    number    = {6},
    pages     = {5271--5283},
    title     = {{PYSAT: Python Satellite Data Analysis Toolkit}},
    volume    = {123},
    year      = {2018}
  }

To aid in scientific reproducibility, please include the version number in
publications that use this code.  This can be found by invoking
:py:attr:`pysat.__version__`.

Information for appropriately acknowledging and citing the different instruments
accessed through pysat is available as Instrument attributes
:py:attr:`inst.acknowledgements` and :py:attr:`inst.references`.
If this information is missing, please consider improving pysat by either
submitting an issue or adding the information yourself.
