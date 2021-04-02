#!/usr/bin/env python
# Full license can be found in License.md
# Full author list can be found in .zenodo.json file
# DOI:10.5281/zenodo.1199703
# ----------------------------------------------------------------------------
"""
tests the pysat meta object and code
"""
import netCDF4
import numpy as np
import os
import pandas as pds
import pytest
import warnings

import pysat
import pysat.instruments.pysat_testing
import pysat.tests.test_utils
from pysat.utils import testing


class TestBasics():
    def setup(self):
        """Runs before every method to create a clean testing setup
        """
        self.testInst = pysat.Instrument('pysat', 'testing')
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.meta = self.testInst.meta

        self.meta_labels = {'units': ('Units', str),
                            'name': ('Long_Name', str)}
        self.dval = None
        self.out = None
        self.default_name = ['long_name']
        self.default_nan = ['fill', 'value_min', 'value_max']
        self.default_val = {'notes': '', 'units': '', 'desc': ''}
        self.frame_list = ['dummy_frame1', 'dummy_frame2']

    def teardown(self):
        """Runs after every method to clean up previous testing
        """
        del self.testInst, self.meta, self.out, self.stime, self.meta_labels
        del self.default_name, self.default_nan, self.default_val, self.dval
        del self.frame_list

    def check_meta_settings(self):
        """ Test the Meta settings for a specified value
        """
        # Test the Meta data for the data value, self.dval
        for lkey in self.default_name:
            assert self.meta[self.dval, lkey] == self.dval

        for lkey in self.default_nan:
            assert np.isnan(self.meta[self.dval, lkey])

        for lkey in self.default_val.keys():
            assert self.meta[self.dval, lkey] == self.default_val[lkey]

        assert 'children' not in self.meta.data.columns
        assert self.dval not in self.meta.keys_nD()

    def test_default_label_value_raises_error(self):
        """ Test MetaLabels.default_values_from_attr ValueError with bad attr
        """
        with pytest.raises(ValueError) as verr:
            self.meta.labels.default_values_from_attr('not_an_attr')

        assert verr.match("unknown label attribute")

    def test_meta_repr(self):
        """ Test the Meta repr function
        """
        self.out = self.meta.__repr__()
        assert isinstance(self.out, str)
        assert self.out.find('Meta(') >= 0

    def test_setting_nonpandas_metadata(self):
        """ Test meta initialization with bad metadata
        """
        with pytest.raises(ValueError):
            self.meta = pysat.Meta(metadata='Not a Panda')

    @pytest.mark.parametrize("labels,vals",
                             [([], []),
                              (['units', 'long_name'], ['V', 'Longgggg']),
                              (['fill'], [-999])])
    def test_inst_data_assign_meta(self, labels, vals):
        """ Test Meta initialization with data
        """
        # Initialize the instrument
        self.testInst.load(date=self.stime)
        self.dval = 'test_inst_data_assign_meta'

        # Update the testing data and set the new data dictionary
        set_dict = {'data': self.testInst['mlt']}
        for i, slabel in enumerate(labels):
            if slabel in self.default_name:
                self.default_name.pop(self.default_name.index(slabel))
            elif slabel in self.default_nan:
                self.default_nan.pop(self.default_nan.index(slabel))
            self.default_val[slabel] = vals[i]
            set_dict[slabel] = vals[i]

        # Initialize the Meta data
        self.testInst[self.dval] = set_dict
        self.meta = self.testInst.meta

        # Test the Meta settings
        self.check_meta_settings()

    @pytest.mark.parametrize("mlabel,slist", [("units", []),
                                              ("notes", ['A', 'B'])])
    def test_inst_data_assign_meta_string_list(self, mlabel, slist):
        """ Test string assignment to meta with a list of strings
        """
        # Initialize the Meta Data
        self.testInst.load(date=self.stime)
        self.dval = 'test_inst_data_assign_meta_string_list'
        self.testInst[self.dval] = {'data': self.testInst['mlt'],
                                    mlabel: slist}
        self.meta = self.testInst.meta

        # Update the testing data
        self.default_val[mlabel] = '\n\n'.join(slist)

        # Test the Meta settings
        self.check_meta_settings()

    def test_init_labels_w_int_default(self):
        """ Test MetaLabels initiation with an integer label type
        """
        # Reinitialize the Meta and test for warning
        self.meta_labels['fill_val'] = ("fill", int)

        with warnings.catch_warnings(record=True) as war:
            self.testInst = pysat.Instrument('pysat', 'testing',
                                             tag='default_meta',
                                             clean_level='clean',
                                             labels=self.meta_labels)
            self.testInst.load(date=self.stime)

        # Test the warning
        default_str = ''.join(['Metadata set to defaults, as they were',
                               ' missing in the Instrument'])
        assert len(war) >= 1
        assert war[0].category == UserWarning
        assert default_str in str(war[0].message)

        # Prepare to test the Metadata
        self.meta = self.testInst.meta
        self.dval = 'int32_dummy'
        self.default_val['fill'] = -1
        self.default_val['notes'] = default_str
        self.default_nan.pop(self.default_nan.index('fill'))

        # Test the Meta settings
        self.check_meta_settings()

    def test_inst_data_assign_meta_empty_list(self):
        self.testInst.load(2009, 1)
        self.testInst['help'] = {'data': self.testInst['mlt'],
                                 'units': [],
                                 'long_name': 'The Doors'}
        assert self.testInst.meta['help', 'units'] == ''

    def test_inst_data_assign_meta_then_data(self):
        """ Test meta assignment when data updated after metadata
        """
        # Initialize the Meta data
        self.dval = 'test_inst_data_assign_meta_then_data'
        self.testInst.load(date=self.stime)
        self.testInst[self.dval] = {'data': self.testInst['mlt'], 'units': 'V'}
        self.testInst[self.dval] = self.testInst['mlt']
        self.meta = self.testInst.meta

        # Update the testing data
        self.default_val['units'] = 'V'

        # Test the Meta settings
        self.check_meta_settings()

    def test_inst_ho_data_assign_no_meta_default(self):
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.testInst['help'] = [frame] * len(self.testInst.data.index)

        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])
        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

    def test_inst_ho_data_assign_meta_default(self):
        """ Test the assignment of the default higher order metadata
        """
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'long_name': 'The Doors'}

        assert self.testInst.meta['help', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])
        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

    def test_inst_ho_data_assign_meta(self):
        """ Test the assignemnt of custom higher order metadata
        """
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        meta = pysat.Meta()
        meta['dummy_frame1'] = {'units': 'A'}
        meta['dummy_frame2'] = {'desc': 'nothing'}
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'long_name': 'The Doors',
                                 'meta': meta}

        assert self.testInst.meta['help', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])

        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'units'] == 'A'
        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'desc'] == ''
        assert self.testInst.meta['help']['children']['dummy_frame2',
                                                      'desc'] == 'nothing'

    def test_inst_ho_data_assign_meta_then_data(self):
        """ Test assignment of higher order metadata before assigning data
        """
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        meta = pysat.Meta()
        meta['dummy_frame1'] = {'units': 'A'}
        meta['dummy_frame2'] = {'desc': 'nothing'}
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'long_name': 'The Doors',
                                 'meta': meta}

        self.testInst['help'] = [frame] * self.testInst.index.shape[0]

        assert self.testInst.meta['help', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])

        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'units'] == 'A'
        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'desc'] == ''
        assert self.testInst.meta['help']['children']['dummy_frame2',
                                                      'desc'] == 'nothing'

    def test_inst_ho_data_assign_meta_different_labels(self):
        """ Test the higher order assignment of custom metadata labels
        """
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.meta_labels = {'units': ('barrels', str),
                            'desc': ('Monkeys', str),
                            'meta': ('meta', object)}
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['dummy_frame1'] = {'barrels': 'A'}
        self.meta['dummy_frame2'] = {'Monkeys': 'are fun'}
        self.meta['dummy_frame2'] = {'bananas': 2}

        # The 'units', 'desc' and other labels used on self.testInst are
        # applied to the input metadata to ensure everything remains
        # consistent across the object.
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'long_name': 'The Doors',
                                 'meta': self.meta}

        assert self.testInst.meta['help', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])

        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'units'] == 'A'
        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'desc'] == ''
        assert self.testInst.meta['help']['children']['dummy_frame2',
                                                      'desc'] == 'are fun'

    def test_inst_assign_from_meta(self):
        """Test Meta assignment form another meta object
        """
        # Assign new meta data
        self.dval = "test_inst_assing_from_meta"
        self.testInst.load(date=self.stime)
        self.testInst['new_data'] = self.testInst['mlt']
        self.testInst[self.dval] = self.testInst['mlt']
        self.testInst.meta[self.dval] = self.testInst.meta['new_data']
        self.meta = self.testInst.meta

        # Update testing info
        for skey in self.default_name:
            self.default_val[skey] = 'new_data'
        self.default_name = []

        # Test the Meta settings
        self.check_meta_settings()

    def test_inst_assign_from_meta_w_ho(self):
        """ Test assignment to Instrument from Meta with higher order data
        """
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.meta = pysat.Meta()
        self.meta['dummy_frame1'] = {'units': 'A'}
        self.meta['dummy_frame2'] = {'desc': 'nothing'}
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'long_name': 'The Doors',
                                 'meta': self.meta}
        self.testInst['help2'] = self.testInst['help']
        self.testInst.meta['help2'] = self.testInst.meta['help']

        assert self.testInst.meta['help'].children['dummy_frame1',
                                                   'units'] == 'A'
        assert self.testInst.meta['help2', 'long_name'] == 'The Doors'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help']['children'])
        for label in ['units', 'desc']:
            assert self.testInst.meta['help']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'desc'] == ''
        assert self.testInst.meta['help2']['children']['dummy_frame2',
                                                       'desc'] == 'nothing'
        assert 'children' not in self.testInst.meta.data.columns

    def test_inst_assign_from_meta_w_ho_then_update(self):
        """ Test assignment of Instrument.meta from separate Meta with HO data
        """
        self.testInst.load(date=self.stime)
        frame = pds.DataFrame({fkey: np.arange(10) for fkey in self.frame_list},
                              columns=self.frame_list)
        self.meta = pysat.Meta()
        self.meta['dummy_frame1'] = {'units': 'A'}
        self.meta['dummy_frame2'] = {'desc': 'nothing'}
        self.testInst['help'] = {'data': [frame] * self.testInst.index.shape[0],
                                 'units': 'V', 'name': 'The Doors',
                                 'meta': self.meta}
        self.testInst['help2'] = self.testInst['help']
        self.testInst.meta['help2'] = self.testInst.meta['help']
        new_meta = self.testInst.meta['help2'].children
        new_meta['dummy_frame1'] = {'units': 'Amps', 'desc': 'something',
                                    'label': 'John Wick'}
        self.testInst.meta['help2'] = new_meta
        self.testInst.meta['help2'] = {'label': 'The Doors Return'}

        assert self.testInst.meta['help']['children']['dummy_frame1',
                                                      'units'] == 'A'
        assert self.testInst.meta['help2', 'name'] == 'The Doors'
        assert self.testInst.meta['help2', 'label'] == 'The Doors Return'
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta.ho_data['help2'])
        testing.assert_list_contains(self.frame_list,
                                     self.testInst.meta['help2']['children'])
        for label in ['units', 'desc']:
            assert self.testInst.meta['help2']['children'].hasattr_case_neutral(
                label)

        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'desc'] == 'something'
        assert self.testInst.meta['help2']['children']['dummy_frame2',
                                                       'desc'] == 'nothing'
        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'units'] == 'Amps'
        assert self.testInst.meta['help2']['children']['dummy_frame1',
                                                       'label'] == 'John Wick'
        assert 'children' not in self.testInst.meta.data.columns

    def test_str_call_runs_long_standard(self):
        """ Test long string output with custom meta data
        """
        self.meta['hi'] = {'units': 'yoyo', 'long_name': 'hello'}
        output = self.meta.__str__()
        assert output.find('pysat Meta object') >= 0
        assert output.find('hi') > 0
        assert output.find('Standard Metadata variables') > 0
        assert output.find('ND Metadata variables') < 0

    def test_str_call_runs_short(self):
        """ Test short string output with custom meta data
        """
        self.meta['hi'] = {'units': 'yoyo', 'long_name': 'hello'}
        output = self.testInst.meta.__str__(long_str=False)
        assert output.find('pysat Meta object') >= 0
        assert output.find('hi') < 0
        assert output.find('Metadata variables') < 0

    def test_str_call_runs_with_higher_order_data(self):
        """ Test string output with higher order data
        """
        ho_meta = pysat.Meta()
        ho_meta['param1'] = {'units': 'blank', 'long_name': 'parameter1',
                             'custom1': 14, 'custom2': np.nan,
                             'custom3': 14.5, 'custom4': 'hello'}
        ho_meta['param0'] = {'units': 'basic', 'long_name': 'parameter0',
                             self.meta.labels.fill_val: '10', 'CUSTOM4': 143}
        self.meta['kiwi'] = ho_meta
        output = self.meta.__str__()
        assert output.find('pysat Meta object') >= 0
        assert output.find('kiwi') >= 0
        assert output.find('ND Metadata variables') >= 0
        assert output.find('Standard Metadata variables') < 0

    def test_basic_pops(self):
        """ Test meta attributes are retained when extracted using pop
        """
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew',
                             'value_min': 0, 'value_max': 1}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo', 'fill': 1,
                             'value_min': 0, 'value_max': 1}

        # create then assign higher order meta data
        meta2 = pysat.Meta()
        meta2['new31'] = {'units': 'hey3', 'long_name': 'crew_brew', 'fill': 1,
                          'value_min': 0, 'value_max': 1}
        self.meta['new3'] = meta2

        aa = self.meta.pop('new3')
        assert np.all(aa['children'] == meta2)

        # ensure lower metadata created when ho data assigned
        assert aa['units'] == ''
        assert aa['long_name'] == 'new3'
        m1 = self.meta['new2']
        m2 = self.meta.pop('new2')
        assert m1['children'] is None
        assert m2['children'] is None
        for key in m1.index:
            if key not in ['children']:
                assert m1[key] == m2[key]

        # make sure both have the same indexes
        assert np.all(m1.index == m2.index)

    def test_basic_pops_w_bad_key(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew',
                             'value_min': 0, 'value_max': 1}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo', 'fill': 1,
                             'value_min': 0, 'value_max': 1}
        with pytest.raises(KeyError):
            _ = self.meta.pop('new4')

    def test_basic_getitem_w_bad_key_string(self):
        with pytest.raises(KeyError):
            self.meta['new4']

    def test_basic_getitem_w_integer(self):
        with pytest.raises(NotImplementedError):
            self.meta[1]

    def test_basic_equality(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo', 'fill': np.NaN}
        # ensure things are the same
        meta2 = self.meta.copy()
        assert (meta2 == self.meta)

        # different way to create meta object
        meta3 = pysat.Meta()
        meta3['new1'] = self.meta['new1']
        meta3['new2'] = self.meta['new2']
        assert (meta3 == self.meta)

        # make sure differences matter
        self.meta['new2'] = {'fill': 1}
        assert not (meta2 == self.meta)

    def test_basic_concat(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        meta2 = pysat.Meta()
        meta2['new3'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        self.meta = self.meta.concat(meta2)

        assert (self.meta['new3'].units == 'hey3')

    def test_concat_w_name_collision_strict(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        meta2 = pysat.Meta()
        meta2['new2'] = {'units': 'hey2', 'long_name': 'crew_brew'}
        meta2['new3'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        with pytest.raises(RuntimeError):
            self.meta = self.meta.concat(meta2, strict=True)

    def test_basic_concat_w_ho(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        meta2 = pysat.Meta()
        meta2['new3'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        meta3 = pysat.Meta()
        meta3['new41'] = {'units': 'hey4', 'long_name': 'crew_brew',
                          'bob_level': 'max'}
        meta2['new4'] = meta3
        self.meta = self.meta.concat(meta2)

        assert (self.meta['new3'].units == 'hey3')
        assert (self.meta['new4'].children['new41'].units == 'hey4')

    def test_basic_concat_w_ho_collision_strict(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        meta2 = pysat.Meta()
        meta2['new31'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        self.meta['new3'] = meta2
        meta3 = pysat.Meta()
        meta3['new31'] = {'units': 'hey4', 'long_name': 'crew_brew',
                          'bob_level': 'max'}
        meta2['new3'] = meta3
        with pytest.raises(RuntimeError):
            self.meta = self.meta.concat(meta2, strict=True)

    def test_basic_concat_w_ho_collision_not_strict(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        meta2 = pysat.Meta()
        meta2['new3'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        meta3 = pysat.Meta()
        meta3['new41'] = {'units': 'hey4', 'long_name': 'crew_brew',
                          'bob_level': 'max'}
        meta2['new3'] = meta3
        self.meta = self.meta.concat(meta2, strict=False)

        assert self.meta['new3'].children['new41'].units == 'hey4'
        assert self.meta['new3'].children['new41'].bob_level == 'max'
        assert self.meta['new2'].units == 'hey'

    def test_basic_concat_w_ho_collisions_not_strict(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        meta2 = pysat.Meta()
        meta2['new31'] = {'units': 'hey3', 'long_name': 'crew_brew'}
        self.meta['new3'] = meta2
        meta3 = pysat.Meta()
        meta3['new31'] = {'units': 'hey4', 'long_name': 'crew_brew',
                          'bob_level': 'max'}
        meta2['new3'] = meta3
        self.meta = self.meta.concat(meta2, strict=False)

        assert self.meta['new3'].children['new31'].units == 'hey4'
        assert self.meta['new3'].children['new31'].bob_level == 'max'
        assert self.meta['new2'].units == 'hey'

    def test_basic_meta_assignment(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        assert (self.meta['new'].units == 'hey')
        assert (self.meta['new'].long_name == 'boo')

    def test_basic_meta_assignment_w_Series(self):
        self.meta['new'] = pds.Series({'units': 'hey', 'long_name': 'boo'})
        assert (self.meta['new'].units == 'hey')
        assert (self.meta['new'].long_name == 'boo')

    def test_multiple_meta_assignment(self):
        self.meta[['new', 'new2']] = {'units': ['hey', 'hey2'],
                                      'long_name': ['boo', 'boo2']}
        assert self.meta['new'].units == 'hey'
        assert self.meta['new'].long_name == 'boo'
        assert self.meta['new2'].units == 'hey2'
        assert self.meta['new2'].long_name == 'boo2'

    def test_multiple_meta_retrieval(self):
        self.meta[['new', 'new2']] = {'units': ['hey', 'hey2'],
                                      'long_name': ['boo', 'boo2']}
        self.meta[['new', 'new2']]
        self.meta[['new', 'new2'], :]
        self.meta[:, 'units']
        self.meta['new', ('units', 'long_name')]

    def test_multiple_meta_ho_data_retrieval(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower']] = {'meta': [meta, None],
                                          'units': [None, 'boo'],
                                          'long_name': [None, 'boohoo']}
        assert self.meta['lower'].units == 'boo'
        assert self.meta['lower'].long_name == 'boohoo'
        assert self.meta['higher'].children == meta

    def test_multiple_meta_assignment_error(self):
        with pytest.raises(ValueError):
            self.meta[['new', 'new2']] = {'units': ['hey', 'hey2'],
                                          'long_name': ['boo']}

    def test_replace_meta_units(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new'] = {'units': 'yep'}
        assert (self.meta['new'].units == 'yep')
        assert (self.meta['new'].long_name == 'boo')

    def test_replace_meta_long_name(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new'] = {'long_name': 'yep'}
        assert (self.meta['new'].units == 'hey')
        assert (self.meta['new'].long_name == 'yep')

    def test_add_additional_metadata_types(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo',
                            'description': 'boohoo'}

        assert (self.meta['new'].units == 'hey')
        assert (self.meta['new'].long_name == 'boo')
        assert (self.meta['new'].description == 'boohoo')

    def test_add_meta_then_add_additional_metadata_types(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'crew'}
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo',
                            'description': 'boohoo'}

        assert self.meta['new'].units == 'hey'
        assert self.meta['new'].long_name == 'boo'
        assert self.meta['new'].description == 'boohoo'

    def test_add_meta_with_custom_then_add_additional_metadata_types(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'crew',
                            'description': 'boohoo'}
        self.meta['new'] = {'units': 'hey2', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'heyy', 'long_name': 'hoo'}
        self.meta['new3'] = {'units': 'hey3', 'long_name': 'crew3',
                             'description': 'boohoo3'}
        assert self.meta['new'].units == 'hey2'
        assert self.meta['new'].long_name == 'boo'
        assert self.meta['new'].description == 'boohoo'
        assert self.meta['new3'].description == 'boohoo3'
        assert self.meta['new2'].long_name == 'hoo'

    def test_add_meta_then_add_different_additional_metadata_types(self):
        self.meta['new1'] = {'units': 'hey1', 'long_name': 'crew'}
        self.meta['new2'] = {'units': 'hey', 'long_name': 'boo',
                             'description': 'boohoo'}
        assert self.meta['new2'].units == 'hey'
        assert self.meta['new2'].long_name == 'boo'
        assert self.meta['new2'].description == 'boohoo'
        assert self.meta['new1'].units == 'hey1'
        assert self.meta['new1'].long_name == 'crew'
        assert np.isnan(self.meta['new1'].description)

    def test_add_meta_then_partially_add_additional_metadata_types(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'crew'}
        self.meta['new'] = {'long_name': 'boo', 'description': 'boohoo'}

        assert self.meta['new'].units == 'hey'
        assert self.meta['new'].long_name == 'boo'
        assert self.meta['new'].description == 'boohoo'

    def test_meta_equality(self):
        """ Test basic equality case
        """
        assert self.testInst.meta == self.testInst.meta

    def test_false_meta_equality(self):
        """ Test inequality with different types
        """
        assert not (self.testInst.meta == self.testInst)

    def test_equality_with_higher_order_meta(self):
        self.meta = pysat.Meta()
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = meta
        meta2 = pysat.Meta()
        meta2['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta2['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        meta3 = pysat.Meta()
        meta3['higher'] = meta2
        assert meta3 == self.meta
        assert self.meta == meta3

    def test_inequality_with_higher_order_meta(self):
        self.meta = pysat.Meta()
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo', 'radn': 'raiden'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = meta
        meta2 = pysat.Meta()
        meta2['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta2['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        meta3 = pysat.Meta()
        meta3['higher'] = meta2
        assert not (meta3 == self.meta)
        assert not (self.meta == meta3)

    def test_inequality_with_higher_order_meta2(self):
        self.meta = pysat.Meta()
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey2', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = meta
        meta2 = pysat.Meta()
        meta2['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta2['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        meta3 = pysat.Meta()
        meta3['higher'] = meta2

        assert not (meta3 == self.meta)
        assert not (self.meta == meta3)

    def test_inequality_with_higher_order_meta3(self):
        self.meta = pysat.Meta()
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = meta
        self.meta['lower'] = {'units': 'yoyooy'}
        meta2 = pysat.Meta()
        meta2['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta2['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        meta3 = pysat.Meta()
        meta3['higher'] = meta2

        assert not (meta3 == self.meta)
        assert not (self.meta == meta3)

    def test_assign_higher_order_meta(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = meta

    def test_assign_higher_order_meta_from_dict(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = {'meta': meta}

    def test_assign_higher_order_meta_from_dict_correct(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta['higher'] = {'meta': meta}
        assert self.meta['higher'].children == meta

    def test_assign_higher_order_meta_from_dict_w_multiple(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower']] = {'meta': [meta, None],
                                          'units': [None, 'boo'],
                                          'long_name': [None, 'boohoo']}
        assert self.meta['lower'].units == 'boo'
        assert self.meta['lower'].long_name == 'boohoo'
        assert self.meta['higher'].children == meta

    def test_assign_higher_order_meta_from_dict_w_multiple_2(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower', 'lower2']] = \
            {'meta': [meta, None, meta],
             'units': [None, 'boo', None],
             'long_name': [None, 'boohoo', None]}
        assert self.meta['lower'].units == 'boo'
        assert self.meta['lower'].long_name == 'boohoo'
        assert self.meta['higher'].children == meta

    def test_create_new_metadata_from_old(self):
        meta = pysat.Meta()
        meta['dm'] = {'units': 'hey', 'long_name': 'boo'}
        meta['rpa'] = {'units': 'crazy', 'long_name': 'boo_whoo'}
        self.meta[['higher', 'lower', 'lower2']] = \
            {'meta': [meta, None, meta],
             'units': [None, 'boo', None],
             'long_name': [None, 'boohoo', None],
             'fill': [1, 1, 1],
             'value_min': [0, 0, 0],
             'value_max': [1, 1, 1]}
        meta2 = pysat.Meta(metadata=self.meta.data)
        m1 = meta2['lower']
        m2 = self.meta['lower']
        assert m1['children'] is None
        assert m2['children'] is None
        for key in m1.index:
            if key not in ['children']:
                assert m1[key] == m2[key]
        # make sure both have the same indexes
        assert np.all(m1.index == m2.index)
        # command below doesn't work because 'children' is None
        # assert np.all(meta2['lower'] == self.meta['lower'])

    def test_replace_meta_units_list(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta[['new2', 'new']] = {'units': ['yeppers', 'yep']}
        assert self.meta['new'].units == 'yep'
        assert self.meta['new'].long_name == 'boo'
        assert self.meta['new2'].units == 'yeppers'
        assert self.meta['new2'].long_name == 'boo2'

    def test_meta_csv_load(self):
        name = os.path.join(pysat.__path__[0], 'tests', 'cindi_ivm_meta.txt')
        mdata = pysat.Meta.from_csv(filename=name, na_values=[],
                                    keep_default_na=False,
                                    col_names=['name', 'long_name', 'idx',
                                               'units', 'description'])
        assert mdata['yrdoy'].long_name == 'Date'
        assert (mdata['unit_mer_z'].long_name
                == 'Unit Vector - Meridional Dir - S/C z')
        assert (mdata['iv_mer'].description
                == 'Constructed using IGRF mag field.')

    @pytest.mark.parametrize("bad_key,bad_val,err_msg",
                             [("col_names", [], "col_names must include"),
                              ("filename", None, "Must provide an instrument"),
                              ("filename", 5, "keyword name must be related"),
                              ("filename", 'fake_inst',
                               "keyword name must be related")])
    def test_meta_csv_load_w_errors(self, bad_key, bad_val, err_msg):
        name = os.path.join(pysat.__path__[0], 'tests', 'cindi_ivm_meta.txt')
        kwargs = {'filename': name, 'na_values': [],
                  'keep_default_na': False, 'col_names': None}
        kwargs[bad_key] = bad_val
        with pytest.raises(ValueError) as excinfo:
            pysat.Meta.from_csv(**kwargs)
        assert str(excinfo.value).find('') >= 0

    # assign multiple values to default
    def test_multiple_input_names_null_value(self):
        self.meta[['test1', 'test2']] = {}
        assert self.meta['test1', 'units'] == ''
        assert self.meta['test2', 'long_name'] == 'test2'

    def test_multiple_input_names_null_value_preexisting_values(self):
        self.meta[['test1', 'test2']] = {'units': ['degrees', 'hams'],
                                         'long_name': ['testing', 'further']}
        self.meta[['test1', 'test2']] = {}
        check1 = self.meta['test1', 'units'] == 'degrees'
        check2 = self.meta['test2', 'long_name'] == 'further'
        assert check1 & check2

    # test behaviors related to case changes
    def test_assign_capitalized_labels(self):
        """ Test assignment of capitalized label names
        """
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'Units': 'hey', 'Long_Name': 'boo'}
        self.meta['new2'] = {'Units': 'hey2', 'Long_Name': 'boo2'}

        assert (self.meta['new'].Units == 'hey')
        assert (self.meta['new'].Long_Name == 'boo')
        assert (self.meta['new2'].Units == 'hey2')
        assert (self.meta['new2'].Long_Name == 'boo2')

    def test_assign_Units_no_units(self):
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'Units': 'hey', 'Long_Name': 'boo'}
        with pytest.raises(AttributeError):
            self.meta['new'].units

    def test_get_Units_wrong_case(self):
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'Units': 'hey', 'Long_Name': 'boo'}
        self.meta['new2'] = {'Units': 'hey2', 'Long_Name': 'boo2'}

        assert (self.meta['new', 'units'] == 'hey')
        assert (self.meta['new', 'long_name'] == 'boo')
        assert (self.meta['new2', 'units'] == 'hey2')
        assert (self.meta['new2', 'long_name'] == 'boo2')

    def test_set_Units_wrong_case(self):
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}

        assert self.meta['new'].Units == 'hey'
        assert self.meta['new'].Long_Name == 'boo'
        assert self.meta['new2'].Units == 'hey2'
        assert self.meta['new2'].Long_Name == 'boo2'

    def test_repeated_set_Units_wrong_case(self):
        self.meta = pysat.Meta(labels=self.meta_labels)
        for i in np.arange(10):
            self.meta['new'] = {'units': 'hey%d' % i, 'long_name': 'boo%d' % i}
            self.meta['new_%d' % i] = {'units': 'hey%d' % i,
                                       'long_name': 'boo%d' % i}

        for i in np.arange(10):
            self.meta['new_5'] = {'units': 'hey%d' % i,
                                  'long_name': 'boo%d' % i}
            self.meta['new_%d' % i] = {'units': 'heyhey%d' % i,
                                       'long_name': 'booboo%d' % i}

        assert self.meta['new'].Units == 'hey9'
        assert self.meta['new'].Long_Name == 'boo9'
        assert self.meta['new_9'].Units == 'heyhey9'
        assert self.meta['new_9'].Long_Name == 'booboo9'
        assert self.meta['new_5'].Units == 'hey9'
        assert self.meta['new_5'].Long_Name == 'boo9'

    def test_change_case_of_meta_labels(self):
        """ Test changing case of meta labels after initialization
        """
        self.meta_labels = {'units': ('units', str), 'name': ('long_name', str)}
        self.meta = pysat.Meta(labels=self.meta_labels)
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta.labels.units = 'Units'
        self.meta.labels.name = 'Long_Name'
        assert (self.meta['new'].Units == 'hey')
        assert (self.meta['new'].Long_Name == 'boo')
        assert (self.meta['new2'].Units == 'hey2')
        assert (self.meta['new2'].Long_Name == 'boo2')

    def test_case_change_of_meta_labels_w_ho(self):
        """ Test changing case of meta labels after initialization with HO data
        """
        # Set the initial labels
        self.meta_labels = {'units': ('units', str), 'name': ('long_Name', str)}
        self.meta = pysat.Meta(labels=self.meta_labels)
        meta2 = pysat.Meta(labels=self.meta_labels)

        # Set meta data values
        meta2['new21'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = meta2

        # Change the label name
        self.meta.labels.units = 'Units'
        self.meta.labels.name = 'Long_Name'

        # Evaluate the results in the main data
        assert (self.meta['new'].Units == 'hey')
        assert (self.meta['new'].Long_Name == 'boo')

        # Evaluate the results in the higher order data
        assert (self.meta['new2'].children['new21'].Units == 'hey2')
        assert (self.meta['new2'].children['new21'].Long_Name == 'boo2')

    def test_change_Units_and_Name_case_w_ho_wrong_case(self):
        self.meta_labels = {'units': ('units', str), 'name': ('long_Name', str)}
        self.meta = pysat.Meta(labels=self.meta_labels)
        meta2 = pysat.Meta(labels=self.meta_labels)
        meta2['new21'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = meta2
        self.meta.labels.units = 'Units'
        self.meta.labels.name = 'Long_Name'
        with pytest.raises(AttributeError):
            self.meta['new'].units
        with pytest.raises(AttributeError):
            self.meta['new'].long_name
        with pytest.raises(AttributeError):
            self.meta['new2'].children['new21'].units
        with pytest.raises(AttributeError):
            self.meta['new2'].children['new21'].long_name

    def test_contains_case_insensitive(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        assert ('new2' in self.meta)
        assert ('NEW2' in self.meta)

    def test_contains_case_insensitive_w_ho(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['new21'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta['new2'] = meta2
        assert ('new2' in self.meta)
        assert ('NEW2' in self.meta)
        assert ('new21' not in self.meta)
        assert ('NEW21' not in self.meta)

    def test_get_variable_name_case_preservation(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['NEW2'] = {'units': 'hey2', 'long_name': 'boo2'}

        assert ('NEW2' == self.meta.var_case_name('new2'))
        assert ('NEW2' == self.meta.var_case_name('nEw2'))
        assert ('NEW2' == self.meta.var_case_name('neW2'))
        assert ('NEW2' == self.meta.var_case_name('NEW2'))

    def test_get_attribute_name_case_preservation(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['NEW2'] = {'units': 'hey2', 'long_name': 'boo2',
                             'YoYoYO': 'yolo'}
        self.meta['new'] = {'yoyoyo': 'YOLO'}

        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['new', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2', 'YoYoYO'] == 'yolo')

    def test_get_attribute_name_case_preservation_w_higher_order(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['NEW2'] = meta2
        self.meta['new'] = {'yoyoyo': 'YOLO'}

        assert (self.meta.attr_case_name('YoYoYo') == 'YoYoYO')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['new', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2'].children['new21', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2'].children['new21', 'YoYoYO'] == 'yolo')
        assert (self.meta['new2'].children.attr_case_name('YoYoYo')
                == 'YoYoYO')

    def test_get_attribute_name_case_preservation_w_higher_order_2(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['NEW2'] = meta2
        self.meta['NEW'] = {'yoyoyo': 'YOLO'}

        assert (self.meta.attr_case_name('YoYoYo') == 'YoYoYO')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['NEW', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2'].children['new21', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2'].children['new21', 'YoYoYO'] == 'yolo')
        assert (self.meta['new2'].children.attr_case_name('YoYoYo')
                == 'YoYoYO')

    def test_get_attribute_name_case_preservation_w_ho_reverse_order(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['new'] = {'yoyoyo': 'YOLO'}
        self.meta['NEW2'] = meta2

        assert (self.meta.attr_case_name('YoYoYo') == 'yoyoyo')
        assert (self.meta['new', 'yoyoyo'] == 'YOLO')
        assert (self.meta['new', 'YoYoYO'] == 'YOLO')
        assert (self.meta['new2'].children['new21', 'yoyoyo'] == 'yolo')
        assert (self.meta['new2'].children['new21', 'YoYoYO'] == 'yolo')
        assert (self.meta['new2'].children.attr_case_name('YoYoYo')
                == 'yoyoyo')

    def test_has_attr_name_case_preservation_w_ho_reverse_order(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['new'] = {'yoyoyo': 'YOLO'}
        self.meta['NEW2'] = meta2

        assert (self.meta.hasattr_case_neutral('YoYoYo'))
        assert (self.meta.hasattr_case_neutral('yoyoyo'))
        assert not (self.meta.hasattr_case_neutral('YoYoYyo'))

    def test_has_attr_name_case_preservation_w_higher_order(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta['NEW2'] = meta2

        assert not (self.meta.hasattr_case_neutral('YoYoYo'))
        assert not (self.meta.hasattr_case_neutral('yoyoyo'))
        assert not (self.meta.hasattr_case_neutral('YoYoYyo'))

    # check support on case preservation, but case insensitive
    def test_replace_meta_units_list_weird_case(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['new2'] = {'units': 'hey2', 'long_name': 'boo2'}
        self.meta[['NEW2', 'new']] = {'units': ['yeppers', 'yep']}

        assert (self.meta['new'].units == 'yep')
        assert (self.meta['new'].long_name == 'boo')
        assert (self.meta['new2'].units == 'yeppers')
        assert (self.meta['new2'].long_name == 'boo2')

    def test_transfer_attributes_to_instrument(self):
        """Test transfer of custom meta attributes"""
        self.meta.mutable = True

        # Set non-conflicting attribute
        self.meta.new_attribute = 'hello'
        self.meta.transfer_attributes_to_instrument(self.testInst)

        # Test transferred
        assert self.testInst.new_attribute == 'hello'

        # Ensure transferred attributes are removed
        with pytest.raises(AttributeError):
            self.meta.new_attribute

    def test_transfer_attributes_to_instrument_leading_(self):
        """Ensure private custom meta attributes not transferred"""
        self.meta.mutable = True

        # Set private attributes
        self.meta._yo_yo = 'yo yo'
        self.meta.__yo_yo = 'yo yo'

        # Include standard parameters as well
        self.meta.new_attribute = 'hello'
        self.meta.transfer_attributes_to_instrument(self.testInst)

        # Test private not transferred
        assert not hasattr(self.testInst, "_yo_yo")
        assert not hasattr(self.testInst, "__yo_yo")

        # Check to make sure other values still transferred
        assert self.testInst.new_attribute == 'hello'

        # Ensure private attribute still present
        assert self.meta._yo_yo == 'yo yo'
        assert self.meta.__yo_yo == 'yo yo'

    def test_transfer_attributes_to_instrument_strict_names(self):
        """Test attr transfer with strict_names set to True/False"""
        self.meta.mutable = True

        self.meta.new_attribute = 'hello'
        self.meta._yo_yo = 'yo yo'
        self.meta.jojo_beans = 'yep!'
        self.meta.name = 'Failure!'
        self.meta.date = 'yo yo2'
        self.testInst.load(2009, 1)
        self.testInst.jojo_beans = 'nope!'
        with pytest.raises(RuntimeError):
            self.meta.transfer_attributes_to_instrument(self.testInst,
                                                        strict_names=True)

    def test_transfer_attributes_to_instrument_strict_names_false(self):
        """Test attr transfer with strict_names set to True"""
        self.meta.mutable = True

        self.meta.new_attribute = 'hello'
        self.meta._yo_yo = 'yo yo'
        self.meta.jojo_beans = 'yep!'
        self.meta.name = 'Failure!'
        self.meta.date = 'yo yo2'
        self.testInst.load(2009, 1)
        self.testInst.jojo_beans = 'nope!'
        self.meta.transfer_attributes_to_instrument(self.testInst,
                                                    strict_names=False)
        assert self.testInst.jojo_beans == 'yep!'

    def test_merge_meta(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        meta2 = pysat.Meta()
        meta2['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                          'YoYoYO': 'yolo'}
        self.meta.merge(meta2)

        assert (self.meta['new'].units == 'hey')
        assert (self.meta['new'].long_name == 'boo')
        assert (self.meta['NEW21'].units == 'hey2')
        assert (self.meta['NEW21'].long_name == 'boo2')
        assert (self.meta['NEW21'].YoYoYO == 'yolo')

    def test_drop_meta(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                              'YoYoYO': 'yolo'}
        self.meta.drop(['new'])

        assert not ('new' in self.meta.data.index)
        assert (self.meta['NEW21'].units == 'hey2')
        assert (self.meta['NEW21'].long_name == 'boo2')
        assert (self.meta['NEW21'].YoYoYO == 'yolo')

    def test_keep_meta(self):
        self.meta['new'] = {'units': 'hey', 'long_name': 'boo'}
        self.meta['NEW21'] = {'units': 'hey2', 'long_name': 'boo2',
                              'YoYoYO': 'yolo'}
        self.meta.keep(['new21'])

        assert not ('new' in self.meta.data.index)
        assert (self.meta['NEW21'].units == 'hey2')
        assert (self.meta['NEW21'].long_name == 'boo2')
        assert (self.meta['NEW21'].YoYoYO == 'yolo')

    def test_meta_immutable(self):

        self.meta.mutable = True
        greeting = '...listen!'
        self.meta.hey = greeting
        assert self.meta.hey == greeting

        self.meta.mutable = False
        with pytest.raises(AttributeError):
            self.meta.hey = greeting

    def test_meta_immutable_at_instrument_instantiation(self):
        """Test meta immutable at instrument Instantiation"""

        assert self.testInst.meta.mutable is False

        greeting = '...listen!'
        with pytest.raises(AttributeError):
            self.meta.hey = greeting

    def test_meta_mutable_properties(self):
        """check that @properties are always mutable"""
        self.meta = pysat.Meta()
        self.meta.mutable = False
        self.meta.data = pds.DataFrame()
        self.meta.ho_data = {}
        self.meta.labels.units = 'nT'
        self.meta.labels.name = 'my name'

    def test_nan_metadata_filtered_netcdf4_via_meta_attribute(self):
        """check that metadata set to NaN is excluded from netcdf"""
        # create an instrument object that has a meta with some
        # variables allowed to be nan within metadata when exporting
        self.testInst.load(2009, 1)

        # Normally this parameter would be set at instrument code level
        self.testInst.meta.mutable = True
        self.testInst.meta._export_nan += ['test_nan_export']
        self.testInst.meta.mutable = False

        # Create new variable
        self.testInst['test_nan_variable'] = 1.0

        # Assign additional metadata
        self.testInst.meta['test_nan_variable'] = {'test_nan_export': np.nan,
                                                   'no_nan_export': np.nan,
                                                   'extra_check': 1.}
        # Write the file
        pysat.tests.test_utils.prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        self.testInst.to_netcdf4(outfile)

        # Load file back and test metadata is as expected
        f = netCDF4.Dataset(outfile)

        pysat.tests.test_utils.remove_files(self.testInst)

        assert 'test_nan_export' in f['test_nan_variable'].ncattrs()
        assert 'non_nan_export' not in f['test_nan_variable'].ncattrs()
        assert 'extra_check' in f['test_nan_variable'].ncattrs()

    def test_nan_metadata_filtered_netcdf4_via_method(self):
        """check that metadata set to NaN is excluded from netcdf via nc call"""
        # create an instrument object that has a meta with some
        # variables allowed to be nan within metadata when exporting
        self.testInst.load(2009, 1)

        # Create new variable
        self.testInst['test_nan_variable'] = 1.0

        # Assign additional metadata
        self.testInst.meta['test_nan_variable'] = {'test_nan_export': np.nan,
                                                   'no_nan_export': np.nan,
                                                   'extra_check': 1.}
        # Write the file
        pysat.tests.test_utils.prep_dir(self.testInst)
        outfile = os.path.join(self.testInst.files.data_path,
                               'pysat_test_ncdf.nc')
        export_nan = self.testInst.meta._export_nan + ['test_nan_export']
        self.testInst.to_netcdf4(outfile, export_nan=export_nan)

        # Load file back and test metadata is as expected
        f = netCDF4.Dataset(outfile)

        pysat.tests.test_utils.remove_files(self.testInst)

        assert 'test_nan_export' in f['test_nan_variable'].ncattrs()
        assert 'non_nan_export' not in f['test_nan_variable'].ncattrs()
        assert 'extra_check' in f['test_nan_variable'].ncattrs()


class TestBasicsImmutable(TestBasics):
    def setup(self):
        """Runs before every method to create a clean testing setup
        """

        # Instrument object and disable mutability
        self.testInst = pysat.Instrument('pysat', 'testing',
                                         clean_level='clean')
        self.stime = pysat.instruments.pysat_testing._test_dates['']['']
        self.meta = self.testInst.meta
        self.meta.mutable = False
        self.meta_labels = {'units': ('Units', str),
                            'name': ('Long_Name', str)}

        # Assign remaining values
        self.dval = None
        self.out = None
        self.default_name = ['long_name']
        self.default_nan = ['fill', 'value_min', 'value_max']
        self.default_val = {'notes': '', 'units': '', 'desc': ''}
        self.frame_list = ['dummy_frame1', 'dummy_frame2']

    def teardown(self):
        """Runs after every method to clean up previous testing
        """
        del self.testInst, self.meta, self.out, self.stime, self.meta_labels
        del self.default_name, self.default_nan, self.default_val, self.dval
        del self.frame_list
