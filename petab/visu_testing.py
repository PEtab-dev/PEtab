from petab.visualize import plot_data_and_simulation
import matplotlib.pyplot as plt

folder = "/home/erika/Documents/Python/Benchmark-Models/" \
         "hackathon_contributions_new_data_format/Isensee_JCB2018/"

data_file_path = folder + "measurementData_Isensee_JCB2018.tsv"
condition_file_path = folder + "experimentalCondition_Isensee_JCB2018.tsv"
visualization_file_path = folder + "visualizationSpecification_Isensee_JCB2018.tsv"
simulation_file_path = folder + "simulationData_Isensee_JCB2018.tsv"

# function to call, to plot data and simulations
ax = plot_data_and_simulation(data_file_path,
                              condition_file_path,
                              visualization_file_path,
                              simulation_file_path)
plt.show()