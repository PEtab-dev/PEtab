import pandas as pd
import generate_experimentId

#DataFilePath = "../../Benchmark-Models/hackathon_contributions_new_data_format/Fujita_SciSignal2010/measurementData_Fujita_SciSignal2010.tsv"
#ConditionFilePath = "../../Benchmark-Models/hackathon_contributions_new_data_format/Fujita_SciSignal2010/experimentalCondition_Fujita_SciSignal2010.tsv"

DataFilePath = "../../Benchmark-Models/hackathon_contributions_new_data_format/Sobotta_Frontiers2017/measurementData_Sobotta_Frontiers2017.tsv"
ConditionFilePath = "../../Benchmark-Models/hackathon_contributions_new_data_format/Sobotta_Frontiers2017/experimentalCondition_Sobotta_Frontiers2017.tsv"


measurement_data = pd.DataFrame.from_csv(
    DataFilePath, sep="\t", index_col=None)

measurement_data = generate_experimentId.generate_experimentId(measurement_data)

