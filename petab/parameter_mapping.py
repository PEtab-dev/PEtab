"""Functions related to mapping parameter from model to parameter estimation
problem"""

import pandas as pd
import numpy as np
import libsbml
import numbers
from . import lint
from . import core
from typing import List, Tuple, Dict, Union


def get_optimization_to_simulation_parameter_mapping(
        condition_df: pd.DataFrame,
        measurement_df: pd.DataFrame,
        parameter_df: pd.DataFrame = None,
        sbml_model: libsbml.Model = None,
        par_sim_ids=None,
        simulation_conditions=None,
        warn_unmapped: bool = True) -> List[Tuple[List, List]]:
    """
    Create array of mappings from PEtab-problem to SBML parameters.

    The length of the returned array is n_conditions, each entry is a tuple of
    two arrays of length n_par_sim, listing the optimization parameters or
    constants to be mapped to the simulation parameters, first for
    preequilibration (empty if no preequilibration condition is specified),
    second for simulation. NaN is used where no mapping exists.

    If no `par_sim_ids` is passed, parameter ordering will be the one obtained
    from `get_model_parameters()`.

    Parameters
    ----------
    condition_df, measurement_df, parameter_df:
        The dataframes in the PEtab format.

        parameter_df is optional if par_sim_ids is provided

    sbml_model:
        The sbml model with observables and noise specified according to the
        petab format. Optional if par_sim_ids is provided.

    par_sim_ids: list of str, optional
        Ids of the simulation parameters. If not passed,
        these are generated from the files automatically. However, passing
        them can ensure having the correct order.

    simulation_conditions: pd.DataFrame
        Table of simulation conditions as created by
        `petab.get_simulation_conditions`.

    warn_unmapped:
        If True, log warning regarding unmapped parameters
    """
    # Ensure inputs are okay
    perform_mapping_checks(measurement_df)

    if simulation_conditions is None:
        simulation_conditions = core.get_simulation_conditions(measurement_df)

    if par_sim_ids is None:
        par_sim_ids = core.get_model_parameters(sbml_model)

    mapping = []
    for condition_ix, condition in simulation_conditions.iterrows():
        cur_measurement_df = core.get_rows_for_condition(
            measurement_df, condition)

        if 'preequilibrationConditionId' not in condition \
                or not isinstance(condition.preequilibrationConditionId, str) \
                or not condition.preequilibrationConditionId:
            preeq_map = []
        else:
            preeq_map = get_parameter_mapping_for_condition(
                condition_id=condition.preequilibrationConditionId,
                is_preeq=True,
                cur_measurement_df=cur_measurement_df,
                condition_df=condition_df,
                parameter_df=parameter_df, sbml_model=sbml_model,
                par_sim_ids=par_sim_ids, warn_unmapped=warn_unmapped
            )

        sim_map = get_parameter_mapping_for_condition(
            condition_id=condition.simulationConditionId,
            is_preeq=False,
            cur_measurement_df=cur_measurement_df,
            condition_df=condition_df,
            parameter_df=parameter_df, sbml_model=sbml_model,
            par_sim_ids=par_sim_ids, warn_unmapped=warn_unmapped
        )
        mapping.append((preeq_map, sim_map),)
    return mapping


def get_parameter_mapping_for_condition(
        condition_id: str,
        is_preeq: bool,
        cur_measurement_df: pd.DataFrame,
        condition_df: pd.DataFrame,
        parameter_df: pd.DataFrame = None,
        sbml_model: libsbml.Model = None,
        par_sim_ids=None,
        warn_unmapped: bool = True) -> List:
    """
    Create array of mappings from PEtab-problem to SBML parameters for the
    given condition.

    The length of the returned array of length n_par_sim, listing the
    optimization parameters or constants to be mapped to the simulation
    parameters. NaN is used where no mapping exists.

    If no `par_sim_ids` is passed, parameter ordering will be the one obtained
    from `get_model_parameters()`.

    Parameters
    ----------
    condition_id: Condition ID for which to perform mapping

    is_preeq: If true, output parameters will not be mapped

    cur_measurement_df: Measurement sub-table for current condition

    condition_df, parameter_df:
        The dataframes in the PEtab format.

        parameter_df is optional if par_sim_ids is provided

    sbml_model:
        The sbml model with observables and noise specified according to the
        petab format. Optional if par_sim_ids is provided.

    par_sim_ids: list of str, optional
        Ids of the simulation parameters. If not passed,
        these are generated from the files automatically. However, passing
        them can ensure having the correct order.

    warn_unmapped:
        If True, log warning regarding unmapped parameters
    """
    perform_mapping_checks(cur_measurement_df)

    if par_sim_ids is None:
        par_sim_ids = core.get_model_parameters(sbml_model)

    # initialize mapping matrix of shape n_par_sim_ids
    # for the case of matching simulation and optimization parameter vector
    mapping = par_sim_ids[:]

    # Lookup table
    par_sim_id_to_ix = {
        name: idx for idx, name in enumerate(par_sim_ids)
    }

    _apply_dynamic_parameter_overrides(mapping, condition_id,
                                       condition_df, parameter_df,
                                       par_sim_id_to_ix)

    if not is_preeq:
        _apply_output_parameter_overrides(mapping, cur_measurement_df,
                                          par_sim_id_to_ix)

    fill_in_nominal_values(mapping, parameter_df)

    # TODO fill in fixed parameters (#103)

    core.handle_missing_overrides(mapping, warn=warn_unmapped)
    return mapping


def _apply_output_parameter_overrides(
        mapping: List,
        cur_measurement_df: pd.DataFrame,
        par_sim_id_to_ix: Dict[str, int]) -> None:
    """
    Apply output parameter overrides to the parameter mapping list for a given
    condition as defined in the measurement table (observableParameter,
    noiseParameters).

    Arguments:
        mapping: parameter mapping list
        cur_measurement_df:
            Subset of the measurement table for the current condition
        par_sim_id_to_ix: mapping of model parameter id to index
    """
    for _, row in cur_measurement_df.iterrows():
        # we trust that the number of overrides matches (see above)
        overrides = core.split_parameter_replacement_list(
            row.observableParameters)
        _apply_overrides_for_observable(mapping, row.observableId,
                                        'observable',
                                        overrides, par_sim_id_to_ix)

        overrides = core.split_parameter_replacement_list(row.noiseParameters)
        _apply_overrides_for_observable(mapping, row.observableId, 'noise',
                                        overrides, par_sim_id_to_ix)


def _apply_overrides_for_observable(
        mapping: list,
        observable_id: str,
        override_type: str,
        overrides: list,
        par_sim_id_to_ix: Dict[str, int]) -> None:
    """
    Apply parameter-overrides for observables and noises to mapping
    matrix.

    Arguments:
        mapping: mapping list to which to apply overrides
        observable_id: observable ID
        override_type: 'observable' or 'noise'
        overrides: list of overrides for noise or observable parameters
        par_sim_id_to_ix: mapping of model parameter id to index
    """
    for i, override in enumerate(overrides):
        overridee_id = f'{override_type}Parameter{i+1}_{observable_id}'
        par_sim_ix = par_sim_id_to_ix[overridee_id]
        mapping[par_sim_ix] = override


def _apply_dynamic_parameter_overrides(mapping,
                                       condition_id: str,
                                       condition_df: pd.DataFrame,
                                       par_sim_id_to_ix):
    """Apply dynamic parameter overrides from condition table (in-place).

    Arguments:
        mapping, par_sim_id_to_ix:
            see get_parameter_mapping_for_condition
        condition_df: PEtab condition and parameter table
    """
    for overridee_id in condition_df.columns:
        if overridee_id == 'conditionName':
            continue
        if condition_df[overridee_id].dtype != 'O':
            continue

        overrider_id = condition_df.loc[condition_id, overridee_id]
        mapping[par_sim_id_to_ix[overridee_id]] = overrider_id


def fill_in_nominal_values(mapping: list, parameter_df: pd.DataFrame) -> None:
    """Replace non-estimated parameters in mapping list for a given condition
    by nominalValues provided in parameter table.

    Arguments:
        mapping: mapping lists obtained from
            get_parameter_mapping_for_condition
        parameter_df:
            PEtab parameter table
    """

    if parameter_df is None:
        return
    if 'estimate' not in parameter_df:
        return

    overrides = {row.name: row.nominalValue for _, row
                 in parameter_df.iterrows() if row.estimate != 1}

    for i_val, val in enumerate(mapping):
        if isinstance(val, str):
            try:
                mapping[i_val] = overrides[val]
                # rescale afterwards. if there the parameter is not
                # overridden, the previous line raises and we save the
                # lookup

                # all overrides will be scaled to 'lin'
                if 'parameterScale' in parameter_df:
                    scale = parameter_df.loc[val, 'parameterScale']
                    if scale == 'log':
                        mapping[i_val] = np.exp(mapping[i_val])
                    elif scale == 'log10':
                        mapping[i_val] = 10**mapping[i_val]
            except KeyError:
                pass


def get_optimization_to_simulation_scale_mapping(
        parameter_df: pd.DataFrame,
        mapping_par_opt_to_par_sim: List[Tuple[List, List]],
        measurement_df: pd.DataFrame,
        simulation_conditions: Union[dict, pd.DataFrame] = None
) -> List[Tuple[List, List]]:
    """Get parameter scale mapping for all conditions"""
    mapping_scale_opt_to_scale_sim = []

    if simulation_conditions is None:
        simulation_conditions = core.get_simulation_conditions(measurement_df)

    # iterate over conditions
    for condition_ix, condition in simulation_conditions.iterrows():
        if 'preequilibrationConditionId' not in condition \
                or not isinstance(condition.preequilibrationConditionId, str) \
                or not condition.preequilibrationConditionId:
            preeq_map = []
        else:
            preeq_map = get_scale_mapping_for_condition(
                parameter_df=parameter_df,
                mapping_par_opt_to_par_sim=mapping_par_opt_to_par_sim[
                    condition_ix][0]
            )

        sim_map = get_scale_mapping_for_condition(
            parameter_df=parameter_df,
            mapping_par_opt_to_par_sim=mapping_par_opt_to_par_sim[
                condition_ix][1]
        )

        # append to mapping
        mapping_scale_opt_to_scale_sim.append((preeq_map, sim_map),)

    return mapping_scale_opt_to_scale_sim


def get_scale_mapping_for_condition(
        parameter_df: pd.DataFrame,
        mapping_par_opt_to_par_sim: List):
    """Get parameter scale mapping for the given condition.

    Arguments:
        parameter_df: PEtab parameter table
        mapping_par_opt_to_par_sim:
            Mapping as obtained from get_parameter_mapping_for_condition
    """
    n_par_sim = len(mapping_par_opt_to_par_sim)

    par_opt_ids_from_df = list(parameter_df.reset_index()['parameterId'])
    par_opt_scales_from_df = list(parameter_df.reset_index()['parameterScale'])

    mapping_scale_opt_to_scale_sim = []

    # iterate over simulation parameters
    for j_par_sim in range(n_par_sim):
        # extract entry in mapping table for j_par_sim
        val = mapping_par_opt_to_par_sim[j_par_sim]

        if isinstance(val, numbers.Number):
            # fixed value assignment
            scale = 'lin'
        else:
            # is par opt id, thus extract its scale
            try:
                scale = \
                    par_opt_scales_from_df[par_opt_ids_from_df.index(val)]
            except ValueError:
                # This is a condition-table parameter which is not
                # present in the parameter table. Those are assumed to be
                # 'lin'
                scale = 'lin'
        mapping_scale_opt_to_scale_sim.append(scale)

    return mapping_scale_opt_to_scale_sim


def perform_mapping_checks(measurement_df: pd.DataFrame) -> None:
    if lint.measurement_table_has_timepoint_specific_mappings(measurement_df):
        # we could allow that for floats, since they don't matter in this
        # function and would be simply ignored
        raise ValueError(
            "Timepoint-specific parameter overrides currently unsupported.")
