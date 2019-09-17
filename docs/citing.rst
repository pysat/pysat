Citations in the pysat ecosystem
================================

When referring to this software package, please cite the original paper by Stoneback et al [2018] https://doi.org/10.1029/2018JA025297 as well as the package https://doi.org/10.5281/zenodo.1199703. Note that this doi will always point to the latest version of the code.  A list of dois for all versions can be found at the [zenodo page](https://zenodo.org/record/3321222).

Citing the package (Version 2.0):

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
    title        = {Python Satellite Data Analysis Toolkit (pysat) v2.0},
    month        = jul,
    year         = 2019,
    doi          = {10.5281/zenodo.3321222},
    url          = {https://doi.org/10.5281/zenodo.3321222}
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

To aid in scientific reproducibility, please include the version number in publications that use this code.  This can be found by invoking `pysat.__version__ `.

Information for appropriately acknowledging and citing the different instruments accessed through pysat is sometimes available in the metadata through `inst.meta.info.acknowledgements` and `inst.meta.info.reference`.  If this information is missing, please consider improving pysat by either submitting an issue or adding the information yourself.
