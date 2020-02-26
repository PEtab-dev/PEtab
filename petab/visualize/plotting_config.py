"""Plotting config"""
import numpy as np
import pandas as pd
import seaborn as sns

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
    if plot_spec.yScale == 'lin':
        ax.set_yscale("linear")
    elif plot_spec.yScale == 'log10':
        ax.set_yscale("log")

    if plot_spec.plotTypeSimulation == LINE_PLOT:

        # set xScale
        if plot_spec[X_SCALE] == LIN:
            ax.set_xscale("linear")
        elif plot_spec[X_SCALE] == LOG10:
            ax.set_xscale("log")
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
        #
        # construct errorbar-plots: Mean and standard deviation
        label_base = plot_spec[LEGEND_ENTRY]
        if plot_spec[PLOT_TYPE_DATA] == MEAN_AND_SD:
            p = ax.errorbar(
                conditions, ms['mean'], ms['sd'], linestyle='-.', marker='.',
                label=label_base)

        # construct errorbar-plots: Mean and standard error of mean
        elif plot_spec[PLOT_TYPE_DATA] == MEAN_AND_SEM:
            p = ax.errorbar(
                conditions, ms['mean'], ms['sem'], linestyle='-.', marker='.',
                label=label_base)

        # plotting all measurement data
        elif plot_spec[PLOT_TYPE_DATA] == REPLICATE:
            p = ax.plot(
                conditions[conditions.index.values],
                ms.repl[ms.repl.index.values], 'x',
                label=label_base)

        # construct errorbar-plots: Mean and noise provided in measurement file
        elif plot_spec[PLOT_TYPE_DATA] == PROVIDED:
            p = ax.errorbar(
                conditions, ms['mean'], ms['noise_model'],
                linestyle='-.', marker='.', label=label_base)
        # construct simulation plot
        colors = p[0].get_color()
        if plot_sim:
            xs, ys = zip(*sorted(zip(conditions, ms['sim'])))
            ax.plot(
                xs, ys, linestyle='-', marker='o',
                label=label_base + " simulation", color=colors)

        ax.legend()
        ax.set_title(plot_spec[PLOT_NAME])

    elif plot_spec[PLOT_TYPE_SIMULATION] == BAR_PLOT:
        x_name = plot_spec[LEGEND_ENTRY]

        p = ax.bar(x_name, ms['mean'], yerr=ms['sd'],
                   color=sns.color_palette()[0])
        ax.set_title(plot_spec[PLOT_NAME])

        if plot_sim:
            colors = p[0].get_facecolor()
            ax.bar(x_name + " simulation", ms['sim'], color='white',
                   edgecolor=colors)
    ax.relim()
    ax.autoscale_view()
