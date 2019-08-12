import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .get_data_to_plot import get_data_to_plot
from .plotting_config import plotting_config
import petab
import seaborn as sns
import functools
import warnings

sns.set()


def plot_data_and_simulation(data_file_path: str,
                             condition_file_path: str,
                             visualization_file_path: str = '',
                             simulation_file_path: str = '',
                             dataset_id_list=None,
                             sim_cond_id_list=None,
                             sim_cond_num_list=None,
                             observable_id_list=None,
                             observable_num_list=None):
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

    Returns
    -------
    ax: Axis object of the created plot.
    """

    # import data from PEtab files
    exp_data, exp_conditions, vis_spec, sim_data = _import_from_files(
        data_file_path, condition_file_path, visualization_file_path,
        simulation_file_path, dataset_id_list, sim_cond_id_list,
        sim_cond_num_list, observable_id_list, observable_num_list)

    # get unique plotIDs
    uni_plot_ids, _ = np.unique(vis_spec.plotId, return_index=True)

    fig, ax, num_row, num_col = _create_figure(uni_plot_ids)

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
            ax = _handle_dataset_plot(i_visu_spec, ind_plot, ax, i_row, i_col,
                                      exp_data, exp_conditions, vis_spec,
                                      sim_data)

    # finalize figure
    fig.tight_layout()

    return ax


def _import_from_files(data_file_path,
                       condition_file_path,
                       visualization_file_path,
                       simulation_file_path,
                       dataset_id_list,
                       sim_cond_id_list,
                       sim_cond_num_list,
                       observable_id_list,
                       observable_num_list):
    """
    Helper function for plotting data and simulations, which imports data
    from PEtab files.

    For documentation, see main function plot_data_and_simulation()
    """

    # import measurement data and experimental condition
    exp_data = petab.get_measurement_df(data_file_path)
    exp_conditions = petab.get_condition_df(condition_file_path)

    # import visualization specification, if file was specified
    if visualization_file_path != '':
        vis_spec = pd.read_csv(visualization_file_path, sep="\t",
                               index_col=None)
    else:
        # create them based on simulation conditions
        vis_spec = _get_default_vis_specs(exp_data,
                                          dataset_id_list,
                                          sim_cond_id_list,
                                          sim_cond_num_list,
                                          observable_id_list,
                                          observable_num_list)

    # import simulation file, if file was specified
    if simulation_file_path != '':
        sim_data = pd.read_csv(simulation_file_path,
                               sep="\t", index_col=None)
    else:
        sim_data = None

    return exp_data, exp_conditions, vis_spec, sim_data


def _get_default_vis_specs(exp_data,
                           dataset_id_list=None,
                           sim_cond_id_list=None,
                           sim_cond_num_list=None,
                           observable_id_list=None,
                           observable_num_list=None):
    """
    Helper function for plotting data and simulations, which creates a
    default visualization table.

    For documentation, see main function plot_data_and_simulation()
    """

    # check consistency of settings
    group_by = _check_vis_spec_consistency(dataset_id_list, sim_cond_id_list,
        sim_cond_num_list, observable_id_list, observable_num_list, exp_data)

    if group_by != 'dataset':
        # datasetId_list will be created (possibly overwriting previous list)
        exp_data, dataset_id_list = _create_dataset_id_list(sim_cond_id_list,
            sim_cond_num_list, observable_id_list, observable_num_list,
            exp_data, group_by)

    datasetId_column = [i_dataset for sublist in dataset_id_list for
                        i_dataset in sublist]

    # get number of plots and create plotId-lists
    plot_id_list = ['plot%s' % str(ind + 1) for ind, inner_list in enumerate(
        dataset_id_list) for _ in inner_list]

    # create dataframe
    vis_spec = pd.DataFrame({'plotId': plot_id_list,
                             'datasetId': datasetId_column,
                             'legendEntry': datasetId_column})

    # fill columns with default values
    fill_vis_spec = ((2, 'yLabel', 'value [a.u.]'),
                     (2, 'yOffset', 0),
                     (2, 'yValues', ''),
                     (2, 'xLabel', 'time'),
                     (2, 'xOffset', 0),
                     (2, 'xValues', 'time'),
                     (1, 'yScale', 'lin'),
                     (1, 'xScale', 'lin'),
                     (0, 'plotTypeData', 'MeanAndSD'),
                     (0, 'plotTypeSimulation', 'LinePlot'),
                     (0, 'plotName', ''))
    for pos, col, val in fill_vis_spec:
        vis_spec.insert(loc=pos, column=col, value=val)

    return vis_spec


def _check_vis_spec_consistency(dataset_id_list,
                                sim_cond_id_list,
                                sim_cond_num_list,
                                observable_id_list,
                                observable_num_list,
                                exp_data):
    """
    Helper function for plotting data and simulations, which check the
    visualization setting, if no visualization specification file is provided.

    For documentation, see main function plot_data_and_simulation()
    """

    # We have no vis_spec file. Check how data should be grouped
    group_by = ''
    if dataset_id_list is not None:
        group_by += 'dataset'

    # check whether grouping by simulation condition should be done
    if sim_cond_id_list is not None and sim_cond_num_list is not None:
        raise ("Either specify a list of dataset IDs or a list "
               "of dataset numbers, but not both. Stopping.")
    if sim_cond_id_list is not None or sim_cond_num_list is not None:
        group_by += 'simulation'

    # check whether grouping by observable should be done
    if observable_id_list is not None and observable_num_list is not None:
        raise ("Either specify a list of observable IDs or a list "
               "of observable numbers, but not both. Stopping.")
    if observable_id_list is not None or observable_num_list is not None:
        group_by += 'observable'

    # consistency check. Warn or error, if grouping not clear
    if group_by == 'datasetsimulation':
        warnings.warn("Found grouping by datasetId and simulation condition. "
                      "Using datasetId, omitting simmulation condition.")
        group_by = 'dataset'

    elif group_by == 'datasetobservable':
        warnings.warn("Found grouping by datasetId and observable. "
                      "Using datasetId, omitting observable.")
        group_by = 'dataset'

    elif group_by == 'datasetsimulationobservable':
        warnings.warn("Found grouping by datasetId, simulation condition, and "
                      "observable. Using datasetId, omitting simulation "
                      "condition and observable.")
        group_by = 'dataset'

    elif group_by == 'simulationobservable':
        raise ("Plotting without visualization specification file and "
               "datasetId can be performed via grouping by simulation "
               "conditions OR observables, but not both. Stopping.")
    elif group_by in ['simulation', 'observable', 'dataset']:
        pass
    else:
        raise ("No information provided, how to plot data. Stopping.")

    if group_by != 'dataset':
        # group plots not by dataset. Check, whether such a column would
        # have been available an file a warning, if so
        if 'datasetId' in exp_data.columns:
            warnings.warn("DatasetIds would have been available, but other "
                          "grouping was requested. Consider using datasetId.")
    else:
        if 'datasetId' not in exp_data.columns:
            raise ("Data should be grouped by datasetId, but no datasetId is "
                   "given in the measureents file. Stopping.")

    return group_by


def _create_dataset_id_list(simcond_id_list,
                            simcond_num_list,
                            observable_id_list,
                            observable_num_list,
                            exp_data,
                            group_by):

    # create a column of dummy datasetIDs:
    tmp_s = list(exp_data['simulationConditionId'])
    tmp_o = list(exp_data['observableId'])
    dataset_id_column = [tmp_s[i] + ' - ' + tmp_o[i] for i in exp_data.index]

    # add this column to the measurement table
    if 'datasetId' in exp_data.columns:
        exp_data.drop('datasetId')
    exp_data.insert(loc=exp_data.columns.size, column='datasetId',
                    value=dataset_id_column)

    # make dummy dataset names unique and iterable
    unique_dataset_list = functools.reduce(
        lambda tmp, x: tmp.append(x) or tmp if x not in tmp else tmp,
        list(exp_data['datasetId']), [])
    unique_simcond_list = functools.reduce(
        lambda tmp, x: tmp.append(x) or tmp if x not in tmp else tmp,
        list(exp_data['simulationConditionId']), [])
    unique_obs_list = functools.reduce(
        lambda tmp, x: tmp.append(x) or tmp if x not in tmp else tmp,
        list(exp_data['observableId']), [])

    # we will need a dictionary for mapping simulation conditions
    # /observables to datasets
    ds_dict = {}
    dataset_id_list = []
    if group_by == 'simulation':
        if simcond_id_list is None:
            simcond_id_list = [[unique_simcond_list[i_cond] for i_cond in
                                i_cond_list] for i_cond_list in
                               simcond_num_list]
        for simcond in unique_simcond_list:
            ds_dict[simcond] = [ds for ds in unique_dataset_list if ds[
                0 : len(simcond) + 3] == simcond + ' - ']
        grouped_list = simcond_id_list

    elif group_by == 'observable':
        if observable_id_list is None:
            obs_id_list = [[unique_obs_list[i_obs] for i_obs in i_obs_list]
                           for i_obs_list in observable_num_list]
        for observable in unique_obs_list:
            ds_dict[observable] = [ds for ds in unique_dataset_list if ds[
                - len(observable) - 3:] == ' - ' + observable]
        grouped_list = observable_id_list

    else:
        raise ('Very, very weird error. Should not have happened. Something '
               'went wrong in how datasets should be grouped. Very weird...')

    for sublist in grouped_list:
        datasets_for_this_plot = [dset for sublist_entry in sublist
                                  for dset in ds_dict[sublist_entry]]
        dataset_id_list.append(datasets_for_this_plot)

    return exp_data, dataset_id_list


def _create_figure(uni_plot_ids):
    """
    Helper function for plotting data and simulations, open figure and axes

    Parameters
    ----------
    uni_plot_ids: ndarray
        Array with unique plot indices

    Returns
    -------
    fig: Figure object of the created plot.
    ax: Axis object of the created plot.
    num_row: int, number of subplot rows
    num_col: int, number of subplot columns
    """

    # Set Options for plots
    # possible options: see: plt.rcParams.keys()
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 10
    plt.rcParams['figure.figsize'] = [20, 10]
    plt.rcParams['errorbar.capsize'] = 2

    # Set Colormap
    sns.set_palette("colorblind")

    #  Initiate subplots
    num_subplot = len(uni_plot_ids)

    # compute, how many rows and columns we need for the subplots
    num_row = np.round(np.sqrt(num_subplot))
    num_col = np.ceil(num_subplot / num_row)

    # initialize figure
    fig, ax = plt.subplots(int(num_row), int(num_col), squeeze=False)

    return fig, ax, num_row, num_col


def _handle_dataset_plot(i_visu_spec,
                         ind_plot,
                         ax,
                         i_row,
                         i_col,
                         exp_data,
                         exp_conditions,
                         vis_spec,
                         sim_data):
    # get datasetID and independent variable of first entry of plot1
    dataset_id = vis_spec.datasetId[i_visu_spec]
    indep_var = vis_spec.xValues[i_visu_spec]

    # define index to reduce exp_data to data linked to datasetId
    ind_dataset = exp_data['datasetId'] == dataset_id

    # gather simulationConditionIds belonging to datasetId
    uni_condition_id = np.unique(exp_data[ind_dataset].simulationConditionId)
    col_name_unique = 'simulationConditionId'

    # Case separation of independent parameter: condition, time or custom
    if indep_var == 'time':
        # obtain unique observation times
        uni_condition_id = np.unique(exp_data[ind_dataset].time)
        col_name_unique = 'time'
        conditions = uni_condition_id
    elif indep_var == 'condition':
        conditions = None
    else:
        # extract conditions (plot input) from condition file
        ind_cond = exp_conditions.index.isin(uni_condition_id)
        conditions = exp_conditions[ind_cond][indep_var]

    # retrieve measurements from dataframes
    measurement_to_plot = get_data_to_plot(vis_spec, exp_data, sim_data,
                                           uni_condition_id, i_visu_spec,
                                           col_name_unique)

    plot_sim = True
    if sim_data is None:
        plot_sim = False

    # plot data
    ax = plotting_config(vis_spec, ax, i_row, i_col, conditions,
                         measurement_to_plot, ind_plot, i_visu_spec, plot_sim)

    # Beautify plots
    ax[i_row, i_col].set_xlabel(
        vis_spec.xLabel[i_visu_spec])
    ax[i_row, i_col].set_ylabel(
        vis_spec.yLabel[i_visu_spec])

    return ax
