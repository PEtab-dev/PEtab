import numpy as np
import pandas as pd


def get_data_to_plot(visualization_specification: pd.DataFrame,
                     measurement_data: pd.DataFrame,
                     simulation_data: pd.DataFrame,
                     condition_ids: np.ndarray,
                     i_visu_spec: int,
                     col_id: str):
    """
    group the data, which should be plotted and save it in pd.dataframe called
    'ms'.

    Parameters:
    ----------

    visualization_specification:
        pandas data frame, contains defined data format (visualization file)
    measurement_data:
        pandas data frame, contains defined data format (measurement file)
    simulation_data:
        pandas data frame, contains defined data format (simulation file)
    condition_ids:
        numpy array, containing all unique condition IDs which should be plotted in
        one figure (can be found in measurementData file,
        column simulationConditionId)
    i_visu_spec:
        int, current index (row number) of row which should be plotted in
        visualizationSpecification file
    col_id:
        str, the name of the column in visualization file, whose entries should be
        unique (depends on condition in column independentVariableName)

    Return:
    ----------

    ms: pandas data frame containing the data which should be plotted
    (Mean and Std)
    """

    # create empty dataframe for means and SDs
    ms = pd.DataFrame(
        columns=[
            'mean',
            'sd',
            'sem',
            'repl',
            'sim'],
        index=condition_ids)

    for var_cond_id in condition_ids:
        # get boolean vector which fulfill the requirements
        vec_bool_meas = ((measurement_data[col_id] == var_cond_id) &
                         (measurement_data['datasetId'] ==
                          visualization_specification.datasetId[i_visu_spec]))
        # get indices of rows with "True" values of vec_bool_meas
        ind_meas = [i_visu_spec for i_visu_spec, x in enumerate(vec_bool_meas) if x]

        # check that all entries for all columns-conditions are the same, for
        # grouping the measurement data
        if col_id != 'time':
            vec_bool_allcond = \
                ((measurement_data.preequilibrationConditionId[ind_meas[0]] ==
                    measurement_data.preequilibrationConditionId) &
                 (measurement_data.time[ind_meas[0]] ==
                     measurement_data.time) &
                 (measurement_data.observableParameters[ind_meas[0]] ==
                     measurement_data.observableParameters) &
                 (measurement_data.noiseParameters[ind_meas[0]] ==
                     measurement_data.noiseParameters) &
                 (measurement_data.observableTransformation[ind_meas[0]] ==
                     measurement_data.observableTransformation) &
                 (measurement_data.noiseDistribution[ind_meas[0]] ==
                     measurement_data.noiseDistribution))
        else:
            vec_bool_allcond = ((measurement_data.preequilibrationConditionId[
                ind_meas[0]] == measurement_data.preequilibrationConditionId) &
                (measurement_data.observableParameters[
                    ind_meas[0]] == measurement_data.observableParameters) &
                (measurement_data.noiseParameters[ind_meas[0]] ==
                    measurement_data.noiseParameters) &
                (measurement_data.observableTransformation[ind_meas[0]] ==
                    measurement_data.observableTransformation) &
                (measurement_data.noiseDistribution[ind_meas[0]] ==
                    measurement_data.noiseDistribution))
        # get indices of rows with "True" values, of vec_bool_allcond
        ind_bool_allcond = [i_visu_spec for i_visu_spec, x in enumerate(vec_bool_allcond) if x]
        # get intersection of ind_meas and ind_bool_allcond
        ind_intersec = np.intersect1d(ind_meas, ind_bool_allcond)

        # TODO: Here not the case: So, if entries of preequCondId,
        # time, observableParams,noiseParams, observableTransf,
        # noiseDistr are not the same, then this belongs not to the data of
        # interest, which should be in one group ->
        #  differ these data into different groups!
        if len(ind_intersec) != len(ind_meas):
            # find unique values in ind_meas that are not in ind_intersec
            unique_values = np.setdiff1d(ind_meas, ind_intersec)
        else:
            ind_intersec = ind_intersec

        # measurement_data[ind_meas].measurement.mean()
        ms.at[var_cond_id, 'mean'] = np.mean(
            measurement_data.measurement[ind_intersec])
        ms.at[var_cond_id, 'sd'] = np.std(
            measurement_data.measurement[ind_intersec])
        # standard error of mean
        ms.at[var_cond_id, 'sem'] = \
            np.std(measurement_data.measurement[ind_intersec]) / \
            np.sqrt(len(measurement_data.measurement[ind_intersec]))
        ms.at[var_cond_id, 'repl'] = \
            measurement_data.measurement[ind_intersec]

        ms.at[var_cond_id, 'sim'] = np.mean(
            simulation_data.simulatedData[ind_intersec])

    return ms
