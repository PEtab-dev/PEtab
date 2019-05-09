import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import get_data_to_plot
import plotting_config
import petab
import seaborn as sns
sns.set()


data_file_path = "https://raw.githubusercontent.com/LoosC/Benchmark-Models/" \
               "hackathon/hackathon_contributions_new_data_format/" \
               "Isensee_JCB2018/measurementData_Isensee_JCB2018.tsv"

condition_file_path = "https://raw.githubusercontent.com/LoosC/" \
                    "Benchmark-Models/hackathon/hackathon_contributions_" \
                    "new_data_format/Isensee_JCB2018/" \
                    "experimentalCondition_Isensee_JCB2018.tsv"

#visualization_file_path = "https://raw.githubusercontent.com/LoosC/"\
#                        "Benchmark-Models/visualization/hackathon_contributions"\
#                        "_new_data_format/Isensee_JCB2018/visualizationSpecific"\
#                        "ation_Isensee_JCB2018.tsv"
visualization_file_path = "https://raw.githubusercontent.com/LoosC/"\
                        "Benchmark-Models/visualization/hackathon_contributions"\
                        "_new_data_format/Isensee_JCB2018/visualizationSpecific"\
                        "ation_Isensee_JCB2018_2.tsv"
simulation_file_path = "https://raw.githubusercontent.com/LoosC/"\
                        "Benchmark-Models/visualization/hackathon_contributions"\
                        "_new_data_format/Isensee_JCB2018/simulationData"\
                        "_Isensee_JCB2018.tsv"

# Set Options for plots
plt.rcParams['font.size'] = 10                  # possible options: see: plt.rcParams.keys()
plt.rcParams['axes.titlesize'] = 10
plt.rcParams['figure.figsize'] = [20,10]
plt.rcParams['errorbar.capsize'] = 2
plt.plot_simulation = True

subplots = True

# import measurement data, experimental condition, visualization specification, simulation data
measurement_data = petab.get_measurement_df(data_file_path)
experimental_condition = petab.get_condition_df(condition_file_path)
visualization_specification = pd.read_csv(
        visualization_file_path, sep="\t", index_col=None)
simulation_data = pd.read_csv(
        simulation_file_path, sep="\t", index_col=None)

# Set Colormap
#ccodes = ['#8c510a','#bf812d','#dfc27d','#f6e8c3','#c7eae5','#80cdc1','#35978f','#01665e']
sns.set_palette("colorblind")

# get unique plotIDs
uni_plotIds, plotInd = np.unique(visualization_specification.plotId, return_index=True)

# Initiate subplots
if subplots:
    num_subplot = len(uni_plotIds)
else:
    num_subplot = 1

num_row = np.round(np.sqrt(num_subplot))
num_col = np.ceil(num_subplot / num_row)

fig, ax = plt.subplots(int(num_row), int(num_col), squeeze=False)

# loop over unique plotIds
for i_plot_id, var_plot_id in enumerate(uni_plotIds):

    # setting axis indices
    if subplots:
        axx = int(np.ceil((i_plot_id+1)/ num_col))-1
        axy = int(((i_plot_id+1) - axx * num_col))-1
    else:
        axx = 0
        axy = 0

    # get indices for specific plotId
    ind_plot = visualization_specification['plotId'] == var_plot_id


    for i in visualization_specification[ind_plot].index.values:
        # get datasetID and independent variable of first entry of plot1
        dataset_id = visualization_specification.datasetId[i]
        #indep_var = visualization_specification.independentVariable[i]
        indep_var = visualization_specification.xValues[i]

        # define index to reduce measurement_data to data linked to datasetId
        ind_dataset = measurement_data['datasetId'] == dataset_id

        # gather simulationConditionIds belonging to datasetId
        uni_condition_id = np.unique(measurement_data[ind_dataset].simulationConditionId)
        clmn_name_unique = 'simulationConditionId'

        # Case seperation indepParameter custom, time or condition
        if indep_var not in ['time', "condition"]:

            # extract conditions (plot input) from condition file
            ind_cond = experimental_condition.index.isin(uni_condition_id)
            conditions = experimental_condition[ind_cond][indep_var]

            ms = get_data_to_plot.get_data_to_plot(visualization_specification, measurement_data, simulation_data, uni_condition_id,
                                                       i, clmn_name_unique)

            # # set xScale
            # if visualization_specification.xScale[i] == 'lin':
            #     ax[axx, axy].set_xscale("linear")
            # elif visualization_specification.xScale[i] == 'log10':
            #     ax[axx, axy].set_xscale("log")
            # elif visualization_specification.xScale[i] == 'order':        # equidistant
            #     ax[axx, axy].set_xscale("linear")
            #     # check if conditions are monotone decreasing or increasing
            #     if np.all(np.diff(conditions) < 0):             # monotone decreasing
            #         xlabel = conditions[::-1]                   # reversing
            #         conditions = range(len(conditions))[::-1]   # reversing
            #         ax[axx, axy].set_xticks(range(len(conditions)), xlabel)
            #     elif np.all(np.diff(conditions) > 0):
            #         print('monotone increasing')
            #         xlabel = conditions
            #         conditions = range(len(conditions))
            #         ax[axx, axy].set_xticks(range(len(conditions)), xlabel)
            #     else:
            #         print('Error: x-conditions do not coincide, some are mon. increasing,'\
            #               ' some monotonically decreasing')
            #
            # conditions = conditions + visualization_specification.xOffset[i]
            #
            # if visualization_specification.plotTypeData[i] == 'MeanAndSD':
            #     ax[axx, axy].errorbar(conditions, ms['mean'], ms['sd'], linestyle='-', marker='.',
            #                             label = visualization_specification[ind_plot].legendEntry[i])
            # elif visualization_specification.plotTypeData[i] == 'MeanAndSEM':
            #     ax[axx, axy].errorbar(conditions, ms['mean'], ms['sem'], linestyle='-', marker='.',
            #                           label=visualization_specification[ind_plot].legendEntry[i])
            # elif visualization_specification.plotTypeData[i] == 'replicate':  # plotting all measurement data
            #     for ii in range(0,len(ms['repl'])):
            #         for k in range(0,len(ms.repl[ii])):
            #             ax[axx, axy].plot(conditions[conditions.index.values[ii]],
            #                               ms.repl[ii][ms.repl[ii].index.values[k]], 'x')
            # ax[axx, axy].legend()
            # ax[axx, axy].set_title(visualization_specification.plotName[i])

            ax = plotting_config.plotting_config(visualization_specification, ax, axx, axy, conditions, ms, ind_plot, i, plt)

        elif indep_var == 'condition':

            ms = get_data_to_plot.get_data_to_plot(visualization_specification, measurement_data, simulation_data, uni_condition_id,
                                                       i, clmn_name_unique)
            # # barplot
            # x_pos = range(len(visualization_specification[ind_plot]))       # how many x-values (how many bars)
            # x_name = visualization_specification[ind_plot].legendEntry[i]
            #
            # ax[axx, axy].bar(x_name, ms['mean'], yerr=ms['sd'])
            # ax[axx, axy].set_title(visualization_specification.plotName[i])
            ax = plotting_config.plotting_config(visualization_specification, ax, axx, axy, conditions, ms, ind_plot, i, plt)

        elif indep_var == 'time':

            # obtain unique observation times
            uni_times = np.unique(measurement_data[ind_dataset].time)

            clmn_name_unique = 'time'

            # group measurement values for each conditionId/unique time
            ms = get_data_to_plot.get_data_to_plot(visualization_specification, measurement_data, simulation_data, uni_times, i,
                                                       clmn_name_unique)

            # uni_times = uni_times + visualization_specification.xOffset[i]

            # ax[axx, axy].errorbar(uni_times, ms['mean'], ms['sd'], linestyle='-', marker='.',
            #              label=visualization_specification[ind_plot].legendEntry[i]
            #              )
            # ax[axx, axy].legend()
            # ax[axx, axy].set_title(visualization_specification.plotName[i])
            ax = plotting_config.plotting_config(visualization_specification, ax, axx, axy, uni_times, ms, ind_plot, i, plt)

    #ax[axx, axy].set_xlabel(visualization_specification.independentVariableName[i])
    ax[axx, axy].set_xlabel(visualization_specification.xLabel[i])
    ax[axx, axy].set_ylabel(visualization_specification.yLabel[i])



    if subplots is False:
        filename='Plot'+str(i_plot_id)+'.png'
        plt.savefig(filename)
        ax[0,0].clear()

if subplots:
    plt.savefig("Plot")

   # plt.show()