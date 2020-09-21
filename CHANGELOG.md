# PEtab changelog

## 0.1 series

### 0.1.10

*Fixed deployment setup, no further changes.*

### 0.1.9

Library:

* Allow URL as filenames for YAML files and SBML models (Closes #187) (#459)
* Allow model time in observable formulas (#445)
* Make float parsing from CSV round-trip (#444)
* Validator: Error message for missing IDs, with line numbers. (#467)
* Validator: Detect duplicated observable IDs (#446)
* Some documentation and CI fixes / updates
* Visualization: Add option to save visualization specification (#457)
* Visualization: Column XValue not mandatory anymore (#429)
* Visualization: Add sorting of indices of dataframes for the correct sorting
  of x-values (#430)
* Visualization: Default value for the column x_label in vis_spec (#431)


### 0.1.8

Library:

* Use ``core.is_empty`` to check for empty values (#434)
* Move tests to python 3.8 (#435)
* Update to libcombine 0.2.6 (#437)
* Make float parsing from CSV round-trip (#444)
* Lint: Allow model time in observable formulas (#445)
* Lint: Detect duplicated observable ids (#446)
* Fix likelihood calculation with missing values (#451)

Documentation:

* Move format documentation to restructuredtext format (#452)
* Document all noise distributions and observable scales (#452)
* Fix documentation for prior distribution (#449)

Visualization:

* Make XValue column non-mandatory (#429)
* Apply correct condition sorting (#430)
* Apply correct default x label (#431)


### 0.1.7

Documentation:

* Update coverage and links of supporting tools
* Update explanatory figure


### 0.1.6

Library:

* Fix handling of empty columns for residual calculation (#392)
* Allow optional fixing of fixed parameters in parameter mapping (#399)
* Fix function to flatten out time-point specific overrides (#404)
* Add function to create a problem yaml file (#398)
* Allow merging of multiple parameter files (#407)

Documentation:

* In README, add to the overview table the coverage for the supporting tools,
  and links and usage examples (various commits)
* Show REAMDE on readthedocs documentation front page (#400)
* Correct description of observable and noise formulas (#401)
* Update documentation on optional visualization values (#405, #419)

Visualization:

* Fix sorting problem (#396)
* More generously handle optional values (#405, #419)
* Create dataset id also for simulation dataframe (#408)
* Extend test suite for visualization (#418)


### 0.1.5

Library:

* New create empty observable function (issue 386) (#387)
* Deprecate petab.sbml.globalize_parameters (#381)
* Fix computing log10 likelihood (#380)
* Documentation update and typehints for visualization  (#372)
* Ordered result of `petab.get_output_parameters`
* Fix missing argument to parameters.create_parameter_df

Documentation:
* Add overview of supported PEtab feature in toolboxes
* Add contribution guide
* Fix optional values in documentation (#378)


### 0.1.4

Library:

* Fixes / updates in functions for computing llh and chi2
* Allow and require output parameters defined in observable table to be defined in parameter table
* Fix merge_preeq_and_sim_pars_condition which incorrectly assumed lists
  instead of dicts
* Update parameter mapping to deal with species and compartments in
  condition table
* Removed `petab.migrations.sbml_observables_to_table`

  For converting older PEtab files to observable table format, use one of the
  previous releases

* Visualization:
  * Fix various issues with get_data_to_plot
  * Fixed various issues with expected presence of optional columns


### 0.1.3

File format:

* Updated documentation
* Observables table in YAML file now mandatory in schema (was implicitly 
  mandatory before, as observable table was required already)

Library:
* petablint:
  * Fix: allow specifying observables file via CLI (Closes #302)
  * Fix: nominalValue is optional unless estimated!=1 anywhere (Fixes #303)
  * Fix: handle undefined observables more gracefully (Closes #300) (#351)
* Parameter mapping: 
  * Fix / refactor parameter mapping (breaking change) (#344)
    (now performing parameter value and scale mapping together)
  * check optional measurement cols in mapping (#350)
* allow calculating llhs (#349), chi2 values (#348) and residuals (#345)
* Visualization
  * Basic Scatterplots & lot of bar plot fixes (#270)
  * Fix incorrect length of bool `bool_preequ` when subsetting with ind_meas 
    (Closes #322)
* make libcombine optional (#338)


### 0.1.2

Library:

* Extensions and fixes for the visualization functions (#255, #262)
* Allow to extract fixed|free and scaled|non-scaled parameters (#256, #268, #273)
* Various fixes (esp. #264)
* Add function to get observable ids (#269)
* Improve documentation (esp. #289)
* Set default column for simulation results to 'simulation'
* Add support for COMBINE archives (#271)
* Fix sbml observables to table
* Improve prior and dataframe tests (#285, #286, #297)
* Add function to get parameter table with all default values (#288)
* Move tests to github actions (#281)
* Check for valid identifiers
* Fix handling of empty values in dataframes
* Allow to get numeric values in parameter mappings in scaled form (#308)

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

## 0.0 series

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
