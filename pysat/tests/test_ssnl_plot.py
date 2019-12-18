"""
tests the pysat averaging code
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import warnings
import pysat
from pysat.ssnl import plot


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean')
        self.testInst.bounds = (pysat.datetime(2008, 1, 1),
                                pysat.datetime(2008, 1, 1))

    def teardown(self):
        """Runs after every method to clean up previous testing."""
        del self.testInst
        plt.close()

    def test_scatterplot_w_ioff(self):
        """Check if scatterplot generates"""

        plt.ioff()
        figs = plot.scatterplot(self.testInst, 'longitude', 'latitude',
                                'slt', [0.0, 24.0])

        axes = figs[0].get_axes()
        assert len(figs) == 1
        assert len(axes) == 3
        assert not mpl.is_interactive()

    def test_scatterplot_w_ion(self):
        """Check if scatterplot generates and resets to interactive mode"""

        plt.ion()
        figs = plot.scatterplot(self.testInst, 'longitude', 'latitude',
                                'slt', [0.0, 24.0])

        axes = figs[0].get_axes()
        assert len(figs) == 1
        assert len(axes) == 3
        assert mpl.is_interactive()

    def test_scatterplot_w_limits(self):
        """Check if scatterplot generates with appropriate limits"""

        figs = plot.scatterplot(self.testInst, 'longitude', 'latitude',
                                'slt', [0.0, 24.0],
                                xlim=[0, 360], ylim=[-80, 80])

        axes = figs[0].get_axes()
        assert len(figs) == 1
        assert len(axes) == 3
        assert axes[0].get_xlim() == (0, 360)
        assert axes[1].get_xlim() == (0, 360)
        assert axes[0].get_ylim() == (-80, 80)
        assert axes[1].get_ylim() == (-80, 80)

    def test_multiple_scatterplots(self):
        """Check if multiple scatterplots generate"""
        figs = plot.scatterplot(self.testInst, 'longitude', 'latitude',
                                ['slt', 'mlt'], [0.0, 24.0])

        axes = figs[0].get_axes()
        axes2 = figs[1].get_axes()
        assert len(figs) == 2
        assert len(axes) == 3
        assert len(axes2) == 3


class TestDeprecation():
    def setup(self):
        """Runs before every method to create a clean testing setup."""
        warnings.simplefilter("always")

    def teardown(self):
        """Runs after every method to clean up previous testing."""

    def test_deprecation_warning_scatterplot(self):
        """Test if scatterplot in ssnl is deprecated"""

        with warnings.catch_warnings(record=True) as war:
            try:
                plot.scatterplot(None, 'longitude', 'latitude', ['slt', 'mlt'],
                                 [0.0, 24.0])
            except TypeError:
                # Setting inst to None should produce a TypeError after
                # warning is generated
                pass

        assert len(war) >= 1
        assert war[0].category == DeprecationWarning
