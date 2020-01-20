# MEASUREMENTS

observableId = 'observableId'
preequilibrationConditionId = 'preequilibrationConditionId'
simulationConditionId = 'simulationConditionId'
measurement = 'measurement'
time = 'time'
observableParameters = 'observableParameters'
observableTransformation = 'observableTransformation'
noiseDistribution = 'noiseDistribution'
noiseParameters = 'noiseParameters'
datasetId = 'datasetId'
replicateId = 'replicateId'

measurement_df_req_cols = [
    observableId, preequilibrationConditionId, simulationConditionId,
    measurement, time, observableParameters, noiseParameters,
    noiseDistribution]

measurement_df_cols = [
    *measurement_df_req_cols, datasetId, replicateId]


# PARAMETERS

parameterId = 'parameterId'
parameterName = 'parameterName'
parameterScale = 'parameterScale'
lowerBound = 'lowerBound'
upperBound = 'upperBound'
nominalValue = 'nominalValue'
estimate = 'estimate'
priorType = 'priorType'
priorParameters = 'priorParameters'
objectivePriorType = 'objectivePriorType'
objectivePriorParameters = 'objectivePriorParameters'

parameter_df_req_cols = [
    parameterId, parameterScale, lowerBound, upperBound, nominalValue,
    estimate]

parameter_df_cols = [
    parameterId, parameterName, *parameter_df_req_cols[1:],
    priorType, priorParameters,
    objectivePriorType, objectivePriorParameters]


# CONDITIONS


# TRANSFORMATIONS

lin = 'lin'
log = 'log'
log10 = 'log10'


# NOISE MODELS

uniform = 'uniform'
normal = 'normal'
laplace = 'laplace'
