# Optimization problem data format specification

This document explains the data format used for the benchmark collection.


## Purpose

Providing a standardized way for specifying parameter estimation problems in
systems biology, especially for the case of Ordinary Differential Equation
(ODE) models.


## Overview

This data format specifies a parameter estimation problems using a number of
text-based files ([Systems Biology Markup Language (SBML)](http://sbml.org)
and [Tab-Separated Values
(TSV)](https://www.iana.org/assignments/media-types/text/tab-separated-values)), i.e.

- An SBML model [SBML]

- A measurement file to fit the model to [TSV]

- A condition file specifying model inputs and condition-specific parameters
  [TSV]

- A parameter file specifying optimization parameters and related information
  [TSV]

The following sections will describe the minimum requirements of those
components in the core standard, which should provide all information for
defining the parameter estimation problem.

Extensions of this format (e.g. additional columns in the measurement table)
are possible and intended. However, those columns should provide extra
information for example for plotting, or for more efficient parameter
estimation, but they should not change the optimum of the optimization
problem. Some optional extensions are described in the last section,
"Extensions", of this document.

**General remarks**
- All model entities column and row names are case-sensitive
- Fields in "[]" in the second row are optional and may be left empty.

## SBML model definition

The model must be specified as valid SBML. Since parameter estimation is
beyond the scope of SBML, there exists no standard way to specify observables
(model outputs) and respective noise models. Therefore, we use the following
convention.

### Observables

In the SBML model, observables are specified as `AssignmentRules` assigning to
parameters with `id`s starting with `observable_` followed by the
`observableId` as in the corresponding column of the *measurement table* (see
below).

E.g.
```
observable_pErk = observableParameter1_pErk + observableParameter2_pErk*pErk
```
where `observableParameter1_pErk` would be an offset, and `observableParameter2_pErk` a
scaling parameter for the observable `pErk`. The observable parameter names have the structure: `observableParameter${indexOfObservableParameter}_${observableId}` to facilitate automatic recognition. The specific values or parameters are assigned in the *measurement table*.


### Noise model

Measurement noise can be specified as a numerical value in the
`noiseParameters` column of the *measurement table* (see below), which will
default to a Gaussian noise model with standard deviation as provided in
`noiseParameters`.

Alternatively, more complex noise models can be specified for each observable,
using additional `AssignmentRules`. Those noise model rules assign to
`sigma_${observableId}` parameters.
A noise model which accounts for relative and absolute contributions could,
e.g., be defined as
```
sigma_pErk = noiseParameter1_pErk + noiseParameter2_pErk*pErk
```
with `noiseParameter1_pErk` denoting the absolute and `noiseParameter2_pErk` the
relative contribution for the observable `pErk`. The noise parameter names have the structure: `noiseParameter${indexOfNoiseParameter}_${observableId}` to facilitate automatic recognition. The specific values or parameters are assigned in the *measurement table*.

Any parameters named `noiseParameter${1..n}` *must* be overwritten in the
`noiseParameters` column of the measurement file (see below).


## Condition table

The condition table specifies parameters or *constant* species for specific
simulation condition (generally corresponding to different experimental
conditions).

This is specified as tab-separated value file with condition-specific
species/parameters in the following way:

| conditionId | [conditionName] | parameterOrStateId1 | ... | parameterOrStateId${n} |
|---|---|---|---|---|
| conditionId1 | conditionName1 | NUMERIC&#124;parameterId | ...| ...
| conditionId2 | ... | ... | ...| ...
|... | ... | ... | ... |...| ...

Row names are condition names as referenced in the measurement table below.
Column names are global parameter IDs or IDs of constant species as given in
the SBML model. These parameters will override any parameter values specified
in the model. `parameterOrStateId`s and `conditionId`s must be unique.

Row- and column-ordering are arbitrary, although specifying `parameterId`
first may improve human readability. The `conditionName` column is optional.
Additional columns are *not* allowed.

*Note 1:* Instead of adding additional columns to the condition table, they
can easily be added to a separate file, since every row of the condition table
has `parameterId` as unique key.

## Measurement table

A tab-separated values files containing all measurements to be used for
model training or validation.

Expected to have the following named columns in any (but preferably this)
order:

| observableId | [preequilibrationConditionId] | simulationConditionId | measurement | ... 
|---|---|---|---|---|
| observableId | [conditionId] | conditionId | NUMERIC | 
|...|...|...|...|...|

*(wrapped for readability)*

| ... | time | [observableParameters] | [noiseParameters] | [observableTransformation] | [noiseDistribution]
|---|---|---|---|---|---|
|... | NUMERIC&#124;'inf' |[parameterId&#124;NUMERIC[;parameterId&#124;NUMERIC][...]] | [parameterId&#124;NUMERIC[;parameterId&#124;NUMERIC][...]] | ['lin'(default)&#124;'log'&#124;'log10'] | ['laplace'&#124;'normal'] | 
|...|...|...|...|...|...|

Additional (non-standard) columns may be added.

## Visualization table

A tab-separated values files containing the specification of visualisations. Plots are in general collections of different datasets as specified using their `datasetId`.  

Expected to have the following named columns in any (but preferably this)
order:

| plotId | [plotName] | plotTypeSimulation | plotTypeData | datasetId | ... 
|---|---|---|---|---|
| plotId | [plotName] | LinePlot | MeanAndSD | datasetId |
|...|...|...|...|...|

*(wrapped for readability)*

| ... |  independentVariable | [independentVariableOffset] | [independentVariableName] | [legendEntry]
|---|---|---|---|---|
|... |  [parameterId] | [NUMERIC] | [STRING] | [STRING] | 
|...|...|...|...|...|...|

The `independentVariable`is the variable over which the dataset is visualised. For time-response data, this should be `time`, for dose response data the respective `parameterOrStateId`. The numerical values of the `independentVariable` are shown on the x-axis, while the values of the observables are shown of the respective y-axis.

If different datasets are assigned to the same `plotID`, multiple datasets are overlaid. The name of the datasets is indicated by the corresponding `legendEntry`, which is by default the `datasetId`.

The visualization types is specified by `plotTypeSimulation` and `plotTypeData`. Possible choices include LinePlot, BarPlot, MeanAndSD and MeanAndSEM. In addition, XScale and YScale, Color, etc. can be specified.

### Detailed field description

- `observableId` [STRING, NOT NULL, REFERENCES(sbml.observableID)]

  Observable ID with a matching parameter in the SBML model with ID
`observable_${observableId}`

- `preequilibrationConditionId` [STRING OR NULL,
REFERENCES(conditionsTable.conditionID)]

  The `conditionId` to be used for preequilibration. E.g. for drug
  treatments the model would be preequilibrated with the no-drug condition.
  Empty for no preequlibration.

- `simulationConditionId` [STRING, NOT NULL,
REFERENCES(conditionsTable.conditionID)]

  `conditionId` as provided in the condition table, specifying the
condition-specific parameters used for simulation.

- `measurement` [NUMERIC, NOT NULL]

  The measured value in the same units/scale as the model output.

- `time` [NUMERIC OR STRING, NOT NULL]

  Time point of the measurement in the time unit specified in the SBML model,
numeric value or `inf` (lower-case) for steady-state measurements.

- `observableParameters` [STRING OR NULL]

  This field allows overriding or introducing condition-specific versions of
  parameters defined in the model. The model can define observables (see above)
  containing place-holder parameters which can be replaced by 
  condition-specific dynamic or constant parameters. Placeholder parameters 
  must be named `observableParameter${n}_${observableId}`
  with `n` ranging from 1 (not 0) to the number of placeholders for the given
  observable, without gaps.
  If the observable specified under `observableId` contains no placeholders,
  this field must be empty. If it contains `n > 0` placeholders, this field 
  must hold `n` semicolon-separated numeric values or parameter names. No 
  trailing semicolon must be added.

  Different lines for the same `observableId` may specify different
  parameters. This may be used to account for condition-specific or
  batch-specific parameters. This will translate into an extended optimization
  parameter vector.

  All placeholders defined in the model must be overwritten here. If there are
  not placeholders in the model, this column may be omitted.

- `noiseParameters` [STRING]

  The measurement standard deviation or `NaN` if the corresponding sigma is a
  model parameter.

  Numeric values or parameter names are allowed. Same rules apply as for
  `observableParameters` in the previous point.

- `observableTransformation` [STRING]

  Transformation of the observable. `lin`, `log` or `log10`. Defaults to 'lin'.

- `noiseDistribution` [STRING: 'normal' or 'laplace']

   Assumed Noise distribution for the given measurement. Only normally or
  Laplace distributed noise is currently allowed. Defaults to `normal`. If
  `normal`, the specified `noiseParameters` will be interpreted as standard 
  deviation (*not* variance).

## Parameter table

A tab-separated value text file containing information on model parameters.

This table must comprise the following parameters:
- All parameters from the SBML model, except for:
    - `constant` and/or `boundaryCondition` parameters (see SBML specs)
    - placeholder parameters (see `observableParameters` and `noiseParameters`
      above)
    - parameters included as column names in the *condition table*
- Named parameter overrides introduced in the *conditions table*
- Named parameter overrides introduced in the *measurement table*

One row per parameter with arbitrary order of rows and columns:

| parameterId | [parameterName] | parameterScale | lowerBound  |upperBound | nominalValue | estimate | [priorType] | [priorParameters] |
|---|---|---|---|---|---|---|---|---|
|STRING|STRING|log10&#124;lin&#124;log|NUMERIC|NUMERIC|NUMERIC|0&#124;1|**TODO**|**TODO**
|...|...|...|...|...|...|...|...|...|

Additional columns may be added.

Detailed column description:

- `parameterId` [STRING, NOT NULL, REFERENCES(sbml.parameterId)]

  The `parameterId` of the parameter described in this row. This has be
  identical to the parameter IDs specified in the SBML model or in the
  `observableParameters` or `noiseParameters` column of the measurement table
  (see above).

  There must exist one line for each parameterId specified in the SBML model
  (except for placeholder parameter, see above) or the `observableParameters` or
  `noiseParameters` column of the measurement table.

- `parameterName` [STRING, OPTIONAL]

  Parameter name to be used e.g. for plotting etc. Can be chosen freely. May
  or may not coincide with the SBML parameter name.

- `parameterScale` [lin|log|log10]

  Scale of the parameter. The parameters and boundaries and the nominal
  parameter value in the following fields are expected to be given in this 
  scale.

- `lowerBound` [NUMERIC]

  Lower bound of the parameter used for optimization.
  Optional, if `estimate==0`.

- `upperBound` [NUMERIC]

  Upper bound of the parameter used for optimization. 
  Optional, if `estimate==0`.

- `nominalValue` [NUMERIC]

  Some parameter value (scale as specified in `parameterScale`) to be used if 
  the parameter is not subject to estimation (see `estimate` below). 
  Optional, unless `estimate==0`.

- `estimate` [BOOL 0|1]

  1 or 0, depending on, if the parameter is estimated (1) or set to a fixed
  value(0) (see `nominalValue`).

- `priorType`

  Type of prior. Leave empty or omit column, if no priors. Normal/ Laplace etc.

  [**Issue #17**](https://github.com/ICB-DCM/PEtab/issues/17)


- `priorParameters`

  Parameters for prior.

  [**Issue #17**](https://github.com/ICB-DCM/PEtab/issues/17)
  Numeric or also parameter names? (issue #17)


## Parameter estimation problems combining multiple models

[**Issue #49**](https://github.com/ICB-DCM/PEtab/issues/49)

## Extensions

### Parameter table

Extra columns

- `hierarchicalOptimization` (optional)

  hierarchicalOptimization: 1 if parameter is optimized using hierarchical
  optimization approach. 0 otherwise.
