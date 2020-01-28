"""Functions for plotting PEtab measurement files and simulation results in
the same format."""

from typing import Union, Optional, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .helper_functions import (get_default_vis_specs,
                               create_figure,
                               handle_dataset_plot)

from .. import problem, measurements, core, conditions
from ..C import *

# for typehints
IdsList = List[str]
NumList = List[int]


def plot_data_and_simulation(
        exp_data: Union[str, pd.DataFrame],
        exp_conditions: Union[str, pd.DataFrame],
        vis_spec: Optional[Union[str, pd.DataFrame]] = '',
        sim_data: Optional[Union[str, pd.DataFrame]] = None,
        dataset_id_list: Optional[List[IdsList]] = None,
        sim_cond_id_list: Optional[List[IdsList]] = None,
        sim_cond_num_list: Optional[List[NumList]] = None,
        observable_id_list: Optional[List[IdsList]] = None,
        observable_num_list: Optional[List[NumList]] = None,
        plotted_noise: Optional[str] = MEAN_AND_SD,
        subplot_file_path: str = ''):
    """
    Main function for plotting data and simulations.

    What exactly should be plotted is specified in a
    visualizationSpecification.tsv file.

    Also, the data, simulations and conditions have
    to be defined in a specific format
    (see "doc/documentation_data_format.md").

    Parameters
    ----------
    exp_data:
        measurement DataFrame in the PEtab format or path to the data file.
    exp_conditions:
        condition DataFrame in the PEtab format or path to the condition file.
    vis_spec: str or pandas.Dataframe (optional)
        Visualization specification DataFrame in the PEtab format or path to
         visualization file.
    sim_data:
        simulation DataFrame in the PEtab format
        or path to the simulation output data file.
    dataset_id_list:
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the datasetIds for this plot.
        Only to be used if no visualization file was available.
    sim_cond_id_list:
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the simulationConditionIds for this plot.
        Only to be used if no visualization file was available.
    sim_cond_num_list:
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the numbers corresponding to the simulationConditionIds for
        this plot.
        Only to be used if no visualization file was available.
    observable_id_list:
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the observableIds for this plot.
        Only to be used if no visualization file was available.
    observable_num_list:
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the numbers corresponding to the observableIds for
        this plot.
        Only to be used if no visualization file was available.
    plotted_noise:
        String indicating how noise should be visualized:
        ['MeanAndSD' (default), 'MeanAndSEM', 'replicate', 'provided']
    subplot_file_path:
        String which is taken as file path to which single subplots are saved.
        PlotIDs will be taken as file names.

    Returns
    -------
    ax: Axis object of the created plot.
    None: In case subplots are save to file
    """

    if isinstance(exp_data, str):
        # import from file
        exp_data = measurements.get_measurement_df(exp_data)

    if isinstance(exp_conditions, str):
        exp_conditions = conditions.get_condition_df(exp_conditions)

    # import visualization specification, if file was specified
    if isinstance(vis_spec, str):
        if vis_spec != '':
            vis_spec = core.get_visualization_df(vis_spec)
        else:
            # create them based on simulation conditions
            vis_spec, exp_data = get_default_vis_specs(exp_data,
                                                       exp_conditions,
                                                       dataset_id_list,
                                                       sim_cond_id_list,
                                                       sim_cond_num_list,
                                                       observable_id_list,
                                                       observable_num_list,
                                                       plotted_noise)

    # import simulation file, if file was specified
    if isinstance(sim_data, str):
        sim_data = core.get_simulation_df(sim_data)

    # get unique plotIDs
    uni_plot_ids, _ = np.unique(vis_spec[PLOT_ID], return_index=True)

    # Switch saving plots to file on or get axes
    plots_to_file = False
    if subplot_file_path != '':
        plots_to_file = True
    else:
        fig, ax, _, num_col = create_figure(uni_plot_ids, plots_to_file)

    # loop over unique plotIds
    for i_plot_id, var_plot_id in enumerate(uni_plot_ids):

        if plots_to_file:
            fig, ax, _, num_col = create_figure(uni_plot_ids,
                                                plots_to_file)
            i_row = 0
            i_col = 0
        else:
            # setting axis indices
            i_row = int(np.ceil((i_plot_id + 1) / num_col)) - 1
            i_col = int(((i_plot_id + 1) - i_row * num_col)) - 1

        # get indices for specific plotId
        ind_plot = (vis_spec[PLOT_ID] == var_plot_id)

        # loop over datsets
        for i_visu_spec in vis_spec[ind_plot].index.values:
            # handle plot of current dataset
            ax = handle_dataset_plot(i_visu_spec, ind_plot, ax, i_row, i_col,
                                     exp_data, exp_conditions, vis_spec,
                                     sim_data)
        if plots_to_file:
            sns.despine()
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(f'{subplot_file_path}/{var_plot_id}.png')
            plt.close()

    # finalize figure
    if not plots_to_file:
        fig.tight_layout()
        sns.despine()
        return ax

    return None


def plot_petab_problem(petab_problem: problem.Problem,
                       sim_data: Optional[Union[str, pd.DataFrame]] = None,
                       dataset_id_list: Optional[List[IdsList]] = None,
                       sim_cond_id_list: Optional[List[IdsList]] = None,
                       sim_cond_num_list: Optional[List[NumList]] = None,
                       observable_id_list: Optional[List[IdsList]] = None,
                       observable_num_list: Optional[List[NumList]] = None,
                       plotted_noise: Optional[str] = MEAN_AND_SD,):
    """
    Visualization using petab problem.
    For documentation, see function plot_data_and_simulation()
    """

    return plot_data_and_simulation(petab_problem.measurement_df,
                                    petab_problem.condition_df,
                                    petab_problem.visualization_df,
                                    sim_data,
                                    dataset_id_list,
                                    sim_cond_id_list,
                                    sim_cond_num_list,
                                    observable_id_list,
                                    observable_num_list,
                                    plotted_noise)


def plot_measurements_by_observable(data_file_path: str,
                                    condition_file_path: str,
                                    plotted_noise: str = MEAN_AND_SD):
    """
    plot measurement data grouped by observable ID.
    A simple wrapper around the more complex function plot_data_and_simulation.

    Parameters:
    ----------

    data_file_path: str
        file path of measurement data
    condition_file_path: str
        file path of condition file
    plotted_noise: str (optional)
        String indicating how noise should be visualized:
        ['MeanAndSD' (default), 'MeanAndSEM', 'replicate', 'provided']

    Return:
    ----------

    ax: axis of figures
    """

    # import measurement data
    measurement_data = measurements.get_measurement_df(data_file_path)

    # get unique observable ID
    observable_id = np.array(measurement_data.observableId)
    uni_observable_id = np.unique(observable_id)
    observable_id_list = [[str(obsId)] for obsId in uni_observable_id]

    # use new routine now
    ax = plot_data_and_simulation(measurement_data, condition_file_path,
                                  observable_id_list=observable_id_list,
                                  plotted_noise=plotted_noise)

    return ax
