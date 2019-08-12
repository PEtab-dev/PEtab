import numpy as np
import pandas as pd


def get_data_to_plot(vis_spec: pd.DataFrame,
                     m_data: pd.DataFrame,
                     simulation_data: pd.DataFrame,
                     condition_ids: np.ndarray,
                     i_visu_spec: int,
                     col_id: str):
    """
    group the data, which should be plotted and save it in pd.dataframe called
    'ms'.

    Parameters:
    ----------

    vis_spec:
        pandas data frame, contains defined data format (visualization file)
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

    Return:
    ----------

    data_to_plot: pandas data frame containing the data which should be plotted
    (Mean and Std)
    """

    # create empty dataframe for means and SDs
    data_to_plot = pd.DataFrame(
        columns=['mean', 'sd', 'sem', 'repl', 'sim'],
        index=condition_ids)

    for var_cond_id in condition_ids:
        # get boolean vector which fulfill the requirements
        vec_bool_meas = ((m_data[col_id] == var_cond_id) & (m_data['datasetId']
                         == vis_spec.datasetId[i_visu_spec]))
        # get indices of rows with True values of vec_bool_meas
        ind_meas = [i_visu_spec for i_visu_spec,
                    x in enumerate(vec_bool_meas) if x]

        # check that all entries for all columns-conditions are the same:
        # check correct observable
        bool_observable = (m_data.observableParameters[ind_meas[0]] ==
                           m_data.observableParameters)
        # check correct observable transformation
        bool_obs_transform = (m_data.observableTransformation[ind_meas[0]] ==
                              m_data.observableTransformation)
        # check correct noise parameters
        # TODO: This might be too restrictive. Maybe rethink this...
        bool_noise = (m_data.noiseParameters[ind_meas[0]] ==
                      m_data.noiseParameters)
        # check correct noise distribution
        bool_noise_dist = (m_data.noiseDistribution[ind_meas[0]] ==
                           m_data.noiseDistribution)
        # check correct time point
        bool_time = True
        if col_id != 'time':
            bool_time = (m_data.time[ind_meas[0]] == m_data.time)
        # check correct preqeuilibration condition
        pre_cond = m_data.preequilibrationConditionId[ind_meas[0]]
        bool_preequ = (pre_cond == m_data.preequilibrationConditionId)
        # special handling is needed, if preequilibration cond is left empty
        if (type(pre_cond) == np.float64) and np.isnan(pre_cond):
            bool_preequ = np.isnan(m_data.preequilibrationConditionId)

        # combine all boolean vectors
        vec_bool_allcond = (bool_preequ & bool_observable & bool_noise &
                            bool_obs_transform & bool_noise_dist & bool_time)

        # get indices of rows with "True" values, of vec_bool_allcond
        ind_bool_allcond = [i_visu_spec for i_visu_spec,
                            x in enumerate(vec_bool_allcond) if x]

        # get intersection of ind_meas and ind_bool_allcond
        ind_intersec = np.intersect1d(ind_meas, ind_bool_allcond)

        # see Issue #117
        # TODO: Here not the case: So, if entries in measurement file:
        #  preequCondId, time, observableParams, noiseParams, observableTransf,
        # noiseDistr are not the same, then  -> differ these data into
        # different groups!
        # now: go in simulationConditionId, search group of unique
        # simulationConditionId e.g. rows 0,6,12,18 share the same
        # simulationCondId, then check if other column entries are the same
        # (now: they are), then take intersection of rows 0,6,12,18 and checked
        # other same columns (-> now: 0,6,12,18) and then go on with code.
        # if there is at some point a difference in other columns, say e.g.
        # row 12,18 have different noiseParams than rows 0,6, the actual code
        # would take rows 0,6 and forget about rows 12,18

        # m_data[ind_meas].measurement.mean()
        data_to_plot.at[var_cond_id, 'mean'] = np.mean(
            m_data.measurement[ind_intersec])
        data_to_plot.at[var_cond_id, 'sd'] = np.std(
            m_data.measurement[ind_intersec])

        # standard error of mean
        data_to_plot.at[var_cond_id, 'sem'] = np.std(m_data.measurement[
            ind_intersec]) / np.sqrt(len(m_data.measurement[ind_intersec]))
        data_to_plot.at[var_cond_id, 'repl'] = m_data.measurement[ind_intersec]

        if simulation_data is not None:
            data_to_plot.at[var_cond_id, 'sim'] = np.mean(
                simulation_data.simulatedData[ind_intersec])

    return data_to_plot
