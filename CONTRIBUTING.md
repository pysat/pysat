Contributing
============

Bug reports, feature suggestions, and other contributions are greatly
appreciated!  pysat is a community-driven project and welcomes both feedback and
contributions.

Short version
-------------

* Submit bug reports and feature requests at `GitHub <https://github.com/pysat/pysat/issues>`_
* Make pull requests to the ``develop`` branch

Bug reports
-----------

When reporting a bug please include:

* Your operating system name and version
* Any details about your local setup that might be helpful in troubleshooting
* Detailed steps to reproduce the bug

Feature requests and feedback
-----------------------------

The best way to send feedback is to file an issue at
`GitHub <https://github.com/pysat/pysat/issues>`_.

If you are proposing a feature:

* Explain in detail how it would work
* Keep the scope as narrow as possible to make it easier to implement
* Remember that this is a volunteer-driven project, and code contributions
  are welcome :)

Development
-----------

To set up `pysat` for local development:

1. `Fork pysat on GitHub <https://github.com/pysat/pysat/fork>`_.
2. Clone your fork locally::

    git clone git@github.com:your_name_here/pysat.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally. 

   Tests for new instruments are performed automatically.  Tests for custom 
   functions should be added to the appropriately named file in ``pysat/tests``.
   For example, custom functions for the OMNI HRO data are tested in 
   ``pysat/tests/test_omni_hro.py``.  If no test file exists, then you should 
   create one.  This testing uses pytest, which will run tests on any python 
   file in the test directory that starts with ``test``.  Classes must begin 
   with ``Test``, and methods must begin with ``test`` as well.

4. When you're done making changes, run all the checks to ensure that nothing
   is broken on your local system::

    pytest -vs pysat

5. Update/add documentation (in ``docs``), if relevant

6. Add your name to the .zenodo.json file as an author

7. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Brief description of your changes"
    git push origin name-of-your-bugfix-or-feature

8. Submit a pull request through the GitHub website. Pull requests should be
   made to the ``develop`` branch.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code, just
make a pull request. Pull requests should be made to the ``develop`` branch.

For merging, you should:

1. Include an example for use
2. Add a note to ``CHANGELOG.md`` about the changes
3. Ensure that all checks passed (current checks include Scrutinizer, Travis-CI,
   and Coveralls) [1]_

.. [1] If you don't have all the necessary Python versions available locally or
       have trouble building all the testing environments, you can rely on
       Travis to run the tests for each change you add in the pull request.
       Because testing here will delay tests by other developers, please ensure
       that the code passes all tests on your local system first.

Project Style Guidelines
------------------------

In general, pysat follows PEP8 and numpydoc guidelines.  Pytest runs the unit
and integration tests, flake8 checks for style, and sphinx-build performs
documentation tests.  However, there are certain additional style elements that
have been settled on to ensure the project maintains a consistent coding style.
These include:

* Line breaks should occur before a binary operator (ignoring flake8 W503)
* Combine long strings using `join`
* Preferably break long lines on open parentheses rather than using `\`
* Use no more than 80 characters per line
* Avoid using Instrument class key attribute names as unrelated variable names: `platform`, `name`, `tag`, and `inst_id`
* The pysat logger is imported into each sub-module and provides status updates
  at the info and warning levels (as appropriate)
* Several dependent packages have common nicknames, including:
  * `import datetime as dt`
  * `import numpy as np`
  * `import pandas as pds`
  * `import xarray as xr`
* When incrementing a timestamp, use `dt.timedelta` instead of `pds.DateOffset`
  when possible to reduce program runtime
* All classes should have `__repr__` and `__str__` functions
* Docstrings use `Note` instead of `Notes`
* Try to avoid creating a try/except statement where except passes
* Use setup and teardown in test classes
* Use pytest parametrize in test classes when appropriate
* Use pysat testing utilities when appropriate
* Provide testing class methods with informative failure statements and
  descriptive, one-line docstrings
