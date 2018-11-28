# Optimization problem data format specification

This document explains the data format used for the benchmark collection.


## Purpose

Providing a standardized way for specifying parameter estimation problems in systems biology, especially for the case of Ordinary Differential Equation (ODE) models. 


## Overview

This data format specifies a parameter estimation problems using a number of text-based files ([Systems Biology Markup Language (SBML)](http://sbml.org) and [Tab-Separated Values (TSV)](https://www.iana.org/assignments/media-types/text/tab-separated-values)) , i.e.

- An SBML model [SBML]

- A measurement file to fit the model to [TSV]

- A "condition" file specifying model inputs and condition-specific parameters [TSV]

The following sections will describe the minimum requirements of those components in the core standard, which should provide all information for defining the parameter estimation problem. 

Extensions of this format (e.g. additional columns in the measurement table) are possible and intended. However, those columns should provide extra information for example for plotting, or for more efficient parameter estimation, but they should not change the optimum of the optimization problem. Some optional extensions are described in the last section, "Extensions", of this document.

## SBML model definition

The model must be specified as valid SBML. Since parameter estimation is beyond the scope of SBML, there exists no standard way to specify observables (model outputs) and respective noise models. Therefore, we use the following convention.

### Observables 

In the SBML model, observables are specified as `AssignmentRules` assigning to parameters with `id`s starting with `observable_` followed by the `observableId` as in the corresponding column of the *measurement sheet* (see below).

E.g.
```
observable_pErk = observableParameter1 + observableParameter2*pErk 
```
where `observableParameter1` would be an offset, and `observableParameter2` a scaling parameter. 

### Noise model

Measurement noise can be specified as a numerical value in the `noiseParameters` column of the *measurement sheet* (see below), which will default to a Gaussian noise model with standard deviation as provided in `noiseParameters`.
  
Alternatively, more complex noise models can be specified for each observable, using additional `AssignmentRules`. Those noise model rules assign to `sigma_${observableId}` parameters. 
A noise model which accounts for relative and absolute contributions could, e.g., be defined as
```
sigma_pErk = noiseParameter1 + noiseParameter2*pErk 
```
with `noiseParameter1` denoting the absolute and `noiseParameter2` the relative contribution.

Any parameters named `noiseParameter${1..n}` *must* be overwritten in the `noiseParameters` column of the measurement file (see below).


## Condition table

The condition table species parameters for specific simulation condition (generally corresponding to different experimental conditions).

This is specified as tab-separated value file with condition-specific parameters in the following way:

| conditionId | conditionName | parameterId1 | ... | parameterId${n} |
|---|---|---|---|---| 
| conditionId1 | conditionName1 | NUMERIC&#124;parameterId | ...| ...
| conditionId2 | ... | ... | ...| ...
|... | ... | ... | ... |...| ...

Row names are condition names as referenced in the measurement table below. Column names are parameter names as given in the SBML model. These parameters will override any parameter values specified in the model.

Row- and column-ordering **are(?) arbitrary**. The `conditionName` column is optional. Additional columns **are|are not** allowed.


**TODO** This will no longer be the input table, what else is allowed here? 

**TODO** Do we allow specifying initial conditions anywhere?

**TODO** Are additional columns allowed here? With special prefix? 

**TODO** Related; Should Column-order matter?

**TODO** Do we allow non-sbml-model parameters here, as introduced in noiseParameters or observable parameters?

**TODO**: do we allow state names here, which will overwrite their dynamics?


## Measurements table

A tab-separated values files containing all measurements to be used for
model training or validation.

Expected to have the following named columns in any (but preferably this) order:

| observableId | preequilibrationConditionId | simulationConditionId | measurement	| ... 
|---|---|---|---|---|
| observableId | [conditionId] | conditionId | NUMERIC | 
|...|...|...|...|...|

*(wrapped for readability)*

| ... | time | observableParameters | noiseParameters | observableTransformation |
|---|---|---|---|---|
|... | NUMERIC&#124;'inf' | [parameterId&#124;NUMERIC[;parameterId&#124;NUMERIC][...]] | [parameterId&#124;NUMERIC[;parameterId&#124;NUMERIC][...]] | ['lin'(default)&#124;'log'&#124;'log10']
|...|...|...|...|...|

Fields in "[]" in the second row are optional and may be left empty. 

Additional (non-standard) columns may be added.  

**TODO** All entries case-sensitive? column names, string values, sbml ids ? 

### Detailed field description

- `observableId` [STRING, NOT NULL, REFERENCES(sbml.observableID)]
  
  Observable name matching the ID of the respective parameter in the SBML
    model (`observable_...`) 
    
  **TODO** What is the observable ID: observable_bla or only the latter part? 

- `preequilibrationConditionId` [STRING OR NULL, REFERENCES(conditionsTable.conditionID)]
 
  The `conditionId` to be used for preequilibration. E.g. for drug 
  treatments the model would be preequilibrated with the no-drug condition.
  Empty for no preequlibration.
  
  **TODO** Can preequilibrationConditionId column be omitted if all empty?
  
- `simulationConditionId` [STRING, NOT NULL, REFERENCES(conditionsTable.conditionID)]
  
  `conditionId` as provided in the condition table, specifying the condition-specific parameters used for simulation. 
  
- `measurement` [NUMERIC, NOT NULL]

  The measured value in the same units/scale as the model output.
  
- `time` [NUMERIC OR STRING, NOT NULL]

  Time point of the measurement in the time unit specified in the SBML model, numeric value or `inf` (lower-case) for steady-state measurements.
     
- `observableParameters` [STRING OR NULL]
  
  This field allows overriding or introducing condition-specific versions of the parameters
  defined in the model. The model can define observables (see above) containing place-holder parameters 
  which can be replaced by condition-specific dynamic or constant parameters.
  
  Placeholder parameters must be named ... **TODO** (with `n` ranging from 0?1? to n, without gaps). If the observable specified under `observableId` contains no placeholder, this field must be empty. If it contains `n > 0` placeholders, this field must hold `n` semicolon-separated numeric values or parameter names. No trailing semicolon should be added.
  
  Different lines for the same `observableId` may specify different parameters. This may be used to account for condition-specific or batch-specific parameters. This will translate into an extended optimization parameter vector.    
  
  **TODO** Optional if there are not observables with placeholders?
  
- `noiseParameters` [STRING]

  The measurement standard deviation or `NaN` if the corresponding sigma is a model 
  parameter.
  
  **TODO**  first finalize observableParameters

- `observableTransformation` [STRING]

  Transformation of the observable. `lin`, `log` or `log10`.

  **TODO** Can observableTransformation column be omitted if all lin?
  
  **TODO** What does this imply?
  
    
**TODO** Do we allow for custom cost functions or likelihood for non-normal case?


## Parameter table

A tab-separated value text file containing information on the parameters. One row per parameter with arbitrary order of rows and columns: 

| parameterId | parameterName | parameterScale | lowerBound  |upperBound | nominalValue | estimate | priorType | priorParameters | 
|---|---|---|---|---|---|---|---|---|
|STRING|STRING|log10&#124;lin&#124; **TODO**|NUMERIC|NUMERIC|NUMERIC|0&#124;1|**TODO**|**TODO**
|...|
|...|

Additional columns may be added.

- `parameterId` [STRING, NOT NULL, REFERENCES(sbml.parameterId)] 
  
  The `parameterId` of the parameter described in this row. This has be identical to the parameter IDs specified in the SBML model or in the `observableParameters` or `noiseParameters` column of the measurement table (see above).
  
  There must exist one line for each parameterId specified in the SBML model (except for placeholder parameter, see above) or the `observableParameters` or `noiseParameters` column of the measurement table.

- `parameterName` [STRING, OPTIONAL]
 
  Parameter name to be used e.g. for plotting etc. Can be chosen freely. May or may not coincide with the SBML parameter name.

- `parameterScale` [lin|log|log10]

  Scale of the parameter. The parameters and boundaries and the nominal parameter value in the following fields are expected to be given in this scale.

  **TODO** optional, NULL==lin?

- `lowerBound` [NUMERIC]
  
  Lower bound of the parameter used for optimization.
  
  **TODO** allow inf or empty?
  
- `upperBound` [NUMERIC]
 
  Upper bound of the parameter used for optimization.

- `nominalValue`
 
  Best values found by optimization or the value used for simulation for artificial data or fixed parameters (see `estimate`).
  
  **TODO** "Best values found by optimization": so they will be updated every time we find something better?

- `estimate` [BOOL 0|1]

  1 or 0, depending on, if the parameter is estimated (1) or set to a fixed value(0) (-> `nominalValue`).

- `priorType`

  Type of prior. Leave empty, if no priors. Normal/ Laplace etc.
  
  **TODO** optional?
  
  **TODO** what will be allowed?

- `priorParameters`

   Parameters for prior.
   
   **TODO** Numeric or also parameter names?


## Extensions

### Parameter table

TODO: 

Extra columns
- `hierarchicalOptimization` (optional)

  hierarchicalOptimization: 1 if parameter is optimized using hierarchical optimization approach. 0 otherwise.
