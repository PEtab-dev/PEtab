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

from typing import Union

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
    # if group_by is still empty (if visuSpec file is available but datasetId
    # is not  available), default: observables
    elif group_by == '':
        group_by = 'observable'
        warnings.warn('Default plotting: grouping by observable. If you want '
                      'to specify another grouping option, please add '
                      '\'datasetId\' columns.')
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
        dataset_id = tmp_simcond[ind] + '_' + tmp_obs[ind]
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
            # ds_dict[simcond] = [ds for ds in unique_dataset_list if ds[
            #    0:len(simcond)+3] == simcond + ' - ']
            # ds_dict[simcond] = [ds for ds in unique_dataset_list if ds[
            #    0:len(simcond) + 3] == simcond + '_']
            ds_dict[simcond] = [ds for ds in unique_dataset_list if ds[
                0:len(simcond)] == simcond]
        grouped_list = simcond_id_list

    elif group_by == 'observable':
        if observable_id_list is None:
            observable_id_list = [[unique_obs_list[i_obs] for i_obs in
                                   i_obs_list] for i_obs_list in
                                  observable_num_list]
        for observable in unique_obs_list:
            # ds_dict[observable] = [ds for ds in unique_dataset_list if ds[
            #    -len(observable)-3:] == ' - ' + observable]
            ds_dict[observable] = [ds for ds in unique_dataset_list if ds[
                -len(observable) - 1:] == '_' + observable]
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


def create_figure(uni_plot_ids: np.ndarray, plots_to_file: bool):
    """
    Helper function for plotting data and simulations, open figure and axes

    Parameters
    ----------
    uni_plot_ids:
        Array with unique plot indices
    plots_to_file:
        Indicator if plots are saved to file

    Returns
    -------
    fig: Figure object of the created plot.
    ax: Axis object of the created plot.
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
        num_subplot = 1
    else:
        num_subplot = len(uni_plot_ids)

    # compute, how many rows and columns we need for the subplots
    num_row = int(np.round(np.sqrt(num_subplot)))
    num_col = int(np.ceil(num_subplot / num_row))

    fig, axes = plt.subplots(num_row, num_col, squeeze=False)

    if not plots_to_file:
        for ax in axes.flat[num_subplot:]:
            ax.remove()

        axes = dict(zip(uni_plot_ids, axes.flat))

    return fig, axes


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


def check_ex_visu_columns(vis_spec, dataset_id_list, legend_dict):
    """
    Check the columns in Visu_Spec file, if non-mandotory columns does not
    exist, create default columns
    """
    if X_VALUES not in vis_spec.columns:
        raise NotImplementedError(
            "Please define column: \'xValues\' in visualization file.")
    if Y_LABEL not in vis_spec.columns:
        vis_spec[Y_LABEL] = 'value'
    if Y_VALUES not in vis_spec.columns:
        vis_spec[Y_VALUES] = ''
    if X_LABEL not in vis_spec.columns:
        vis_spec[X_LABEL] = 'time'
    if X_OFFSET not in vis_spec.columns:
        vis_spec[X_OFFSET] = 0
    if Y_SCALE not in vis_spec.columns:
        vis_spec[Y_SCALE] = LIN
    if X_SCALE not in vis_spec.columns:
        vis_spec[X_SCALE] = LIN
    if LEGEND_ENTRY not in vis_spec.columns:
        # if we have dataset_id_list and legend_dict is empty
        # if dataset_id_list is not None and not bool(legend_dict):
        if dataset_id_list and not legend_dict:
            dataset_id_column = [i_dataset for sublist in dataset_id_list
                                 for i_dataset in sublist]
            vis_spec[LEGEND_ENTRY] = dataset_id_column
        # if dataset_id_list is empty but we have legend_dict
        elif dataset_id_list is None and bool(legend_dict):
            vis_spec[LEGEND_ENTRY] = legend_dict
        # if dataset_id_list is empty and legend_dict is empty, but
        # datasetID-column is available
        elif dataset_id_list is None and not bool(legend_dict) and \
                DATASET_ID in vis_spec.columns:
            vis_spec[LEGEND_ENTRY] = vis_spec[DATASET_ID]
        else:
            vis_spec[LEGEND_ENTRY] = 'condition'
    if PLOT_NAME not in vis_spec.columns:
        vis_spec[PLOT_NAME] = ''
    if PLOT_TYPE_DATA not in vis_spec.columns:
        vis_spec[PLOT_TYPE_DATA] = MEAN_AND_SD
    if PLOT_TYPE_SIMULATION not in vis_spec.columns:
        vis_spec[PLOT_TYPE_SIMULATION] = LINE_PLOT

    return vis_spec


def check_ex_exp_columns(exp_data,
                         dataset_id_list,
                         sim_cond_id_list,
                         sim_cond_num_list,
                         observable_id_list,
                         observable_num_list,
                         exp_conditions):
    """
    Check the columns in measurement file, if non-mandotory columns does not
    exist, create default columns
    """
    # mandatory columns
    if OBSERVABLE_ID not in exp_data.columns:
        raise NotImplementedError(
            "Column \'observableId\' is missing in measurement file. ")
    if SIMULATION_CONDITION_ID not in exp_data.columns:
        raise NotImplementedError(
            "Column \'simulationConditionId\' is missing in measurement "
            "file. ")
    if MEASUREMENT not in exp_data.columns:
        raise NotImplementedError(
            "Column \'measurement\' is missing in measurement "
            "file. ")
    if TIME not in exp_data.columns:
        raise NotImplementedError(
            "Column \'time\' is missing in measurement "
            "file. ")
    # non-mandatory columns
    if PREEQUILIBRATION_CONDITION_ID not in exp_data.columns:
        exp_data.insert(loc=1, column=PREEQUILIBRATION_CONDITION_ID,
                        value='')
    if OBSERVABLE_PARAMETERS not in exp_data.columns:
        exp_data.insert(loc=4, column=OBSERVABLE_PARAMETERS,
                        value='')
    if NOISE_PARAMETERS not in exp_data.columns:
        exp_data.insert(loc=4, column=NOISE_PARAMETERS,
                        value=0)
    if REPLICATE_ID not in exp_data.columns:
        exp_data.insert(loc=4, column=REPLICATE_ID,
                        value='')
    legend_dict = {}
    if DATASET_ID not in exp_data.columns:
        if dataset_id_list is not None:
            exp_data.insert(loc=4, column=DATASET_ID,
                            value=dataset_id_list)
        else:
            # datasetId_list will be created (possibly overwriting previous
            # list - only in the local variable, not in the tsv-file)
            # check consistency of settings
            group_by = check_vis_spec_consistency(dataset_id_list,
                                                  sim_cond_id_list,
                                                  sim_cond_num_list,
                                                  observable_id_list,
                                                  observable_num_list,
                                                  exp_data)
            observable_id_list = \
                [[el] for el in exp_data.observableId.unique()]

            exp_data, dataset_id_list, legend_dict = create_dataset_id_list(
                sim_cond_id_list, sim_cond_num_list, observable_id_list,
                observable_num_list, exp_data, exp_conditions, group_by)

    return exp_data, dataset_id_list, legend_dict


def handle_dataset_plot(plot_spec: pd.Series,
                        ax: plt.Axes,
                        exp_data: pd.DataFrame,
                        exp_conditions: pd.DataFrame,
                        sim_data: pd.DataFrame):
    """
    Handle dataset plot
    """
    # get datasetID and independent variable of first entry of plot1
    dataset_id = plot_spec[DATASET_ID]
    indep_var = plot_spec[X_VALUES]

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
    measurement_to_plot = get_data_to_plot(plot_spec, exp_data, sim_data,
                                           uni_condition_id, col_name_unique)

    # check, whether simulation should be plotted
    plot_sim = sim_data is not None

    # plot data
    nan_set = all([np.isnan(val) for val in measurement_to_plot['mean']])
    if not nan_set:
        plot_lowlevel(plot_spec, ax, conditions, measurement_to_plot, plot_sim)

    # Beautify plots
    ax.set_xlabel(
        plot_spec.xLabel)
    ax.set_ylabel(
        plot_spec.yLabel)


def matches_plot_spec(df: pd.DataFrame,
                      col_id: str,
                      x_value: Union[float, str],
                      plot_spec: pd.Series) -> pd.Series:
    """
    constructs an index for subsetting of the dataframe according to what is
    specified in plot_spec.

    Parameters:
        df:
            pandas data frame to subset, can be from measurement file or
            simulation file
        col_id:
            name of the column that will be used for indexing in x variable
        x_value:
            subsetted x value
        plot_spec:
            visualization spec from the visualization file

    Returns:
        index:
            boolean series that can be used for subsetting of the passed
            dataframe
    """
    subset = (
        (df[col_id] == x_value) &
        (df[DATASET_ID] == plot_spec[DATASET_ID])
    )
    if plot_spec[Y_VALUES] == '':
        if len(df.loc[subset, OBSERVABLE_ID].unique()) > 1:
            ValueError(
                f'{Y_VALUES} must be specified in visualization table if '
                f'multiple different observables are available.'
            )
    else:
        subset &= (df[OBSERVABLE_ID] == plot_spec[Y_VALUES])
    return subset


def get_data_to_plot(plot_spec: pd.Series,
                     m_data: pd.DataFrame,
                     simulation_data: pd.DataFrame,
                     condition_ids: np.ndarray,
                     col_id: str,
                     simulation_field: str = SIMULATION) -> pd.DataFrame:
    """
    group the data, which should be plotted and return it as dataframe.

    Parameters:
        plot_spec:
            information about contains defined data format (visualization file)
        m_data:
            pandas data frame, contains defined data format (measurement file)
        simulation_data:
            pandas data frame, contains defined data format (simulation file)
        condition_ids:
            numpy array, containing all unique condition IDs which should be
            plotted in one figure (can be found in measurementData file,
            column simulationConditionId)
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
        index=condition_ids
    )

    for var_cond_id in condition_ids:

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
        subset = matches_plot_spec(m_data, col_id, var_cond_id, plot_spec)
        data_measurements = m_data.loc[
            subset,
            MEASUREMENT
        ]

        data_to_plot.at[var_cond_id, 'mean'] = np.mean(data_measurements)
        data_to_plot.at[var_cond_id, 'sd'] = np.std(data_measurements)

        if (plot_spec.plotTypeData == PROVIDED) & sum(subset):
            if len(m_data.loc[subset, NOISE_PARAMETERS].unique()) > 1:
                raise NotImplementedError(
                    f"Datapoints with inconsistent {NOISE_PARAMETERS} is "
                    f"currently not implemented. Stopping.")
            tmp_noise = m_data.loc[subset, NOISE_PARAMETERS].values[0]
            if isinstance(tmp_noise, str):
                raise NotImplementedError(
                    "No numerical noise values provided in the measurement "
                    "table. Stopping.")
            if isinstance(tmp_noise, Number) or tmp_noise.dtype == 'float64':
                data_to_plot.at[var_cond_id, 'noise_model'] = tmp_noise

        # standard error of mean
        data_to_plot.at[var_cond_id, 'sem'] = \
            np.std(data_measurements) / np.sqrt(len(data_measurements))

        # single replicates
        data_to_plot.at[var_cond_id, 'repl'] = \
            data_measurements

        if simulation_data is not None:
            simulation_measurements = simulation_data.loc[
                matches_plot_spec(simulation_data, col_id, var_cond_id,
                                  plot_spec),
                simulation_field
            ]
            data_to_plot.at[var_cond_id, 'sim'] = np.mean(
                simulation_measurements
            )

    return data_to_plot
