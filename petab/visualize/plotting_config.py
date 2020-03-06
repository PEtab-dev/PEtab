"""Plotting config"""
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.ticker as mtick

from ..C import *


def plot_lowlevel(plot_spec: pd.Series,
                  ax: 'matplotlib.pyplot.Axes',
                  conditions: pd.Series,
                  ms: pd.DataFrame,
                  plot_sim: bool):
    """
    plotting routine / preparations: set properties of figure and plot
    the data with given specifications (lineplot with errorbars, or barplot)

    Parameters
    ----------

    plot_spec:
        contains defined data format (visualization file)
    ax:
        axes to which to plot
    conditions:
        pd.Series, Values on x-axis
    ms:
        pd.DataFrame,  containing measurement data which should be plotted
    plot_sim:
        bool, tells whether or not simulated data should be plotted as well
    """

    # set yScale
    if plot_spec[Y_SCALE] == LIN:
        ax.set_yscale("linear")
    elif plot_spec[Y_SCALE] == LOG10:
        ax.set_yscale("log")
    elif plot_spec[Y_SCALE] == LOG:
        ax.set_yscale("log", basey=np.e)

    # set type of noise
    if plot_spec[PLOT_TYPE_DATA] == MEAN_AND_SD:
        noise_col = 'sd'
    elif plot_spec[PLOT_TYPE_DATA] == MEAN_AND_SEM:
        noise_col = 'sem'
    elif plot_spec[PLOT_TYPE_DATA] == PROVIDED:
        noise_col = 'noise_model'

    if plot_spec.plotTypeSimulation == LINE_PLOT:

        # set xScale
        if plot_spec[X_SCALE] == LIN:
            ax.set_xscale("linear")
        elif plot_spec[X_SCALE] == LOG10:
            ax.set_xscale("log")
        elif plot_spec[X_SCALE] == LOG:
            ax.set_xscale("log", basex=np.e)
        # equidistant
        elif plot_spec[X_SCALE] == 'order':
            ax.set_xscale("linear")
            # check if conditions are monotone decreasing or increasing
            if np.all(np.diff(conditions) < 0):             # monot. decreasing
                xlabel = conditions[::-1]                   # reversing
                conditions = range(len(conditions))[::-1]   # reversing
                ax.set_xticks(range(len(conditions)), xlabel)
            elif np.all(np.diff(conditions) > 0):
                xlabel = conditions
                conditions = range(len(conditions))
                ax.set_xticks(range(len(conditions)), xlabel)
            else:
                raise ValueError('Error: x-conditions do not coincide, '
                                 'some are mon. increasing, some monotonically'
                                 ' decreasing')

        # add xOffset
        conditions = conditions + plot_spec[X_OFFSET]

        # TODO sort mean and sd/sem by x values (as for simulatedData below)
        #  to avoid crazy lineplots in case x values are not sorted by default.
        #  cf issue #207
        # plotting all measurement data
        label_base = plot_spec[LEGEND_ENTRY]
        if plot_spec[PLOT_TYPE_DATA] == REPLICATE:
            p = ax.plot(
                conditions[conditions.index.values],
                ms.repl[ms.repl.index.values], 'x',
                label=label_base
            )

        # construct errorbar-plots: noise specified above
        else:
            p = ax.errorbar(
                conditions, ms['mean'], ms[noise_col],
                linestyle='-.', marker='.', label=label_base
            )
        # construct simulation plot
        colors = p[0].get_color()
        if plot_sim:
            xs, ys = zip(*sorted(zip(conditions, ms['sim'])))
            ax.plot(
                xs, ys, linestyle='-', marker='o',
                label=label_base + " simulation", color=colors
            )

    # construct bar plot
    elif plot_spec[PLOT_TYPE_SIMULATION] == BAR_PLOT:
        x_name = plot_spec[LEGEND_ENTRY]

        if plot_sim:
            bar_kwargs = {
                'align': 'edge',
                'width': -1/3,
            }
        else:
            bar_kwargs = {
                'align': 'center',
                'width': 2/3,
            }

        p = ax.bar(x_name, ms['mean'], yerr=ms[noise_col],
                   color=sns.color_palette()[0], **bar_kwargs)

        if plot_sim:
            colors = p[0].get_facecolor()
            bar_kwargs['width'] = -bar_kwargs['width']
            ax.bar(x_name, ms['sim'], color='white',
                   edgecolor=colors, **bar_kwargs)

    # construct scatter plot
    elif plot_spec[PLOT_TYPE_SIMULATION] == SCATTER_PLOT:
        if not plot_sim:
            raise NotImplementedError('Scatter plots do not work without'
                                      ' simulation data')
        ax.scatter(ms['mean'], ms['sim'],
                   label=plot_spec[LEGEND_ENTRY])
        ax = square_plot_equal_ranges(ax)

    # show 'e' as basis not 2.7... in natural log scale cases
    def ticks(y, _):
        return r'$e^{{{:.0f}}}$'.format(np.log(y))
    if plot_spec[X_SCALE] == LOG:
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(ticks))
    if plot_spec[Y_SCALE] == LOG:
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(ticks))

    # set further plotting/layout settings

    if not plot_spec[PLOT_TYPE_SIMULATION] == BAR_PLOT:
        ax.legend()
    ax.set_title(plot_spec[PLOT_NAME])
    ax.relim()
    ax.autoscale_view()

    return ax


def square_plot_equal_ranges(ax, lim=None):
    """Square plot with equal range for scatter plots"""

    ax.axis('square')

    if lim is None:
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        lim = [np.min([xlim[0], ylim[0]]),
               np.max([xlim[1], ylim[1]])]

    ax.set_xlim(lim)
    ax.set_ylim(lim)

    # Same tick mark on x and y
    ax.yaxis.set_major_locator(ax.xaxis.get_major_locator())

    return ax
