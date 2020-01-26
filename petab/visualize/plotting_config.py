"""Plotting config"""
import numpy as np
import pandas as pd

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

    if vis_spec[PLOT_TYPE_SIMULATION][i_visu_spec] == LINE_PLOT:

        # set xScale
        if vis_spec[X_SCALE][i_visu_spec] == LIN:
            ax[axx, axy].set_xscale("linear")
        elif vis_spec[X_SCALE][i_visu_spec] == LOG10:
            ax[axx, axy].set_xscale("log")
        # equidistant
        elif vis_spec[X_SCALE][i_visu_spec] == 'order':
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
        #
        # construct errorbar-plots: Mean and standard deviation
        label_base = vis_spec[ind_plot][LEGEND_ENTRY][i_visu_spec]
        if vis_spec[PLOT_TYPE_DATA][i_visu_spec] == MEAN_AND_SD:
            p = ax[axx, axy].errorbar(
                conditions, ms['mean'], ms['sd'], linestyle='-.', marker='.',
                label=label_base)

        # construct errorbar-plots: Mean and standard error of mean
        elif vis_spec[PLOT_TYPE_DATA][i_visu_spec] == MEAN_AND_SEM:
            p = ax[axx, axy].errorbar(
                conditions, ms['mean'], ms['sem'], linestyle='-.', marker='.',
                label=label_base)

        # plotting all measurement data
        elif vis_spec[PLOT_TYPE_DATA][i_visu_spec] == REPLICATE:
            p = ax[axx, axy].plot(
                conditions[conditions.index.values],
                ms.repl[ms.repl.index.values], 'x',
                label=label_base)

        # construct errorbar-plots: Mean and noise provided in measurement file
        elif vis_spec[PLOT_TYPE_DATA][i_visu_spec] == PROVIDED:
            p = ax[axx, axy].errorbar(
                conditions, ms['mean'], ms['noise_model'],
                linestyle='-.', marker='.', label=label_base)
        # construct simulation plot
        colors = p[0].get_color()
        if plot_sim:
            xs, ys = zip(*sorted(zip(conditions, ms['sim'])))
            ax[axx, axy].plot(
                xs, ys, linestyle='-', marker='o',
                label=label_base + " simulation", color=colors)

        ax[axx, axy].legend()
        ax[axx, axy].set_title(vis_spec[PLOT_NAME][i_visu_spec])

    elif vis_spec[PLOT_TYPE_SIMULATION][i_visu_spec] == BAR_PLOT:

        x_name = vis_spec[ind_plot][LEGEND_ENTRY][i_visu_spec]

        p = ax[axx, axy].bar(x_name, ms['mean'], yerr=ms['sd'])
        ax[axx, axy].set_title(vis_spec[PLOT_NAME][i_visu_spec])

        if plot_sim:
            colors = p[0].get_facecolor()
            ax[axx, axy].bar(x_name + " simulation", ms['sim'], color='white',
                             edgecolor=colors)

    return ax
