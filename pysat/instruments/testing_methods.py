import numpy as np


def generate_fake_data(t0, num_array, period=5820, data_range=24.0,
                       cyclic=True):
    """Generates fake data over a given range

    Parameters
    ----------
    t0 : float
        Start time in seconds
    num_array : array_like
        Array of time steps from t0.  This is the index of the fake data
    period : int
        The number of seconds per period.
        (default = 5820)
    data_range : float
        For cyclic functions, the range of data values cycled over one period.
        Not used for non-cyclic functions.
        (default = 24.0)
    cyclic : bool
    """

    if cyclic:
        uts_root = np.mod(t0, period)
        data = (np.mod(uts_root + num_array, period)
                * (data_range / float(period)))
    else:
        data = ((t0 + num_array) / period).astype(int)

    return data
