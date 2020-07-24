def computational_form(data):
    """
    Repackages numbers, Series, or DataFrames

    .. deprecated:: 2.2.0
      `computational_form` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Regardless of input format, mathematical operations may be performed on the
    output via the same pandas mechanisms.

    This method may be particularly useful in analysis methods that aim to be
    instrument independent. pysat.Instrument objects can package data in a
    variety of ways within a DataFrame, depending upon the scientific data
    source. Thus, a variety of data types will be encountered by instrument
    independent methods and computational_form method may reduce the effort
    required to support more generalized processing.

    Parameters
    ----------
    data : pandas.Series
        Series of numbers, Series, DataFrames

    Returns
    -------
    pandas.Series, DataFrame, or Panel
        repacked data, aligned by indices, ready for calculation
    """

    from pysat import DataFrame, Series, Panel
    import warnings

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    if isinstance(data.iloc[0], DataFrame):
        dslice = Panel.from_dict(dict([(i, data.iloc[i])
                                       for i in range(len(data))]))
    elif isinstance(data.iloc[0], Series):
        dslice = DataFrame(data.tolist())
        dslice.index = data.index
    else:
        dslice = data
    return dslice
