Citations in the pysat ecosystem
================================

When referring to this software package, please cite the original paper by
Stoneback et al [2018] `<https://doi.org/10.1029/2018JA025297>`_ as well as the
package `<https://doi.org/10.5281/zenodo.1199703>`_. Note that this DOI will
always point to the latest version of the code.  A list of DOIs for all
versions can be found at the Zenodo page above.

Example for citation in BibTex for a generalized version:

.. code::

  @misc{pysat200,
    author       = {Stoneback, R.A. and
                    Klenzing, J.H. and
                    Burrell, A.G. and
                    Spence, C. and
                    Depew, M. and
                    Hargrave, N. and
                    von Bose, V. and
                    Luis, S. and
                    Iyer, G.},
    title        = {Python Satellite Data Analysis Toolkit (pysat) vX.Y.Z},
    month        = jul,
    year         = 2019,
    doi          = {10.5281/zenodo.1199703},
    url          = {https://doi.org/10.5281/zenodo.1199703}
  }

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
`pysat.__version__ `.

Information for appropriately acknowledging and citing the different instruments
accessed through pysat is sometimes available in the metadata through
``inst.meta.acknowledgements`` and ``inst.meta.references``.
If this information is missing, please consider improving pysat by either
submitting an issue or adding the information yourself.
