import main
import matplotlib.pyplot as plt

data_file_path = "https://raw.githubusercontent.com/LoosC/Benchmark-Models/" \
    "hackathon/hackathon_contributions_new_data_format/" \
    "Isensee_JCB2018/measurementData_Isensee_JCB2018.tsv"

condition_file_path = "https://raw.githubusercontent.com/LoosC/" \
    "Benchmark-Models/hackathon/hackathon_contributions_" \
    "new_data_format/Isensee_JCB2018/" \
    "experimentalCondition_Isensee_JCB2018.tsv"

visualization_file_path = "https://raw.githubusercontent.com/LoosC/"\
    "Benchmark-Models/visualization/hackathon_contributions"\
    "_new_data_format/Isensee_JCB2018/visualizationSpecific"\
    "ation_Isensee_JCB2018_2.tsv"
simulation_file_path = "https://raw.githubusercontent.com/LoosC/"\
    "Benchmark-Models/visualization/hackathon_contributions"\
    "_new_data_format/Isensee_JCB2018/simulationData"\
    "_Isensee_JCB2018.tsv"

# function to call, to plot your data and simulations
ax = main.plot_data_and_simulation(data_file_path, condition_file_path,
                                   visualization_file_path, simulation_file_path)
plt.show()
