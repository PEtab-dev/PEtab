# PEtab data format specification


## Version: 1

This document explains the PEtab data format.


## Purpose

Providing a standardized way for specifying parameter estimation problems in
systems biology, especially for the case of Ordinary Differential Equation
(ODE) models.


## Overview

The PEtab data format specifies a parameter estimation problem using a number
of text-based files ([Systems Biology Markup Language (SBML)](http://sbml.org)
and
[Tab-Separated Values (TSV)](https://www.iana.org/assignments/media-types/text/tab-separated-values)),
i.e.

- An SBML model [SBML]

- A measurement file to fit the model to [TSV]

- A condition file specifying model inputs and condition-specific parameters
  [TSV]

- A parameter file specifying optimization parameters and related information
  [TSV]

- (optional) A simulation file, which has the same format as the measurement
  file, but contains model simulations [TSV]

- (optional) A visualization file, which contains specifications how the data
  and/or simulations should be plotted by the visualization routines [TSV]

![Files constituting a PEtab problem](gfx/petab_files.png)

The following sections will describe the minimum requirements of those
components in the core standard, which should provide all information for
defining the parameter estimation problem.

Extensions of this format (e.g. additional columns in the measurement table)
are possible and intended. However, those columns should provide extra
information for example for plotting, or for more efficient parameter
estimation, but they should not affect the optimization problem as such. 
Some optional extensions are described in the last section, "Extensions", of
 this document.

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
where `observableParameter1_pErk` would be an offset, and
`observableParameter2_pErk` a scaling parameter for the observable `pErk`.
The observable parameter names have the structure:
`observableParameter${indexOfObservableParameter}_${observableId}` to
facilitate automatic recognition. The specific values or parameters are
assigned in the *measurement table*.


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
with `noiseParameter1_pErk` denoting the absolute and `noiseParameter2_pErk`
the relative contribution for the observable `pErk`. The noise parameter names
have the structure: `noiseParameter${indexOfNoiseParameter}_${observableId}`
to facilitate automatic recognition. The specific values or parameters are
assigned in the *measurement table*.

Any parameters named `noiseParameter${1..n}` *must* be overwritten in the
`noiseParameters` column of the measurement file (see below).


## Condition table

The condition table specifies parameters or *constant* species for specific
simulation conditions (generally corresponding to different experimental
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

Values for condition parameters may be provided either as numeric values, or
as parameter IDs. In case parameter IDs are provided, they need to be defined
in the SBML model, the parameter table or both. 

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

| observableId | [preequilibrationConditionId] | simulationConditionId | measurement | time |...
|---|---|---|---|---|---|
| observableId | [conditionId] | conditionId | NUMERIC | NUMERIC&#124;'inf' |
|...|...|...|...|...|...|

*(wrapped for readability)*

| ... | [observableParameters] | [noiseParameters] | [observableTransformation] | [noiseDistribution]
|---|---|---|---|---|
|... | [parameterId&#124;NUMERIC[;parameterId&#124;NUMERIC][...]] | [parameterId&#124;NUMERIC[;parameterId&#124;NUMERIC][...]] | ['lin'(default)&#124;'log'&#124;'log10'] | ['laplace'&#124;'normal'] |
|...|...|...|...|...|

Additional (non-standard) columns may be added. If the additional plotting 
functionality of PEtab should be used, such columns could be

| ... | [datasetId] | [replicateId]  | ... |
|---|---|---|---|
|... | [String] | [String] | ... | 
|...|...|...|...|

where `datasetId` is a necessary column to use particular plotting 
functionality, and `replicateId` is optional, which can be used to group 
replicates and plot error bars. 


### Detailed field description

- `observableId` [STRING, NOT NULL, REFERENCES(sbml.observableID)]

  Observable ID with a matching parameter in the SBML model with ID
`observable_${observableId}`

- `preequilibrationConditionId` [STRING OR NULL,
REFERENCES(conditionsTable.conditionID), OPTIONAL]

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

- `observableParameters` [STRING OR NULL, OPTIONAL]

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

- `noiseParameters` [STRING, OPTIONAL]

  The measurement standard deviation or `NaN` if the corresponding sigma is a
  model parameter.

  Numeric values or parameter names are allowed. Same rules apply as for
  `observableParameters` in the previous point.

- `observableTransformation` [STRING, OPTIONAL]

  Transformation of the observable and measurement for computing the objective
  function.
  `lin`, `log` or `log10`. Defaults to 'lin'.
  The measurements and model outputs are both assumed to be provided in linear
  space.

- `noiseDistribution` [STRING: 'normal' or 'laplace', OPTIONAL]

  Assumed Noise distribution for the given measurement. Only normally or
  Laplace distributed noise is currently allowed. Defaults to `normal`. If
  `normal`, the specified `noiseParameters` will be interpreted as standard
  deviation (*not* variance).

- `datasetId` [STRING, OPTIONAL]

  The datasetId is used to group certain measurements to datasets. This is
  typically the case for data points which belong to the same observable,
  the same simulation and preequilibration condition, the same noise model,
  the same observable tranformation and the same observable parameters.
  This grouping makes it possible to use the plotting routines which are
  provided in the PEtab repository.

- `replicateId` [STRING, OPTIONAL]

  The replicateId can be used to discern replicates with the same
  datasetId, which is helpful for plotting e.g. error bars.


## Parameter table

A tab-separated value text file containing information on model parameters.

This table *must* include the following parameters:
- Named parameter overrides introduced in the *conditions table*,
  unless defined in the SBML model
- Named parameter overrides introduced in the *measurement table*

and *must not* include:
- Placeholder parameters (see `observableParameters` and `noiseParameters`
  above)
- Parameters included as column names in the *condition table*
- Parameters that are AssignmentRule targets in the SBML model

it *may* include:
- Any SBML model parameter that was not excluded above
- Named parameter overrides introduced in the *conditions table*

One row per parameter with arbitrary order of rows and columns:

| parameterId | [parameterName] | parameterScale | lowerBound  |upperBound | nominalValue | estimate | [priorType] | [priorParameters] |
|---|---|---|---|---|---|---|---|---|
|STRING|STRING|log10&#124;lin&#124;log|NUMERIC|NUMERIC|NUMERIC|0&#124;1|*see below*|*see below*
|...|...|...|...|...|...|...|...|...|

Additional columns may be added.


### Detailed field description:

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
  Must be provided in linear space, independent of `parameterScale`.

- `upperBound` [NUMERIC]

  Upper bound of the parameter used for optimization.
  Optional, if `estimate==0`.
  Must be provided in linear space, independent of `parameterScale`.

- `nominalValue` [NUMERIC]

  Some parameter value to be used if
  the parameter is not subject to estimation (see `estimate` below).
  Must be provided in linear space, independent of `parameterScale`.
  Optional, unless `estimate==0`.

- `estimate` [BOOL 0|1]

  1 or 0, depending on, if the parameter is estimated (1) or set to a fixed
  value(0) (see `nominalValue`).

- `initializationPriorType` [STRING, OPTIONAL]

  Prior types used for sampling of initial points for optimization. Sampled
  points are clipped to lie inside the parameter boundaries specified by
  `lowerBound` and `upperBound`. Defaults to `parameterScaleUniform`.

  Possible prior types are:

    - *uniform*: flat prior on linear parameters
    - *normal*: Gaussian prior on linear parameters
    - *laplace*: Laplace prior on linear parameters
    - *logNormal*: exponentiated Gaussian prior on linear parameters
    - *logLaplace*: exponentiated Laplace prior on linear parameters
    - *parameterScaleUniform* (default): Flat prior on original parameter
      scale (equivalent to "no prior")
    - *parameterScaleNormal*: Gaussian prior on original parameter scale
    - *parameterScaleLaplace*: Laplace prior on original parameter scale

- `initializationPriorParameters` [STRING, OPTIONAL]

  Prior parameters used for sampling of initial points for optimization,
  separated by a semicolon. Defaults to `lowerBound;upperBound`.

  So far, only numeric values will be supported, no parameter names. 
  Parameters for the different prior types are:
  
    - uniform: lower bound; upper bound
    - normal: mean; standard deviation (**not** variance)
    - laplace: location; scale
    - logNormal: parameters of corresp. normal distribution (see: normal)
    - logLaplace: parameters of corresp. Laplace distribution (see: laplace)
    - parameterScaleUniform: lower bound; upper bound
    - parameterScaleNormal: mean; standard deviation (**not** variance)
    - parameterScaleLaplace: location; scale

- `objectivePriorType` [STRING, OPTIONAL]

  Prior types used for the objective function during optimization or sampling.
  For possible values, see `initializationPriorType`.

- `objectivePriorParameters` [STRING, OPTIONAL]

  Prior parameters used for the objective function during optimization.
  For more detailed documentation, see `initializationPriorParameters`.   


## Visualization table

A tab-separated value file containing the specification of the visualization
routines which come with the PEtab repository. Plots are in general 
collections of different datasets as specified using their `datasetId` (if 
provided) inside the measurement table.

Expected to have the following columns in any (but preferably this)
order:

| plotId | [plotName] | plotTypeSimulation | plotTypeData | datasetId | ...
|---|---|---|---|---|---|
| plotId | [plotName] | LinePlot | MeanAndSD | datasetId | ...
|...|...|...|...|...|...|

*(wrapped for readability)*

| ... | [xValues] | [xOffset] | [xLabel] | [xScale] | ...
|---|---|---|---|---|---|
|... |  [parameterId] | [NUMERIC] | [STRING] | [STRING] | ...
|...|...|...|...|...|...|

*(wrapped for readability)*

| ... | [yValues] | [yOffset] | [yLabel] | [yScale] | [legendEntry] |  ...
|---|---|---|---|---|---|---|
|... |  [observableId] | [NUMERIC] | [STRING] | [STRING] | [STRING] | ...
|...|...|...|...|...|...|...|


### Detailed field description:

- `plotId` [STRING, NOT NULL]

  An ID which corresponds to a specific plot. All datasets with the same
  plotId will be plotted into the same axes object.

- `plotName` [STRING]

  A name for the specific plot.

- `plotTypeSimulation` [STRING]

  The type of the corresponding plot, can be `LinePlot` or `BarPlot`. Default
  is `LinePlot`.

- `plotTypeData`

  The type how replicates should be handled, can be `MeanAndSD`,
  `MeanAndSEM`, `replicate` (for plotting all replicates separately), or
  `provided` (if numeric values for the noise level are provided in the
  measurement table). Default is `MeanAndSD`.

 - `datasetId` [STRING, NOT NULL, REFERENCES(measurementTable.datasetId)]

  The datasets, which should be grouped into one plot.

 - `xValues` [STRING]

  The independent variable, which will be plotted on the x-axis. Can be 
  `time` (default, for time resolved data), or it can be `parameterOrStateId`
  for dose-response plots. The corresponding numeric values will be shown on
  the x-axis.

 - `xOffset` [NUMERIC]

  Possible data-offsets for the independent variable (default is `0`).

 - `xLabel` [STRING]

  Label for the x-axis.

- `xScale` [STRING]

  Scale of the independent variable, can be `lin`, `log`, or `log10`.

- `yValues` [observableId, REFERENCES(measurementTable.observableId)]

  The observable which should be plotted on the y-axis.

- `yOffset` [NUMERIC]

  Possible data-offsets for the observable (default is `0`).

- `yLabel` [STRING]

  Label for the y-axis.

- `yScale` [STRING]

  Scale of the observable, can be `lin`, `log`, or `log10`.

- `legendEntry` [STRING]

  The name that should be displayed for the corresponding dataset in the
  legend and which defaults to `datasetId`.


### Extensions

Additional columns, such as `Color`, etc. may be specified.


## YAML file for grouping files

To link the SBML model, measurement table, condition table, etc. in an
unambiguous way, we use a [YAML](https://yaml.org/) file.

This file also allows specifying a PEtab version (as the format is not unlikely
to change in the future).

Furthermore, this can be used to describe parameter estimation problems
comprising multiple models (more details below).

The format is described in the schema
[../petab/petab_schema.yaml](_static/petab_schema.yaml), which allows for
easy validation.


### Parameter estimation problems combining multiple models

Parameter estimation problems can comprise multiple models. For now, PEtab
allows to specify multiple SBML models with corresponding condition and
measurement tables, and one joint parameter table. This means that the parameter
namespace is global. Therefore, parameters with the same ID in different models
will be considered identical.
