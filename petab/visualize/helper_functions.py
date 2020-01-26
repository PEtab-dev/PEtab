"""
This file should contain the functions, which PEtab internally needs for
plotting, but which are not meant to be used by non-developers and should
hence not be directly visible/usable when using `import petab.visualize`.
"""

import functools
import warnings
from numbers import Number

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import petab
import seaborn as sns

from .plotting_config import plot_lowlevel
from ..C import *

sns.set()


def import_from_files(data_file_path,
                      condition_file_path,
                      visualization_file_path,
                      simulation_file_path,
                      dataset_id_list,
                      sim_cond_id_list,
                      sim_cond_num_list,
                      observable_id_list,
                      observable_num_list,
                      plotted_noise):
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
        vis_spec = petab.get_visualization_df(visualization_file_path)
    else:
        # create them based on simulation conditions
        vis_spec = get_default_vis_specs(exp_data,
                                         exp_conditions,
                                         dataset_id_list,
                                         sim_cond_id_list,
                                         sim_cond_num_list,
                                         observable_id_list,
                                         observable_num_list,
                                         plotted_noise)

    # import simulation file, if file was specified
    if simulation_file_path != '':
        sim_data = petab.get_simulation_df(simulation_file_path)
    else:
        sim_data = None

    return exp_data, exp_conditions, vis_spec, sim_data


def check_vis_spec_consistency(dataset_id_list,
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
        raise NotImplementedError(
            "Either specify a list of dataset IDs or a list of dataset "
            "numbers, but not both. Stopping.")
    if sim_cond_id_list is not None or sim_cond_num_list is not None:
        group_by += 'simulation'

    # check whether grouping by observable should be done
    if observable_id_list is not None and observable_num_list is not None:
        raise NotImplementedError(
            "Either specify a list of observable IDs or a list "
            "of observable numbers, but not both. Stopping.")
    if observable_id_list is not None or observable_num_list is not None:
        group_by += 'observable'

    # consistency check. Warn or error, if grouping not clear
    if group_by == 'datasetsimulation':
        warnings.warn("Found grouping by datasetId and simulation condition. "
                      "Using datasetId, omitting simulation condition.")
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
        raise NotImplementedError(
            "Plotting without visualization specification file and datasetId "
            "can be performed via grouping by simulation conditions OR "
            "observables, but not both. Stopping.")
    elif group_by in ['simulation', 'observable', 'dataset']:
        pass
    else:
        raise NotImplementedError(
            "No information provided, how to plot data. Stopping.")

    if group_by != 'dataset':
        # group plots not by dataset. Check, whether such a column would
        # have been available (and give a warning, if so)
        if 'datasetId' in exp_data.columns:
            warnings.warn("DatasetIds would have been available, but other "
                          "grouping was requested. Consider using datasetId.")
    else:
        if 'datasetId' not in exp_data.columns:
            raise NotImplementedError(
                "Data should be grouped by datasetId, but no datasetId is "
                "given in the measurement file. Stopping.")

    return group_by


def create_dataset_id_list(simcond_id_list,
                           simcond_num_list,
                           observable_id_list,
                           observable_num_list,
                           exp_data,
                           exp_conditions,
                           group_by):
    """Create dataset id list"""
    # create a column of dummy datasetIDs and legend entries: preallocate
    dataset_id_column = []
    legend_dict = {}

    # loop over experimental data table, create datasetId for each entry
    tmp_simcond = list(exp_data[SIMULATION_CONDITION_ID])
    tmp_obs = list(exp_data[OBSERVABLE_ID])
    for ind, cond_id in enumerate(tmp_simcond):
        # create and add dummy datasetID
        dataset_id = tmp_simcond[ind] + ' - ' + tmp_obs[ind]
        dataset_id_column.append(dataset_id)

        # create nicer legend entries from condition names instead of IDs
        if dataset_id not in legend_dict.keys():
            tmp = exp_conditions.loc[exp_conditions.index == cond_id]
            try:
                legend_dict[dataset_id] = tmp.conditionName[0] + ' - ' + \
                    tmp_obs[ind]
            except AttributeError:
                legend_dict[dataset_id] = tmp.index[0] + ' - ' + \
                    tmp_obs[ind]

    # add these column to the measurement table (possibly overwrite)
    if DATASET_ID in exp_data.columns:
        exp_data = exp_data.drop(DATASET_ID, axis=1)
    exp_data.insert(loc=exp_data.columns.size, column=DATASET_ID,
                    value=dataset_id_column)

    # make dummy dataset names unique and iterable
    unique_dataset_list = functools.reduce(
        lambda tmp, x: tmp.append(x) or tmp if x not in tmp else tmp,
        list(exp_data[DATASET_ID]), [])
    unique_simcond_list = functools.reduce(
        lambda tmp, x: tmp.append(x) or tmp if x not in tmp else tmp,
        list(exp_data[SIMULATION_CONDITION_ID]), [])
    unique_obs_list = functools.reduce(
        lambda tmp, x: tmp.append(x) or tmp if x not in tmp else tmp,
        list(exp_data[OBSERVABLE_ID]), [])

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
                0:len(simcond)+3] == simcond + ' - ']
        grouped_list = simcond_id_list

    elif group_by == 'observable':
        if observable_id_list is None:
            observable_id_list = [[unique_obs_list[i_obs] for i_obs in
                                   i_obs_list] for i_obs_list in
                                  observable_num_list]
        for observable in unique_obs_list:
            ds_dict[observable] = [ds for ds in unique_dataset_list if ds[
                -len(observable)-3:] == ' - ' + observable]
        grouped_list = observable_id_list

    else:
        raise NotImplementedError(
            "Very, very weird error. Should not have happened. Something "
            "went wrong in how datasets should be grouped. Very weird...")

    for sublist in grouped_list:
        datasets_for_this_plot = [dset for sublist_entry in sublist
                                  for dset in ds_dict[sublist_entry]]
        dataset_id_list.append(datasets_for_this_plot)

    return exp_data, dataset_id_list, legend_dict


def create_figure(uni_plot_ids, plots_to_file):
    """
    Helper function for plotting data and simulations, open figure and axes

    Parameters
    ----------
    uni_plot_ids: ndarray
        Array with unique plot indices
    plots_to_file: bool
        Indicator if plots are saved to file

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
    sns.set(style="ticks", palette="colorblind")

    # Check if plots are saved to file and return single subplot axis
    if plots_to_file:
        fig, ax = plt.subplots(1, 1, squeeze=False)
        return fig, ax, 1, 1

    #  Initiate subplots
    num_subplot = len(uni_plot_ids)

    # compute, how many rows and columns we need for the subplots
    num_row = np.round(np.sqrt(num_subplot))
    num_col = np.ceil(num_subplot / num_row)

    # initialize figure
    fig, ax = plt.subplots(int(num_row), int(num_col), squeeze=False)
    # trim subplots output to the correct size
    for axes in ax.flat[num_subplot:]:
        axes.remove()

    return fig, ax, num_row, num_col


def get_default_vis_specs(exp_data,
                          exp_conditions,
                          dataset_id_list=None,
                          sim_cond_id_list=None,
                          sim_cond_num_list=None,
                          observable_id_list=None,
                          observable_num_list=None,
                          plotted_noise='MeanAndSD'):
    """
    Helper function for plotting data and simulations, which creates a
    default visualization table.

    For documentation, see main function plot_data_and_simulation()
    """

    # check consistency of settings
    group_by = check_vis_spec_consistency(
        dataset_id_list, sim_cond_id_list, sim_cond_num_list,
        observable_id_list, observable_num_list, exp_data)

    if group_by != 'dataset':
        # datasetId_list will be created (possibly overwriting previous list
        #  - only in the local variable, not in the tsv-file)
        exp_data, dataset_id_list, legend_dict = create_dataset_id_list(
            sim_cond_id_list, sim_cond_num_list, observable_id_list,
            observable_num_list, exp_data, exp_conditions, group_by)

    dataset_id_column = [i_dataset for sublist in dataset_id_list
                         for i_dataset in sublist]
    if group_by != 'dataset':
        dataset_label_column = [legend_dict[i_dataset] for sublist in
                                dataset_id_list for i_dataset in sublist]
    else:
        dataset_label_column = dataset_id_column

    # get number of plots and create plotId-lists
    plot_id_list = ['plot%s' % str(ind + 1) for ind, inner_list in enumerate(
        dataset_id_list) for _ in inner_list]

    # create dataframe
    vis_spec = pd.DataFrame({PLOT_ID: plot_id_list,
                             DATASET_ID: dataset_id_column,
                             LEGEND_ENTRY: dataset_label_column})

    # fill columns with default values
    fill_vis_spec = ((2, Y_LABEL, 'value'),
                     (2, Y_OFFSET, 0),
                     (2, Y_VALUES, ''),
                     (2, X_LABEL, 'time'),
                     (2, X_OFFSET, 0),
                     (2, X_VALUES, 'time'),
                     (1, Y_SCALE, LIN),
                     (1, X_SCALE, LIN),
                     (0, PLOT_TYPE_DATA, plotted_noise),
                     (0, PLOT_TYPE_SIMULATION, LINE_PLOT),
                     (0, PLOT_NAME, ''))
    for pos, col, val in fill_vis_spec:
        vis_spec.insert(loc=pos, column=col, value=val)

    return vis_spec, exp_data


def handle_dataset_plot(i_visu_spec,
                        ind_plot,
                        ax,
                        i_row,
                        i_col,
                        exp_data,
                        exp_conditions,
                        vis_spec,
                        sim_data):
    """Handle dataset plot"""
    # get datasetID and independent variable of first entry of plot1
    dataset_id = vis_spec[DATASET_ID][i_visu_spec]
    indep_var = vis_spec[X_VALUES][i_visu_spec]

    # define index to reduce exp_data to data linked to datasetId
    ind_dataset = exp_data[DATASET_ID] == dataset_id

    # gather simulationConditionIds belonging to datasetId
    uni_condition_id = np.unique(
        exp_data[ind_dataset][SIMULATION_CONDITION_ID])
    col_name_unique = SIMULATION_CONDITION_ID

    # Case separation of independent parameter: condition, time or custom
    if indep_var == TIME:
        # obtain unique observation times
        uni_condition_id = np.unique(exp_data[ind_dataset][TIME])
        col_name_unique = TIME
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

    # check, whether simulation should be plotted
    plot_sim = True
    if sim_data is None:
        plot_sim = False

    # plot data
    nan_set = all([np.isnan(val) for val in measurement_to_plot['mean']])
    if not nan_set:
        ax = plot_lowlevel(vis_spec, ax, i_row, i_col, conditions,
                           measurement_to_plot, ind_plot, i_visu_spec,
                           plot_sim)

    # Beautify plots
    ax[i_row, i_col].set_xlabel(
        vis_spec.xLabel[i_visu_spec])
    ax[i_row, i_col].set_ylabel(
        vis_spec.yLabel[i_visu_spec])

    return ax


def get_data_to_plot(vis_spec: pd.DataFrame,
                     m_data: pd.DataFrame,
                     simulation_data: pd.DataFrame,
                     condition_ids: np.ndarray,
                     i_visu_spec: int,
                     col_id: str,
                     simulation_field: str = SIMULATION) -> pd.DataFrame:
    """
    group the data, which should be plotted and return it as dataframe.

    Parameters:
        vis_spec:
            pandas data frame, contains defined data format
            (visualization file)
        m_data:
            pandas data frame, contains defined data format (measurement file)
        simulation_data:
            pandas data frame, contains defined data format (simulation file)
        condition_ids:
            numpy array, containing all unique condition IDs which should be
            plotted in one figure (can be found in measurementData file,
            column simulationConditionId)
        i_visu_spec:
            int, current index (row number) of row which should be plotted in
            visualizationSpecification file
        col_id:
            str, the name of the column in visualization file, whose entries
            should be unique (depends on condition in column
            independentVariableName)
        simulation_field:
            Column name in ``simulation_data`` that contains the actual
            simulation result.

    Returns:
        data_to_plot:
            pandas.DataFrame containing the data which should be plotted
            (Mean and Std)
    """

    # create empty dataframe for means and SDs
    data_to_plot = pd.DataFrame(
        columns=['mean', 'noise_model', 'sd', 'sem', 'repl', 'sim'],
        index=condition_ids)

    for var_cond_id in condition_ids:
        # get boolean vector which fulfill the requirements
        vec_bool_meas = ((m_data[col_id] == var_cond_id)
                         & (m_data[DATASET_ID]
                            == vis_spec.datasetId[i_visu_spec]))
        # get indices of rows with True values of vec_bool_meas
        ind_meas = [i_visu_spec for i_visu_spec,
                    x in enumerate(vec_bool_meas) if x]

        # check that all entries for all columns-conditions are the same:
        # check correct observable
        bool_observable = (m_data[OBSERVABLE_PARAMETERS][ind_meas[0]] ==
                           m_data[OBSERVABLE_PARAMETERS])
        # special handling, if column in m_data.observableParameters is empty
        if isinstance(m_data[OBSERVABLE_PARAMETERS][ind_meas[0]], Number) \
                and np.isnan(m_data.observableParameters[ind_meas[0]]):
            bool_observable = np.isnan(m_data[OBSERVABLE_PARAMETERS])

        # check correct time point
        bool_time = True
        if col_id != TIME:
            bool_time = (m_data[TIME][ind_meas[0]] == m_data[TIME])

        # check correct preqeuilibration condition
        pre_cond = m_data[PREEQUILIBRATION_CONDITION_ID][ind_meas[0]]
        bool_preequ = (pre_cond == m_data[PREEQUILIBRATION_CONDITION_ID])
        # special handling is needed, if preequilibration cond is left empty
        if isinstance(pre_cond, Number) and np.isnan(pre_cond):
            bool_preequ = np.isnan(m_data[PREEQUILIBRATION_CONDITION_ID])

        # combine all boolean vectors
        vec_bool_allcond = bool_preequ & bool_observable & bool_time

        # get indices of rows with "True" values, of vec_bool_allcond
        ind_bool_allcond = [i_visu_spec for i_visu_spec,
                            x in enumerate(vec_bool_allcond) if x]

        # get intersection of ind_meas and ind_bool_allcond
        ind_intersec = np.intersect1d(ind_meas, ind_bool_allcond)

        # TODO (#117): Here not the case: So, if entries in measurement file:
        #  preequCondId, time, observableParams, noiseParams,
        #  are not the same, then  -> differ these data into
        #  different groups!
        # now: go in simulationConditionId, search group of unique
        # simulationConditionId e.g. rows 0,6,12,18 share the same
        # simulationCondId, then check if other column entries are the same
        # (now: they are), then take intersection of rows 0,6,12,18 and checked
        # other same columns (-> now: 0,6,12,18) and then go on with code.
        # if there is at some point a difference in other columns, say e.g.
        # row 12,18 have different noiseParams than rows 0,6, the actual code
        # would take rows 0,6 and forget about rows 12,18

        # compute mean and standard deviation across replicates
        data_to_plot.at[var_cond_id, 'mean'] = np.mean(
            m_data[MEASUREMENT][ind_intersec])
        data_to_plot.at[var_cond_id, 'sd'] = np.std(
            m_data[MEASUREMENT][ind_intersec])

        if vis_spec.plotTypeData[i_visu_spec] == PROVIDED:
            tmp_noise = m_data[NOISE_PARAMETERS][ind_intersec].values[0]
            if isinstance(tmp_noise, str):
                raise NotImplementedError(
                    "No numerical noise values provided in the measurement "
                    "table. Stopping.")
            if isinstance(tmp_noise, Number) or tmp_noise.dtype == 'float64':
                data_to_plot.at[var_cond_id, 'noise_model'] = tmp_noise

        # standard error of mean
        data_to_plot.at[var_cond_id, 'sem'] = np.std(m_data[MEASUREMENT][
            ind_intersec]) / np.sqrt(len(m_data[MEASUREMENT][ind_intersec]))

        # single replicates
        data_to_plot.at[var_cond_id, 'repl'] = \
            m_data[MEASUREMENT][ind_intersec]

        if simulation_data is not None:
            data_to_plot.at[var_cond_id, 'sim'] = np.mean(
                simulation_data[simulation_field][ind_intersec])

    return data_to_plot
