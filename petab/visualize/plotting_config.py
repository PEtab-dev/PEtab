"""Plotting config"""
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.ticker as mtick

from ..C import *


def plot_lowlevel(vis_spec: pd.DataFrame,
                  ax: np.ndarray,
                  axx: int,
                  axy: int,
                  conditions: pd.Series,
                  ms: pd.DataFrame,
                  ind_plot: pd.Series,
                  i_visu_spec: int,
                  plot_sim: bool):
    """
    plotting routine / preparations: set properties of figure and plot
    the data with given specifications (lineplot with errorbars, or barplot)

    Parameters
    ----------

    vis_spec:
        pandas data frame, contains defined data format (visualization file)
    ax:
        np.ndarray, matplotlib.Axes
    axx:
        int, subplot axis indices for x
    axy:
        int, subplot axis indices for y
    conditions:
        pd.Series, Values on x-axis
    ms:
        pd.DataFrame,  containing measurement data which should be plotted
    ind_plot:
        pd.Series, boolean vector, with size:
        len(rows in visualization file) x 1
        with 'True' entries for rows which should be plotted
    i_visu_spec:
        int64, current index (row number) of row which should be plotted in
        visualizationSpecification file
    plot_sim:
        bool, tells whether or not simulated data should be plotted as well

    Returns
    -------
    ax: matplotlib.Axes
    """

    # set xScale
    if vis_spec[X_SCALE][i_visu_spec] == LIN:
        ax[axx, axy].set_xscale("linear")
    elif vis_spec[X_SCALE][i_visu_spec] == LOG10:
        ax[axx, axy].set_xscale("log")
    elif vis_spec.xScale[i_visu_spec] == LOG:
        ax[axx, axy].set_xscale("log", basex=np.e)

    # set yScale
    if vis_spec.yScale[i_visu_spec] == LIN:
        ax[axx, axy].set_yscale("linear")
    elif vis_spec.yScale[i_visu_spec] == LOG10:
        ax[axx, axy].set_yscale("log")
    elif vis_spec.yScale[i_visu_spec] == LOG:
        ax[axx, axy].set_yscale("log", basey=np.e)

    # set type of noise
    if vis_spec[PLOT_TYPE_DATA][i_visu_spec] == MEAN_AND_SD:
        noise_col = 'sd'
    elif vis_spec[PLOT_TYPE_DATA][i_visu_spec] == MEAN_AND_SEM:
        noise_col = 'sem'
    elif vis_spec[PLOT_TYPE_DATA][i_visu_spec] == PROVIDED:
        noise_col = 'noise_model'

    if vis_spec.plotTypeSimulation[i_visu_spec] == LINE_PLOT:

        # equidistant
        if vis_spec[X_SCALE][i_visu_spec] == 'order':
            ax[axx, axy].set_xscale("linear")
            # check if conditions are monotone decreasing or increasing
            if np.all(np.diff(conditions) < 0):             # monot. decreasing
                xlabel = conditions[::-1]                   # reversing
                conditions = range(len(conditions))[::-1]   # reversing
                ax[axx, axy].set_xticks(range(len(conditions)), xlabel)
            elif np.all(np.diff(conditions) > 0):
                xlabel = conditions
                conditions = range(len(conditions))
                ax[axx, axy].set_xticks(range(len(conditions)), xlabel)
            else:
                raise ValueError('Error: x-conditions do not coincide, '
                                 'some are mon. increasing, some monotonically'
                                 ' decreasing')

        # add xOffset
        conditions = conditions + vis_spec[X_OFFSET][i_visu_spec]

        # TODO sort mean and sd/sem by x values (as for simulatedData below)
        #  to avoid crazy lineplots in case x values are not sorted by default.
        #  cf issue #207
        # plotting all measurement data
        label_base = vis_spec[ind_plot][LEGEND_ENTRY][i_visu_spec]
        if vis_spec[PLOT_TYPE_DATA][i_visu_spec] == REPLICATE:
            p = ax[axx, axy].plot(
                conditions[conditions.index.values],
                ms.repl[ms.repl.index.values], 'x',
                label=label_base)

        # construct errorbar-plots: noise specified above
        else:
            p = ax[axx, axy].errorbar(
                conditions, ms['mean'], ms[noise_col],
                linestyle='-.', marker='.', label=label_base)
        # construct simulation plot
        colors = p[0].get_color()
        if plot_sim:
            xs, ys = zip(*sorted(zip(conditions, ms['sim'])))
            ax[axx, axy].plot(
                xs, ys, linestyle='-', marker='o',
                label=label_base + " simulation", color=colors)

    # construct bar plot
    elif vis_spec[PLOT_TYPE_SIMULATION][i_visu_spec] == BAR_PLOT:
        x_name = vis_spec[ind_plot][LEGEND_ENTRY][i_visu_spec]
        ind_bars = vis_spec[ind_plot][PLOT_TYPE_SIMULATION] == BAR_PLOT
        x_names = list(vis_spec[ind_plot][ind_bars][LEGEND_ENTRY])
        p = ax[axx, axy].bar(x_name, ms['mean'], yerr=ms[noise_col],
                             color=sns.color_palette()[0], width=2/3)
        legend = ['measurement']
        tick_factor = 1
        tick_offset = 0

        if plot_sim:
            colors = p[0].get_facecolor()
            ax[axx, axy].bar(x_name + " simulation", ms['sim'], color='white',
                             width=-2/3, align='edge', edgecolor=colors)
            legend.append('simulation')
            tick_factor = 2
            tick_offset = 1/3

        x_ticks = tick_factor * np.linspace(0, len(x_names) - 1,
                                            len(x_names)) + tick_offset
        ax[axx, axy].set_xticks(x_ticks)
        ax[axx, axy].set_xticklabels(x_names)

        for label in ax[axx, axy].get_xmajorticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment("right")

        ax[axx, axy].legend(legend)

    # construct scatter plot
    elif vis_spec[PLOT_TYPE_SIMULATION][i_visu_spec] == SCATTER_PLOT:
        if not plot_sim:
            raise NotImplementedError('Scatter plots do not work without'
                                      ' simulation data')
        ax[axx, axy].scatter(ms['mean'], ms['sim'],
                             label=vis_spec[ind_plot][LEGEND_ENTRY][
                                 i_visu_spec])
        ax[axx, axy] = square_plot_equal_ranges(ax[axx, axy])

    # show 'e' as basis not 2.7... in natural log scale cases
    def ticks(y, _):
        return r'$e^{{{:.0f}}}$'.format(np.log(y))
    if vis_spec.xScale[i_visu_spec] == LOG:
        ax[axx, axy].xaxis.set_major_formatter(mtick.FuncFormatter(ticks))
    if vis_spec.yScale[i_visu_spec] == LOG:
        ax[axx, axy].yaxis.set_major_formatter(mtick.FuncFormatter(ticks))

    # set further plotting/layout settings

    if not vis_spec[PLOT_TYPE_SIMULATION][i_visu_spec] == BAR_PLOT:
        ax[axx, axy].legend()
    ax[axx, axy].set_title(vis_spec[PLOT_NAME][i_visu_spec])
    ax[axx, axy].relim()
    ax[axx, axy].autoscale_view()

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
