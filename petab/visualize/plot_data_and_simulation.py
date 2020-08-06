"""Functions for plotting PEtab measurement files and simulation results in
the same format."""

from typing import Dict, Union, Optional, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .helper_functions import (create_figure,
                               handle_dataset_plot,
                               check_ex_exp_columns,
                               create_or_update_vis_spec)

from .. import problem, measurements, core, conditions
from ..C import *

# for typehints
IdsList = List[str]
NumList = List[int]


def plot_data_and_simulation(
        exp_data: Union[str, pd.DataFrame],
        exp_conditions: Union[str, pd.DataFrame],
        vis_spec: Optional[Union[str, pd.DataFrame]] = None,
        sim_data: Optional[Union[str, pd.DataFrame]] = None,
        dataset_id_list: Optional[List[IdsList]] = None,
        sim_cond_id_list: Optional[List[IdsList]] = None,
        sim_cond_num_list: Optional[List[NumList]] = None,
        observable_id_list: Optional[List[IdsList]] = None,
        observable_num_list: Optional[List[NumList]] = None,
        plotted_noise: Optional[str] = MEAN_AND_SD,
        subplot_file_path: str = ''
) -> Optional[Union[Dict[str, plt.Subplot],
                    'np.ndarray[plt.Subplot]']]:
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
    vis_spec:
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

    if isinstance(exp_conditions, str):
        exp_conditions = conditions.get_condition_df(exp_conditions)

    # import simulation file, if file was specified
    if sim_data is not None:
        if isinstance(sim_data, str):
            sim_data = core.get_simulation_df(sim_data)
        # check columns, and add non-mandatory default columns
        sim_data, _, _ = check_ex_exp_columns(sim_data,
                                              dataset_id_list,
                                              sim_cond_id_list,
                                              sim_cond_num_list,
                                              observable_id_list,
                                              observable_num_list,
                                              exp_conditions,
                                              sim=True)

    # import from file in case experimental data is provided in file
    if isinstance(exp_data, str):
        exp_data = measurements.get_measurement_df(exp_data)
    # check columns, and add non-mandatory default columns
    exp_data, dataset_id_list, legend_dict = \
        check_ex_exp_columns(exp_data,
                             dataset_id_list,
                             sim_cond_id_list,
                             sim_cond_num_list,
                             observable_id_list,
                             observable_num_list,
                             exp_conditions)

    # import visualization specification, if file was specified
    if isinstance(vis_spec, str):
        vis_spec = core.get_visualization_df(vis_spec)

    exp_data, vis_spec = create_or_update_vis_spec(exp_data,
                                                   exp_conditions,
                                                   vis_spec,
                                                   dataset_id_list,
                                                   sim_cond_id_list,
                                                   sim_cond_num_list,
                                                   observable_id_list,
                                                   observable_num_list,
                                                   plotted_noise)

    if sim_data is not None:
        sim_data[DATASET_ID] = exp_data[DATASET_ID]

    # get unique plotIDs
    uni_plot_ids = np.unique(vis_spec[PLOT_ID])

    # Switch saving plots to file on or get axes
    plots_to_file = subplot_file_path != ''
    if not plots_to_file:
        fig, axes = create_figure(uni_plot_ids, plots_to_file)

    # loop over unique plotIds
    for var_plot_id in uni_plot_ids:

        if plots_to_file:
            fig, axes = create_figure(uni_plot_ids, plots_to_file)
            ax = axes[0, 0]
        else:
            ax = axes[var_plot_id]

        # get indices for specific plotId
        ind_plot = (vis_spec[PLOT_ID] == var_plot_id)

        # loop over datsets
        for _, plot_spec in vis_spec[ind_plot].iterrows():
            # handle plot of current dataset
            handle_dataset_plot(plot_spec, ax, exp_data,
                                exp_conditions, sim_data)

        if BAR_PLOT in vis_spec.loc[ind_plot, PLOT_TYPE_SIMULATION]:

            legend = ['measurement']

            if sim_data is not None:
                legend.append('simulation')

            ax.legend(legend)
            x_names = vis_spec.loc[ind_plot, LEGEND_ENTRY]
            ax.set_xticks(range(len(x_names)))
            ax.set_xticklabels(x_names)

            for label in ax.get_xmajorticklabels():
                label.set_rotation(30)
                label.set_horizontalalignment("right")

        if plots_to_file:
            plt.tight_layout()
            plt.savefig(f'{subplot_file_path}/{var_plot_id}.png')
            plt.close()

    # finalize figure
    if not plots_to_file:
        fig.tight_layout()
        return axes

    return None


def plot_petab_problem(
        petab_problem: problem.Problem,
        sim_data: Optional[Union[str, pd.DataFrame]] = None,
        dataset_id_list: Optional[List[IdsList]] = None,
        sim_cond_id_list: Optional[List[IdsList]] = None,
        sim_cond_num_list: Optional[List[NumList]] = None,
        observable_id_list: Optional[List[IdsList]] = None,
        observable_num_list: Optional[List[NumList]] = None,
        plotted_noise: Optional[str] = MEAN_AND_SD
) -> Optional[Union[Dict[str, plt.Subplot], 'np.ndarray[plt.Subplot]']]:
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


def plot_measurements_by_observable(
        data_file_path: str,
        condition_file_path: str,
        plotted_noise: Optional[str] = MEAN_AND_SD
) -> Optional[Union[Dict[str, plt.Subplot], 'np.ndarray[plt.Subplot]']]:
    """
    plot measurement data grouped by observable ID.
    A simple wrapper around the more complex function plot_data_and_simulation.

    Parameters:
    ----------

    data_file_path:
        file path of measurement data
    condition_file_path:
        file path of condition file
    plotted_noise:
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


def save_vis_spec(
        exp_data: Union[str, pd.DataFrame],
        exp_conditions: Union[str, pd.DataFrame],
        vis_spec: Optional[Union[str, pd.DataFrame]] = None,
        dataset_id_list: Optional[List[IdsList]] = None,
        sim_cond_id_list: Optional[List[IdsList]] = None,
        sim_cond_num_list: Optional[List[NumList]] = None,
        observable_id_list: Optional[List[IdsList]] = None,
        observable_num_list: Optional[List[NumList]] = None,
        plotted_noise: Optional[str] = MEAN_AND_SD,
        output_file_path: str = 'visuSpec.tsv'
):
    """
    Generate and save visualization specification to a file.
    If vis_spec is provided, the missing columns will be added.

    Parameters
    ----------
    exp_data:
        Measurement DataFrame in the PEtab format or path to the data file.
    exp_conditions:
        Condition DataFrame in the PEtab format or path to the condition file.
    vis_spec:
        Visualization specification DataFrame in the PEtab format or path to
        visualization file.
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
    output_file_path:
        File path to which  the generated visualization specification is saved.
    """
    # import from file in case experimental data is provided in file
    if isinstance(exp_data, str):
        exp_data = measurements.get_measurement_df(exp_data)

    if isinstance(exp_conditions, str):
        exp_conditions = conditions.get_condition_df(exp_conditions)

    # import visualization specification, if file was specified
    if isinstance(vis_spec, str):
        vis_spec = core.get_visualization_df(vis_spec)

    _, vis_spec = create_or_update_vis_spec(exp_data,
                                            exp_conditions,
                                            vis_spec,
                                            dataset_id_list,
                                            sim_cond_id_list,
                                            sim_cond_num_list,
                                            observable_id_list,
                                            observable_num_list,
                                            plotted_noise)

    vis_spec.to_csv(output_file_path, sep='\t', index=False)
