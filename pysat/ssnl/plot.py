from __future__ import print_function
from __future__ import absolute_import

import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import warnings

from pysat import logger

def scatterplot(inst, labelx, labely, data_label, datalim, xlim=None,
                ylim=None):
    """Return scatterplot of data_label(s) as functions of labelx,y over a
    season.

    .. deprecated:: 2.2.0
      `scatterplot` will be removed in pysat 3.0.0, it will
      be added to pysatSeasons

    Parameters
    ----------
    labelx : string
        data product for x-axis
    labely : string
        data product for y-axis
    data_label : string, array-like of strings
        data product(s) to be scatter plotted
    datalim : numyp array
        plot limits for data_label

    Returns
    -------
    Returns a list of scatter plots of data_label as a function
    of labelx and labely over the season delineated by start and
    stop datetime objects.

    """

    warnings.warn(' '.join(["This function is deprecated here and will be",
                            "removed in pysat 3.0.0. Please use",
                            "pysatSeasons instead:"
                            "https://github.com/pysat/pysatSeasons"]),
                  DeprecationWarning, stacklevel=2)

    if mpl.is_interactive():
        interactive_mode = True
        # turn interactive plotting off
        plt.ioff()
    else:
        interactive_mode = False

    # create figures for plotting
    figs = []
    axs = []

    # Check for list-like behaviour of data_label
    if type(data_label) is str:
        data_label = [data_label]

    # multiple data to be plotted
    for i in np.arange(len(data_label)):
        figs.append(plt.figure())
        ax1 = figs[i].add_subplot(211, projection='3d')
        ax2 = figs[i].add_subplot(212)
        axs.append((ax1, ax2))
        plt.suptitle(data_label[i])
        if xlim is not None:
            ax1.set_xlim(xlim)
            ax2.set_xlim(xlim)
        if ylim is not None:
            ax1.set_ylim(ylim)
            ax2.set_ylim(ylim)

    # norm method so that data may be scaled to colors appropriately
    norm = mpl.colors.Normalize(vmin=datalim[0], vmax=datalim[1])
    p = [i for i in np.arange(len(figs))]
    q = [i for i in np.arange(len(figs))]
    for i, inst in enumerate(inst):
        for j, (fig, ax) in enumerate(zip(figs, axs)):
            if not inst.empty:
                check1 = len(inst.data[labelx]) > 0
                check2 = len(inst.data[labely]) > 0
                check3 = len(inst.data[data_label[j]]) > 0
                if (check1 & check2 & check3):
                    p[j] = ax[0].scatter(inst.data[labelx], inst.data[labely],
                                         inst.data[data_label[j]], zdir='z',
                                         c=inst.data[data_label[j]], norm=norm,
                                         linewidth=0, edgecolors=None)
                    q[j] = ax[1].scatter(inst.data[labelx], inst.data[labely],
                                         c=inst.data[data_label[j]],
                                         norm=norm, alpha=0.5, edgecolor=None)

    for j, (fig, ax) in enumerate(zip(figs, axs)):
        try:
            plt.colorbar(p[j], ax=ax[0], label='Amplitude (m/s)')
        except:
            logger.info('Tried colorbar but failed, thus no colorbar.')
        ax[0].elev = 30.

    if interactive_mode:
        # turn interactive plotting back on
        plt.ion()

    return figs
