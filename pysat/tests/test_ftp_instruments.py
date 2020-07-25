"""
tests the pysat meta object and code for instruments with ftp downloads.

Intended to be run locally, excluded from Travis CI
"""
from importlib import import_module
import os
import tempfile

import pysat
import pysat.instruments.pysat_testing
import pysat.tests.test_instruments as test_inst

include_list = ['icon_euv', 'icon_fuv', 'icon_ivm', 'icon_might', 'sw_dst']
# dict, keyed by pysat instrument, with a list of usernames and passwords
user_download_dict = {}


def init_func_external(self):
    """Iterate through and create all of the test Instruments needed.
       Only want to do this once.

    """

    # names of all the instrument modules
    instrument_names = pysat.instruments.__all__
    temp = []
    for name in instrument_names:
        if name in include_list:
            temp.append(name)
    instrument_names = temp
    self.instrument_names = temp
    self.instruments = []
    self.instrument_modules = []

    # create temporary directory
    dir_name = tempfile.mkdtemp()
    saved_path = pysat.data_dir
    pysat.utils.set_data_dir(dir_name, store=False)

    for name in instrument_names:
        try:
            print(' '.join(('FTP', name)))
            module = import_module(''.join(('.', name)),
                                   package='pysat.instruments')
        except ImportError:
            print("Couldn't import instrument module")
            pass
        else:
            # try and grab basic information about the module so we
            # can iterate over all of the options
            try:
                info = module._test_dates
            except AttributeError:
                info = {}
                info[''] = {'': pysat.datetime(2009, 1, 1)}
                module._test_dates = info
            for sat_id in info.keys():
                for tag in info[sat_id].keys():
                    try:
                        inst = pysat.Instrument(inst_module=module,
                                                tag=tag,
                                                sat_id=sat_id,
                                                temporary_file_list=True)
                        inst._test_dates = module._test_dates
                        self.instruments.append(inst)
                        self.instrument_modules.append(module)
                    except:
                        pass
    pysat.utils.set_data_dir(saved_path, store=False)


init_inst = None
init_mod = None
init_names = None

# this environment variable is set by the TRAVIS CI folks
if not (os.environ.get('TRAVIS') == 'true'):
    class TestFTPInstrumentQualifier(test_inst.TestInstrumentQualifier):

        def __init__(self):
            """Iterate through and create all of the test Instruments needed"""
            global init_inst
            global init_mod
            global init_names

            if init_inst is None:
                init_func_external(self)
                init_inst = self.instruments
                init_mod = self.instrument_modules
                init_names = self.instrument_names

            else:
                self.instruments = init_inst
                self.instrument_modules = init_mod
                self.instrument_names = init_names

        def setup(self):
            """Runs before every method to create a clean testing setup."""
            pass

        def teardown(self):
            """Runs after every method to clean up previous testing."""
            pass
