#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""Tests the pysat MetaHeader object."""

import pytest

import pysat


class TestMetaHeader(object):
    """Unit and integration tests for the MetaLabels class."""

    def setup_method(self):
        """Set up the unit test environment for each method."""

        self.meta_header = pysat.MetaHeader()

        return

    def teardown_method(self):
        """Clean up the unit test environment after each method."""
        del self.meta_header
        return

    # ---------------------------
    # Test the class magic methods

    def test_repr(self):
        """Test the `MetaHeader.__repr__` method."""

        out = repr(self.meta_header)
        assert isinstance(out, str)
        assert out.find('pysat.MetaHeader(') >= 0
        return

    def test_eval(self):
        """Test the `MetaHeader.__repr__` method can be called using eval."""

        out = eval(repr(self.meta_header))
        assert out == self.meta_header
        return

    def test_str(self):
        """Test the `MetaHeader.__str__` method."""

        out = self.meta_header.__str__()
        assert isinstance(out, str)
        assert out.find('Metadata for') >= 0
        assert out.find('global attributes') >= 0
        return

    @pytest.mark.parametrize("other", [
        pysat.Meta(), pysat.MetaHeader(header_data={'test': 'value'})])
    def test_not_equal(self, other):
        """Test the MetaHeader inequality.

        Parameters
        ----------
        other : any
            Object not equal to the default MetaHeader object

        """

        assert other != self.meta_header
        return

    def test_not_equal_bad_class(self):
        """Test the MetaHeader inequality with a badly formed class."""

        other = pysat.MetaHeader()
        delattr(other, "global_attrs")
        assert other != self.meta_header
        assert self.meta_header != other
        return

    @pytest.mark.parametrize("header_data", [None, {"test": "value"}])
    def test_equal(self, header_data):
        """Test the MetaHeader equality.

        Parameters
        ----------
        header_data : dict or NoneType
            Dict of data to put in the MetaHeader class

        """

        other = pysat.MetaHeader(header_data=header_data)

        if header_data is not None:
            for hkey in header_data.keys():
                setattr(self.meta_header, hkey, header_data[hkey])

        assert self.meta_header == other
        assert other == self.meta_header
        return

    # -----------------------------
    # Test the class public methods

    @pytest.mark.parametrize("header_data", [{}, {"test": "value"}])
    def test_to_dict(self, header_data):
        """Test the MetaHeader equality.

        Parameters
        ----------
        header_data : dict
            Dict of data to put in the MetaHeader class

        """

        # Initialize the MetaHeader data
        self.meta_header = pysat.MetaHeader(header_data=header_data)

        # Convert to a dictionary
        out_dict = self.meta_header.to_dict()

        # Test the output dictionary
        assert header_data == out_dict
        return

    # ----------------------------------------
    # Test the integration with the Meta class

    @pytest.mark.parametrize("header_data", [{}, {"test": "value"}])
    def test_init_metaheader_in_meta(self, header_data):
        """Test changing case of meta labels after initialization.

        Parameters
        ----------
        header_data : dict
            Dict of data to put in the MetaHeader class

        """

        # Initalize the header data directly and through the meta object
        meta = pysat.Meta(header_data=header_data)
        self.meta_header = pysat.MetaHeader(header_data=header_data)

        # Ensure both initialization methods work the same
        assert meta.header == self.meta_header
        return
