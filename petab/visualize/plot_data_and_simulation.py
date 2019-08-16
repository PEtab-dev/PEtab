import numpy as np
import pandas as pd
import seaborn as sns
from .helper_functions import (import_from_files,
                               create_figure,
                               handle_dataset_plot)


def plot_data_and_simulation(data_file_path: str,
                             condition_file_path: str,
                             visualization_file_path: str = '',
                             simulation_file_path: str = '',
                             dataset_id_list=None,
                             sim_cond_id_list=None,
                             sim_cond_num_list=None,
                             observable_id_list=None,
                             observable_num_list=None,
                             plotted_noise: str = 'MeanAndSD'):
    """
    Main function for plotting data and simulations.

    What exactly should be plotted is specified in a
    visualizationSpecification.tsv file.

    Also, the data, simulations and conditions have
    to be defined in a specific format
    (see "doc/documentation_data_format.md").

    Parameters
    ----------
    data_file_path: str
        Path to the data file.
    condition_file_path: str
        Path to the condition file.
    visualization_file_path: str (optional)
        Path to the visualization specification file.
    simulation_file_path: str (optional)
        Path to the simulation output data file.
    dataset_id_list: list (optional)
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the datasetIds for this plot.
        Only to be used if no visualization file was available.
    sim_cond_id_list: list (optional)
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the simulationConditionIds for this plot.
        Only to be used if no visualization file was available.
    sim_cond_num_list: list (optional)
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the numbers corresponding to the simulationConditionIds for
        this plot.
        Only to be used if no visualization file was available.
    observable_id_list: list (optional)
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the observableIds for this plot.
        Only to be used if no visualization file was available.
    observable_num_list: list (optional)
        A list of lists. Each sublist corresponds to a plot, each subplot
        contains the numbers corresponding to the observableIds for
        this plot.
        Only to be used if no visualization file was available.
    plotted_noise: str (optional)
        String indicating how noise should be visualized:
        ['MeanAndSD' (default), 'MeanAndSEM', 'replicate', 'provided']

    Returns
    -------
    ax: Axis object of the created plot.
    """

    # import data from PEtab files
    exp_data, exp_conditions, vis_spec, sim_data = import_from_files(
        data_file_path, condition_file_path, visualization_file_path,
        simulation_file_path, dataset_id_list, sim_cond_id_list,
        sim_cond_num_list, observable_id_list, observable_num_list,
        plotted_noise)

    # get unique plotIDs
    uni_plot_ids, _ = np.unique(vis_spec.plotId, return_index=True)

    fig, ax, num_row, num_col = create_figure(uni_plot_ids)

    # loop over unique plotIds
    for i_plot_id, var_plot_id in enumerate(uni_plot_ids):

        # setting axis indices
        i_row = int(np.ceil((i_plot_id + 1) / num_col)) - 1
        i_col = int(((i_plot_id + 1) - i_row * num_col)) - 1

        # get indices for specific plotId
        ind_plot = (vis_spec['plotId'] == var_plot_id)

        # loop over datsets
        for i_visu_spec in vis_spec[ind_plot].index.values:
            # handle plot of current dataset
            ax = handle_dataset_plot(i_visu_spec, ind_plot, ax, i_row, i_col,
                                     exp_data, exp_conditions, vis_spec,
                                     sim_data)

    # finalize figure
    fig.tight_layout()
    sns.despine()

    return ax


def plot_measurements_by_observable(data_file_path: str,
                                    condition_file_path: str,
                                    plotted_noise: str = 'MeanAndSD'):
    '''
    plot measurement data grouped by observable ID.
    A simple wrapper around the more complex function plot_data_and_simulation.

    Parameters:
    ----------

    DataFilePath: str
        file path of measurement data
    ConditionFilePath: str
        file path of condition file
    plotted_noise: str (optional)
        String indicating how noise should be visualized:
        ['MeanAndSD' (default), 'MeanAndSEM', 'replicate', 'provided']

    Return:
    ----------

    ax: axis of figures
    '''

    # import measurement data
    measurement_data = pd.read_csv(
        data_file_path, sep="\t", index_col=None)

    # get unique observable ID
    observable_id = np.array(measurement_data.observableId)
    uni_observable_id = np.unique(observable_id)
    observable_id_list = [[str(obsId)] for obsId in uni_observable_id]

    # use new routine now
    ax = plot_data_and_simulation(data_file_path, condition_file_path,
                                  observable_id_list=observable_id_list,
                                  plotted_noise=plotted_noise)

    return ax
