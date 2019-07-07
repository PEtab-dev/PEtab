import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .get_data_to_plot import get_data_to_plot
from .plotting_config import plotting_config
import petab
import seaborn as sns
sns.set()


def plot_data_and_simulation(data_file_path: str,
                             condition_file_path: str,
                             visualization_file_path: str,
                             simulation_file_path: str):
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
    visualization_file_path: str
        Path to the vizualization specification file.
    simulation_file_path: str
        Path to the simulation output data file.

    Returns
    -------
    ax: Axis object of the created plot.
    """

    # Set Options for plots
    # possible options: see: plt.rcParams.keys()
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 10
    plt.rcParams['figure.figsize'] = [20, 10]
    plt.rcParams['errorbar.capsize'] = 2
    plt.plot_simulation = True

    subplots = True

    # import measurement data, experimental condition, visualization
    # specification, simulation data
    measurement_data = petab.get_measurement_df(data_file_path)
    experimental_condition = petab.get_condition_df(condition_file_path)
    visualization_specification = pd.read_csv(
        visualization_file_path, sep="\t", index_col=None)
    simulation_data = pd.read_csv(
        simulation_file_path, sep="\t", index_col=None)

    # Set Colormap
    # ccodes = \
    # ['#8c510a','#bf812d','#dfc27d','#f6e8c3', \
    #  '#c7eae5','#80cdc1','#35978f','#01665e']
    sns.set_palette("colorblind")

    # get unique plotIDs
    uni_plot_ids, plot_ind = np.unique(
        visualization_specification.plotId, return_index=True)

    # Initiate subplots
    if subplots:
        num_subplot = len(uni_plot_ids)
    else:
        num_subplot = 1

    num_row = np.round(np.sqrt(num_subplot))
    num_col = np.ceil(num_subplot / num_row)

    # initialize figure
    fig, ax = plt.subplots(int(num_row), int(num_col), squeeze=False)

    # loop over unique plotIds
    for i_plot_id, var_plot_id in enumerate(uni_plot_ids):

        # setting axis indices
        if subplots:
            axx = int(np.ceil((i_plot_id + 1) / num_col)) - 1
            axy = int(((i_plot_id + 1) - axx * num_col)) - 1
        else:
            axx = 0
            axy = 0

        # get indices for specific plotId
        ind_plot = visualization_specification['plotId'] == var_plot_id

        for i_visu_spec in visualization_specification[ind_plot].index.values:
            # get datasetID and independent variable of first entry of plot1
            dataset_id = visualization_specification.datasetId[i_visu_spec]
            indep_var = visualization_specification.xValues[i_visu_spec]

            # define index to reduce measurement_data to data linked to
            # datasetId
            ind_dataset = measurement_data['datasetId'] == dataset_id

            # gather simulationConditionIds belonging to datasetId
            uni_condition_id = np.unique(
                measurement_data[ind_dataset].simulationConditionId)
            col_name_unique = 'simulationConditionId'

            # Case seperation indepParameter custom, time or condition
            if indep_var not in ['time', "condition"]:

                # extract conditions (plot input) from condition file
                ind_cond = experimental_condition.index.isin(uni_condition_id)
                conditions = experimental_condition[ind_cond][indep_var]

                ms = get_data_to_plot(
                    visualization_specification, measurement_data,
                    simulation_data, uni_condition_id, i_visu_spec,
                    col_name_unique)

                ax = plotting_config(
                    visualization_specification, ax, axx, axy, conditions,
                    ms, ind_plot, i_visu_spec, plt)

            elif indep_var == 'condition':

                ms = get_data_to_plot(
                    visualization_specification, measurement_data,
                    simulation_data, uni_condition_id, i_visu_spec,
                    col_name_unique)

                ax = plotting_config(
                    visualization_specification, ax, axx, axy, conditions, ms,
                    ind_plot, i_visu_spec, plt)

            elif indep_var == 'time':

                # obtain unique observation times
                uni_times = np.unique(measurement_data[ind_dataset].time)

                col_name_unique = 'time'

                # group measurement values for each conditionId/unique time
                ms = get_data_to_plot(
                    visualization_specification, measurement_data,
                    simulation_data, uni_times, i_visu_spec, col_name_unique)

                ax = plotting_config(
                    visualization_specification, ax, axx, axy, uni_times, ms,
                    ind_plot, i_visu_spec, plt)

        ax[axx, axy].set_xlabel(
            visualization_specification.xLabel[i_visu_spec])
        ax[axx, axy].set_ylabel(
            visualization_specification.yLabel[i_visu_spec])

    # finalize figure
    fig.tight_layout()

    return ax
