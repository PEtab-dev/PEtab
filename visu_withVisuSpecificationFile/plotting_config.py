import numpy as np
import pandas as pd


def plotting_config(visualization_specification: pd.DataFrame,
                    ax: np.ndarray,
                    axx: int,
                    axy: int,
                    conditions: pd.Series,
                    ms: pd.DataFrame,
                    ind_plot: pd.Series,
                    i_visu_spec: int,
                    plt):
    """
    plotting routine / preparations: set properties of figure and plot
    the data with given specifications (lineplot with errorbars, or barplot)

    Parameters:
    ----------

    visualization_specification:
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
        pd.Series, boolean vector, with size: len(rows in visualization file) x 1
        with 'True' entries for rows which should be plotted
    i_visu_spec:
        int64, current index (row number) of row which should be plotted in
        visualizationSpecification file
    plt:
        module matplotlib.pyplot

    Return:
    ----------
    ax: matplotlib.Axes
    """

    if visualization_specification.plotTypeSimulation[i_visu_spec] == 'LinePlot':

        # set xScale
        if visualization_specification.xScale[i_visu_spec] == 'lin':
            ax[axx, axy].set_xscale("linear")
        elif visualization_specification.xScale[i_visu_spec] == 'log10':
            ax[axx, axy].set_xscale("log")
        # equidistant
        elif visualization_specification.xScale[i_visu_spec] == 'order':
            ax[axx, axy].set_xscale("linear")
            # check if conditions are monotone decreasing or increasing
            if np.all(np.diff(conditions) < 0):             # monotone decreasing
                xlabel = conditions[::-1]                   # reversing
                conditions = range(len(conditions))[::-1]   # reversing
                ax[axx, axy].set_xticks(range(len(conditions)), xlabel)
            elif np.all(np.diff(conditions) > 0):
                xlabel = conditions
                conditions = range(len(conditions))
                ax[axx, axy].set_xticks(range(len(conditions)), xlabel)
            else:
                raise ValueError('Error: x-conditions do not coincide, some are'
                                 ' mon. increasing, some monotonically decreasing')

        # add xOffset
        conditions = conditions + \
            visualization_specification.xOffset[i_visu_spec]

        # construct errorbar-plots
        if visualization_specification.plotTypeData[i_visu_spec] == 'MeanAndSD':
            p = ax[axx, axy].errorbar(
                conditions, ms['mean'], ms['sd'], linestyle='-', marker='.',
                label=visualization_specification[ind_plot].legendEntry[i_visu_spec])
            colors = p[0].get_color()
            if plt.plot_simulation:
                ax[axx, axy].plot(
                    conditions, ms['sim'], linestyle='-.', marker='o',
                    label=visualization_specification[ind_plot]
                    .legendEntry[i_visu_spec]
                    + " simulation", color=colors)
        elif visualization_specification.plotTypeData[i_visu_spec] == 'MeanAndSEM':
            ax[axx, axy].errorbar(
                conditions, ms['mean'], ms['sem'], linestyle='-', marker='.',
                label=visualization_specification[ind_plot].legendEntry[i_visu_spec])
        # plotting all measurement data
        elif visualization_specification.plotTypeData[i_visu_spec] == 'replicate':
            for ii in range(0, len(ms['repl'])):
                for k in range(0, len(ms.repl[ii])):
                    ax[axx, axy].plot(
                        conditions[conditions.index.values[ii]],
                        ms.repl[ii][ms.repl[ii].index.values[k]], 'x')
        ax[axx, axy].legend()
        ax[axx, axy].set_title(
            visualization_specification.plotName[i_visu_spec])

    elif visualization_specification.plotTypeSimulation[i_visu_spec] == 'BarPlot':

        x_name = visualization_specification[ind_plot].legendEntry[i_visu_spec]

        ax[axx, axy].bar(x_name, ms['mean'], yerr=ms['sd'])
        ax[axx, axy].set_title(
            visualization_specification.plotName[i_visu_spec])

    return ax
