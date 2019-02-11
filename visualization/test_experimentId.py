import pandas as pd
import generate_experimentId


DataFilePath = "https://raw.githubusercontent.com/LoosC/Benchmark-Models/" \
               "hackathon/hackathon_contributions_new_data_format/Sobotta_" \
               "Frontiers2017/measurementData_Sobotta_Frontiers2017.tsv"

measurement_data = pd.DataFrame.from_csv(
    DataFilePath, sep="\t", index_col=None)

measurement_data = generate_experimentId.generate_experimentId\
    (measurement_data)

