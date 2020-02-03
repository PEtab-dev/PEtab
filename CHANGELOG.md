# PEtab changelog

### 0.1.1

Library:
* Fix parameter mapping: include output parameters not present in SBML model
* Fix missing `petab/petab_schema.yaml` in source distribution
* Let get_placeholders return an (ordered) list of placeholders
* Deprecate `petab.problem.from_folder` and related functions
  (obsolete after introducing more flexible YAML files for grouping tables
  and models) 

### 0.1.0

Data format:

* Introduce observables table instead of SBML assignment rules for defining
  observation model (#244) (moves observableTransformation and noiseModel
  from the measurement table to the observables table)
* Allow initial concentrations / sizes in condition table (#238)
* Fixes and clarifications in the format documentation
* Changes in prior columns of the parameter table (#222)
* Introduced separate version number of file format, this release being
  version 1

Library:

* Adaptations to new file formats
* Various bugfixes and clean-up, especially in visualization and validator
* Parameter mapping changed to include all model parameters and not only
  those differing from the ones defined inside the SBML model
* Introduced constants for all field names and string options, replacing
  most string literals in the code (#228)
* Added unit tests and additional format validation steps
* Optional parallelization of parameter mapping (#205)
* Extended documentation (in-source and example Jupyter notebooks)


### 0.0.2

Bugfix release

* Fix `petablint` error
* Fix minor issues in `petab.visualize`


### 0.0.1

Data format:
* Update format and documentation with respect to data and parameter scales
  (#169)
* Define YAML schema for grouping PEtab files, also allowing for more complex
  combinations of files (#183)

Library:
* Refactor library. Reorganize `petab.core` functions.
* Fix visualization w/o condition names #142
* Extend validator
* Removed deprecated functions petab.Problem.get_constant_parameters
  and petab.sbml.constant_species_to_parameters
* Minor fixes and extensions


### 0.0.0a17

Data format: *No changes*

Library:
* Extended visualization support
* Add helper function and test case to deal with timepoint-specific parameters
  flatten_timepoint_specific_output_overrides (#128) (Closes #125)
* Fix get_noise_distributions: so far we got 'normal' everywhere due to 
  wrong grouping (#147)
* Fix create_parameter_df: Exclude rule targets (#149)
* Verify condition table column names occur as model parameters
  (Closes #150) (#151)
* More informative error messages in case of wrongly set observable and
  noise parameters (Closes #118) (#155)
* Update doc for copasi import and github installation (#158) 
* Extend validator to check if all required parameters are present in
  parameter table (Closes #43) (#159)
* Setup documentation for RTD (#161)
* Handle None in petab.core.split_parameter_replacement_list (Closes #121) 
* Fix(lint) correct handling of optional columns. Check before access.
* Remove obsolete generate_experiment_id.py (Closes #111) #166 

### 0.0.0a16 and earlier

See git history
