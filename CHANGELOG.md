# PEtab changelog

### [Unreleased]

Data format:

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
