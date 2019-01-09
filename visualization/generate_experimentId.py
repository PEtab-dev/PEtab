import pandas as pd
import numpy as np
import numbers

def generate_experimentId(measurement_data):
    '''
    automatically generate the experimentId:
    every row which shares the observableParameters (if provided), noiseParameters and observableTransformation gets
    the same experimentId, for the assignment all numeric values in the noiseParameters are considered to be the same

    Parameters:
    ----------

    measurement_data: pandas data frame for measurement data

    Return:
    ----------

    measurement_data: pandas data frame for measurement data with column for experimentId added

    '''
    observableParameters = np.array(measurement_data.observableParameters)
    noiseParameters = np.array(measurement_data.noiseParameters)
    observableTransformation = np.array(measurement_data.observableTransformation)

    # check if there occurs the name 'nan' in the observableParameter column, should not occur!
    checkNaming = np.where(observableParameters == 'empty')
    if checkNaming[0].size > 0:
        print('error')

    # but noiseParameters should always has an entry
    checkNaming = np.where(noiseParameters == 'empty')
    if checkNaming[0].size > 0:
        print('error')

    # help functions to check for numeric values and nans in arrays
    isnumeric = np.vectorize(isinstance)
    isnanVectorized = np.vectorize(np.isnan)

    # assign 'empty' to missing observableParameters
    tmp_observableParameters = observableParameters
    tmp_ind = np.where(isnumeric(observableParameters, numbers.Number))
    tmp_observableParameters[tmp_ind[0][np.where(isnanVectorized(observableParameters[tmp_ind[0]]))]] = 'empty'

    # all numeric values in noiseParameters are temporarily set to 0 to be treated the same
    tmp_noiseParameters = noiseParameters
    tmp_noiseParameters[np.where(isnumeric(noiseParameters,numbers.Number))] = 0

    # add new column for experimentId
    measurement_data = measurement_data.assign(experimentId=pd.Series(np.zeros(len(measurement_data))))

    ind_noExpId = np.where(measurement_data.experimentId == 0)
    count = 1
    while ind_noExpId[0].size > 0:
        ind_expId = np.where((observableParameters == observableParameters[ind_noExpId[0][0]])*
                             (tmp_noiseParameters == tmp_noiseParameters[ind_noExpId[0][0]])*
                             (observableTransformation == observableTransformation[ind_noExpId[0][0]]))
        for ind in ind_expId[0]:
            measurement_data.experimentId[ind] = 'experiment_' + str(count)

        # extract measurements with no assigned experimentId
        ind_noExpId = np.where(measurement_data.experimentId == 0)

        # if it does not decrease there might be a missing value in the observableTransformation or noiseParameter
        print(str(len(ind_noExpId[0])) + ' measurements left to be assigned')
        count = count + 1

    print(str(count-1) + ' experimentIds added.')
    return measurement_data
