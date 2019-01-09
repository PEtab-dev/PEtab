#!/usr/bin/env python3

import plot_measurement
import plot_simulation
import matplotlib.pyplot as plt

DataFilePath = "measurementData_Fujita_SciSignal2010.tsv"
ConditionFilePath = "experimentalCondition_Fujita_SciSignal2010.tsv"

ax = plot_measurement.plot_measurementdata(DataFilePath, ConditionFilePath)
plot_simulation.plot_simulationdata(DataFilePath, ConditionFilePath, ax)
plt.show()