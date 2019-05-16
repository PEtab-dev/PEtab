import pandas as pd
import numpy as np
import numbers


def generate_experiment_id(measurement_data):
    '''
    automatically generate the experimentId:
    every row which shares the observableParameters (if provided),
    noiseParameters and observableTransformation gets
    the same experimentId, for the assignment all numeric values in the
    noiseParameters are considered to be the same

    Parameters:
    ----------

    measurement_data: pandas data frame for measurement data

    Return:
    ----------

    measurement_data: pandas data frame for measurement data with column for
    experimentId added

    '''
    observable_parameters = np.array(measurement_data.observableParameters)
    noise_parameters = np.array(measurement_data.noiseParameters)
    observable_transformation = np.array(
        measurement_data.observableTransformation)

    # check if there is empty values in the observableParameter column, should
    # not occur!
    if np.any(observable_parameters == 'empty'):
        raise AssertionError("NOOOOOOO! observable_parameter must have an "
                             "entry!")

    # noiseParameters should always has an entry
    if np.any(noise_parameters == 'empty'):
        raise AssertionError("NOOOOOOO! noise_parameters must have an entry!")

    # help functions to check for numeric values and nans in arrays
    isnumeric = np.vectorize(isinstance)
    isnan_vectorized = np.vectorize(np.isnan)

    # assign 'empty' to missing observableParameters
    tmp_observable_parameters = observable_parameters
    tmp_ind = np.where(isnumeric(observable_parameters, numbers.Number))
    if tmp_ind[0].size == 0:
        tmp_observable_parameters == observable_parameters
    else:
        tmp_observable_parameters[tmp_ind[0][
            np.where(isnan_vectorized(observable_parameters[tmp_ind[0]]))]
        ] = 'empty'

    # all numeric values in noiseParameters are temporarily set to 0 to be
    # treated the same
    tmp_noise_parameters = noise_parameters
    tmp_noise_parameters[
        np.where(isnumeric(noise_parameters, numbers.Number))
    ] = 0

    # add new column for experimentId
    measurement_data = measurement_data.assign(
        experimentId=pd.Series(np.zeros(len(measurement_data)))
    )

    ind_no_exp_id = np.array(range(len(measurement_data.experimentId)))
    count = 1
    # assign experiment ID when data share the same observable parameters,
    # noise parameters and observable transformation
    while ind_no_exp_id.size > 0:
        ind_exp_id = np.where(
            (observable_parameters == observable_parameters[ind_no_exp_id[
                0]]) *
            (tmp_noise_parameters == tmp_noise_parameters[ind_no_exp_id[
                0]]) *
            (observable_transformation ==
             observable_transformation[ind_no_exp_id[0]]))
        for ind in ind_exp_id[0]:
            measurement_data.loc[ind, 'experimentId'] = 'experiment_' + str(
                count)

        # extract measurements with no assigned experimentId
        ind_no_exp_id = np.where(measurement_data.experimentId == 0)[0]

        # if it does not decrease there might be a missing value in the
        # observableTransformation or noiseParameter
        print(str(ind_no_exp_id.size) + ' measurements left to be assigned')
        count = count + 1

    print(str(count - 1) + ' experimentIds added.')
    return measurement_data
