import pandas as pd
import numpy as np


def plot_simulationdata(DataFilePath, ConditionFilePath, ax):
    '''
    plot simulation data grouped by variable ID

    Parameters:
    ----------

    DataFilePath: string, file path of measurement data
    ConditionFilePath: string, file path of condition file

    Return:
    ----------

    axis: axis of figures
    '''

    # import measurement data
    measurement_data = pd.DataFrame.from_csv(
        DataFilePath, sep="\t", index_col=None)
    # import experimental condition
    experimental_condition = pd.DataFrame.from_csv(
        ConditionFilePath, sep="\t")

    observableId = np.array(measurement_data.observableId)
    measurement = np.array(measurement_data.measurement)
    simulationCondition = np.array(measurement_data.simulationConditionId)
    time = np.array(measurement_data.time)

    # get unique observable ID
    uni_observableId = np.unique(observableId)

    # group measurement, time and condition Id by observable Id
    for i_uniobs, val_uniobs in enumerate(uni_observableId):
        ind_uniobs = np.where(observableId == val_uniobs)[0]
        measurement_uniobs = measurement[ind_uniobs]
        time_uniobs = time[ind_uniobs]
        condition_uniobs = simulationCondition[ind_uniobs]

        uni_condition = np.unique(condition_uniobs)
        # measurement value for each unique condition
        for val_unicon in uni_condition:
            ind_unicon = np.where(condition_uniobs == val_unicon)
            time_unicon = time_uniobs[ind_unicon]
            measurement_unicon = measurement_uniobs[ind_unicon]

            condition_name = experimental_condition.conditionName[val_unicon]
            ax[i_uniobs].plot(time_unicon, measurement_unicon,
                              label=condition_name + '_' + 'simulation')

        ax[i_uniobs].legend()
    return ax
