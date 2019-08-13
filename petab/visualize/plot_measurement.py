import pandas as pd
import numpy as np
from petab.visualize import plot_data_and_simulation


def plot_measurements_by_observable(data_file_path, condition_file_path):
    '''
    plot measurement data grouped by observable ID.
    A simple wrapper around the more complex function plot_data_and_simulation.

    Parameters:
    ----------

    DataFilePath: str
        file path of measurement data
    ConditionFilePath: str
        file path of condition file

    Return:
    ----------

    axis: axis of figures
    '''

    # import measurement data
    measurement_data = pd.DataFrame.from_csv(
        data_file_path, sep="\t", index_col=None)
    # import experimental condition
    experimental_condition = pd.DataFrame.from_csv(
        condition_file_path, sep="\t")

    # get unique observable ID
    observable_id = np.array(measurement_data.observableId)
    uni_observable_id = np.unique(observable_id)
    observable_id_list = [str(obsId) for obsId in uni_observable_id]

    # use new routine now
    ax = plot_data_and_simulation(data_file_path, condition_file_path,
                                  observable_id_list=observable_id_list)

    return ax
