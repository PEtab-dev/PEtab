import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DataFilePath = "measurementData_Isensee_JCB2018.tsv"
ConditionFilePath = "parameters_Isensee_JCB2018.tsv"

# import measurement data
measurement_data = pd.DataFrame.from_csv(
    DataFilePath, sep="\t", index_col=None)
# import experimental condition
experimental_condition = pd.DataFrame.from_csv(
    ConditionFilePath, sep="\t")

observableId = np.array(measurement_data.observableId)
measurement = np.array(measurement_data.measurement)
simulationConditionId = np.array(measurement_data.simulationConditionId)
time = np.array(measurement_data.time)
replicateId = np.array(measurement_data.replicateId)

# get unique observable ID
uni_observableId = np.unique(observableId)

# for the same observable ID, get the measurement, time and condition
for i_uniobs, value_uniobs in enumerate(uni_observableId):
    index_uniobs = np.where(observableId == value_uniobs)[0]

    # replicateId, condition ID, measurement and time for unique observableId
    replicateId_uniobs = replicateId[index_uniobs]
    conditionId_uniobs = simulationConditionId[index_uniobs]
    measurement_uniobs = measurement[index_uniobs]
    time_uniobs = time[index_uniobs]

    # for the same replicate ID, get the measurement, time and condition
    uni_replicateId_uniobs = np.unique(replicateId_uniobs)
    for i_unirep_uniobs, val_unirep_uniobs in enumerate(uni_replicateId_uniobs):
        # one figure for each replicate
        fig,ax = plt.subplots()
        index_unirep_uniobs = np.where(replicateId_uniobs ==
                                       val_unirep_uniobs)[0]
        conditionId_unirep_uniobs = conditionId_uniobs[index_unirep_uniobs]
        measurement_unirep_uniobs = measurement_uniobs[index_unirep_uniobs]
        time_unirep_uniobs = time_uniobs[index_unirep_uniobs]

        # plot each condition
        uni_condition_unirep_uniobs = np.unique(conditionId_unirep_uniobs)
        for i_unicon_unirep_uniobs, val_unicon_unirep_uniobs in enumerate(
                uni_condition_unirep_uniobs):
            index_unicon_unirep_uniobs = np.where(conditionId_unirep_uniobs
                                                  ==
                                                  val_unicon_unirep_uniobs)[0]
            measurement_unicon_unirep_uniobs = measurement_unirep_uniobs[index_unicon_unirep_uniobs]
            time_unicon_unirep_uniobs = time_unirep_uniobs[index_unicon_unirep_uniobs]
            ax.plot(time_unicon_unirep_uniobs,
                    measurement_unicon_unirep_uniobs, 'x-',
                    label=val_unicon_unirep_uniobs)
            ax.set_xlabel('time')
            ax.set_ylabel('measurement')
        title_rep_obs = value_uniobs+'_'+val_unirep_uniobs
        ax.set_title(title_rep_obs)
        ax.legend()
        plt.show()