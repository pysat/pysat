Contributing
============

Bug reports, feature suggestions and other contributions are greatly
appreciated!  Pysat is a community-driven project and welcomes both feedback and
contributions.

Short version
=============

* Submit bug reports and feature requests at `GitHub <https://github.com/rstoneback/pysat/issues>`_
* Make pull requests to the ``develop`` branch

Bug reports
===========

When `reporting a bug <https://github.com/rstoneback/pysat/issues>`_ please
include:

* Your operating system name and version
* Any details about your local setup that might be helpful in troubleshooting
* Detailed steps to reproduce the bug

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at
`GitHub <https://github.com/rstoneback/pysat/issues>`_.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions
  are welcome :)

Development
===========

To set up `pysat` for local development:

1. `Fork pysat on GitHub <https://github.com/rstoneback/pysat/fork>`_.
2. Clone your fork locally::

    git clone git@github.com:your_name_here/pysat.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally. Tests for new instruments are
   performed automatically.  Tests for custom functions should be added to the
   appropriately named file in ``pysat/tests``.  For example, custom functions
   for the OMNI HRO data are tested in ``pysat/tests/test_omni_hro.py``.  If no
   test file exists, then you should create one.  This testing uses nose, which
   will run tests on any python file in the test directory that starts with
   ``test_``.

4. When you're done making changes, run all the checks to ensure that nothing
   is broken on your local system::

    nosetests -vs pysat

5. Update/add documentation (in ``docs``), if relevant

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Brief description of your changes"
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website. Pull requests should be
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
