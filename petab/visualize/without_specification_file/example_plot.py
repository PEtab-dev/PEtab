#!/usr/bin/env python3

import plot_measurement
import plot_simulation
import matplotlib.pyplot as plt

data_file_path = "https://raw.githubusercontent.com/LoosC/Benchmark-Models/" \
               "hackathon/hackathon_contributions_new_data_format/" \
               "Fujita_SciSignal2010/measurementData_Fujita_SciSignal2010.tsv"

condition_file_path = "https://raw.githubusercontent.com/LoosC/" \
                    "Benchmark-Models/hackathon/hackathon_contributions_" \
                    "new_data_format/Fujita_SciSignal2010/" \
                    "experimentalCondition_Fujita_SciSignal2010.tsv"

ax = plot_measurement.plot_measurementdata(data_file_path, condition_file_path)
plot_simulation.plot_simulationdata(data_file_path, condition_file_path, ax)
plt.show()
