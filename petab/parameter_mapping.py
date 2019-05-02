"""Functions related to mapping parameter from model to parameter estimation
problem"""

import pandas as pd
import numpy as np
import libsbml
import numbers
import re
from . import lint
from . import core
from typing import List, Tuple, Dict, Union, Any
import logging

logger = logging.getLogger(__name__)

# Parameter mapping for condition
ParMappingDict = Dict[str, Union[str, numbers.Number]]
# Parameter mapping for combination of preequilibration and simulation
# condition
ParMappingDictTuple = Tuple[ParMappingDict, ParMappingDict]
# Same for scale mapping
ScaleMappingDict = Dict[str, str]
ScaleMappingDictTuple = Tuple[ScaleMappingDict, ScaleMappingDict]


def get_optimization_to_simulation_parameter_mapping(
        condition_df: pd.DataFrame,
        measurement_df: pd.DataFrame,
        parameter_df: pd.DataFrame = None,
        sbml_model: libsbml.Model = None,
        simulation_conditions=None,
        warn_unmapped: bool = True) -> List[ParMappingDictTuple]:
    """
    Create list of mapping dicts from PEtab-problem to SBML parameters.

    Parameters
    ----------
    condition_df, measurement_df, parameter_df:
        The dataframes in the PEtab format.

        parameter_df is optional if par_sim_ids is provided

    sbml_model:
        The sbml model with observables and noise specified according to the
        petab format. Optional if par_sim_ids is provided.

    simulation_conditions: pd.DataFrame
        Table of simulation conditions as created by
        `petab.get_simulation_conditions`.

    warn_unmapped:
        If True, log warning regarding unmapped parameters

    Returns
    -------
    The length of the returned array is n_conditions, each entry is a tuple of
    two dicts of length n_par_sim, listing the optimization parameters or
    constants to be mapped to the simulation parameters, first for
    preequilibration (empty if no preequilibration condition is specified),
    second for simulation. NaN is used where no mapping exists.
    """
    # Ensure inputs are okay
    perform_mapping_checks(measurement_df)

    if simulation_conditions is None:
        simulation_conditions = core.get_simulation_conditions(measurement_df)

    mapping = []
    for condition_ix, condition in simulation_conditions.iterrows():
        cur_measurement_df = core.get_rows_for_condition(
            measurement_df, condition)

        if 'preequilibrationConditionId' not in condition \
                or not isinstance(condition.preequilibrationConditionId, str) \
                or not condition.preequilibrationConditionId:
            preeq_map = {}
        else:
            preeq_map = get_parameter_mapping_for_condition(
                condition_id=condition.preequilibrationConditionId,
                is_preeq=True,
                cur_measurement_df=cur_measurement_df,
                condition_df=condition_df,
                parameter_df=parameter_df, sbml_model=sbml_model,
                warn_unmapped=warn_unmapped
            )

        sim_map = get_parameter_mapping_for_condition(
            condition_id=condition.simulationConditionId,
            is_preeq=False,
            cur_measurement_df=cur_measurement_df,
            condition_df=condition_df,
            parameter_df=parameter_df, sbml_model=sbml_model,
            warn_unmapped=warn_unmapped
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
        warn_unmapped: bool = True) -> ParMappingDict:
    """
    Create dictionary of mappings from PEtab-problem to SBML parameters for the
    given condition.

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

    warn_unmapped:
        If True, log warning regarding unmapped parameters

    Returns
    -------
    Dictionary of parameter IDs with mapped parameters IDs to be estimated or
    filled in values in case of non-estimated parameters. NaN is used where no
    mapping exists.
    """
    perform_mapping_checks(cur_measurement_df)

    par_sim_ids = core.get_model_parameters(sbml_model)

    # initialize mapping dict
    # for the case of matching simulation and optimization parameter vector
    mapping = {par: par for par in par_sim_ids}

    _apply_dynamic_parameter_overrides(mapping, condition_id, condition_df)

    if not is_preeq:
        _apply_output_parameter_overrides(mapping, cur_measurement_df)

    fill_in_nominal_values(mapping, parameter_df)

    # TODO fill in fixed parameters (#103)

    handle_missing_overrides(mapping, warn=warn_unmapped)
    return mapping


def _apply_output_parameter_overrides(
        mapping: ParMappingDict,
        cur_measurement_df: pd.DataFrame) -> None:
    """
    Apply output parameter overrides to the parameter mapping dict for a given
    condition as defined in the measurement table (observableParameter,
    noiseParameters).

    Arguments:
        mapping: parameter mapping dict
        cur_measurement_df:
            Subset of the measurement table for the current condition
    """
    for _, row in cur_measurement_df.iterrows():
        # we trust that the number of overrides matches (see above)
        overrides = core.split_parameter_replacement_list(
            row.observableParameters)
        _apply_overrides_for_observable(mapping, row.observableId,
                                        'observable', overrides)

        overrides = core.split_parameter_replacement_list(row.noiseParameters)
        _apply_overrides_for_observable(mapping, row.observableId, 'noise',
                                        overrides)


def _apply_overrides_for_observable(
        mapping: ParMappingDict,
        observable_id: str,
        override_type: str,
        overrides: list) -> None:
    """
    Apply parameter-overrides for observables and noises to mapping
    matrix.

    Arguments:
        mapping: mapping dict to which to apply overrides
        observable_id: observable ID
        override_type: 'observable' or 'noise'
        overrides: list of overrides for noise or observable parameters
    """
    for i, override in enumerate(overrides):
        overridee_id = f'{override_type}Parameter{i+1}_{observable_id}'
        mapping[overridee_id] = override


def _apply_dynamic_parameter_overrides(mapping: ParMappingDict,
                                       condition_id: str,
                                       condition_df: pd.DataFrame) -> None:
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
        mapping[overridee_id] = overrider_id


def fill_in_nominal_values(mapping: ParMappingDict,
                           parameter_df: pd.DataFrame) -> None:
    """Replace non-estimated parameters in mapping list for a given condition
    by nominalValues provided in parameter table.

    Arguments:
        mapping:
            mapping dict obtained from get_parameter_mapping_for_condition
        parameter_df:
            PEtab parameter table
    """

    if parameter_df is None:
        return
    if 'estimate' not in parameter_df:
        return

    overrides = {row.name: row.nominalValue for _, row
                 in parameter_df.iterrows() if row.estimate != 1}

    for par, overridee in mapping.items():
        if not isinstance(overridee, str):
            continue

        try:
            mapping[par] = overrides[overridee]
            # all overrides will be scaled to 'lin'
            if 'parameterScale' in parameter_df:
                scale = parameter_df.loc[overridee, 'parameterScale']
                if scale == 'log':
                    mapping[par] = np.exp(mapping[par])
                elif scale == 'log10':
                    mapping[par] = np.power(10, mapping[par])
        except KeyError:
            # parameter is to be estimated
            pass


def get_optimization_to_simulation_scale_mapping(
        parameter_df: pd.DataFrame,
        mapping_par_opt_to_par_sim: List[ParMappingDictTuple],
        measurement_df: pd.DataFrame,
        simulation_conditions: Union[dict, pd.DataFrame] = None
) -> List[ScaleMappingDictTuple]:
    """Get parameter scale mapping for all conditions"""
    mapping_scale_opt_to_scale_sim = []

    if simulation_conditions is None:
        simulation_conditions = core.get_simulation_conditions(measurement_df)

    # iterate over conditions
    for condition_ix, condition in simulation_conditions.iterrows():
        if 'preequilibrationConditionId' not in condition \
                or not isinstance(condition.preequilibrationConditionId, str) \
                or not condition.preequilibrationConditionId:
            preeq_map = {}
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
        mapping_par_opt_to_par_sim: ParMappingDict) -> ScaleMappingDict:
    """Get parameter scale mapping for the given condition.

    Arguments:
        parameter_df: PEtab parameter table
        mapping_par_opt_to_par_sim:
            Mapping as obtained from get_parameter_mapping_for_condition
    """
    def get_scale(par_id_or_val):
        if isinstance(par_id_or_val, numbers.Number):
            # fixed value assignment
            return 'lin'
        else:
            # is par opt id, thus extract its scale
            try:
                return parameter_df.loc[par_id_or_val, 'parameterScale']
            except KeyError:
                # This is a condition-table parameter which is not
                # present in the parameter table. Those are assumed to be
                # 'lin'
                return 'lin'

    return {par: get_scale(val)
            for par, val in mapping_par_opt_to_par_sim.items()}


def perform_mapping_checks(measurement_df: pd.DataFrame) -> None:
    if lint.measurement_table_has_timepoint_specific_mappings(measurement_df):
        # we could allow that for floats, since they don't matter in this
        # function and would be simply ignored
        raise ValueError(
            "Timepoint-specific parameter overrides currently unsupported.")


def handle_missing_overrides(mapping_par_opt_to_par_sim: ParMappingDict,
                             warn: bool = True,
                             condition_id: str = None) -> None:
    """
    Find all observable parameters and noise parameters that were not mapped
    and set their mapping to np.nan.

    Assumes that parameters matching "(noise|observable)Parameter[0-9]+_" were
    all supposed to be overwritten.

    Parameters:
    -----------
    mapping_par_opt_to_par_sim:
        Output of get_parameter_mapping_for_condition
    warn:
        If True, log warning regarding unmapped parameters
    """
    _missed_vals = []
    rex = re.compile("^(noise|observable)Parameter[0-9]+_")
    for key, val in mapping_par_opt_to_par_sim.items():
        try:
            matches = rex.match(val)
        except TypeError:
            continue

        if matches:
            mapping_par_opt_to_par_sim[key] = np.nan
            _missed_vals.append(key)

    if len(_missed_vals) and warn:
        logger.warning(f"Could not map the following overrides for condition "
                       f"{condition_id}: "
                       f"{_missed_vals}. Usually, this is just due to missing "
                       f"data points.")


def merge_preeq_and_sim_pars_condition(
        condition_map_preeq: ParMappingDict,
        condition_map_sim: ParMappingDict,
        condition_scale_map_preeq: ScaleMappingDict,
        condition_scale_map_sim: ScaleMappingDict,
        condition: Any) -> None:
    """Merge preequilibration and simulation parameters and scales while
    checking for compatibility.

    This function is meant for the case where we cannot have different
    parameters (and scales) for preequilibration and simulation. Therefore,
    merge both and ensure matching scales and parameters.
    `condition_map_sim` and `condition_scale_map_sim` will ne modified in
    place.

    Arguments:
        condition_map_preeq, condition_map_sim:
            Parameter mapping as obtained from
            `get_parameter_mapping_for_condition`
        condition_scale_map_preeq, condition_scale_map_sim:
            Parameter scale mapping as obtained from
            `get_get_scale_mapping_for_condition`
        condition: Condition identifier for more informative error messages
    """
    if not condition_map_preeq:
        # nothing to do
        return

    for idx, (par_preeq, par_sim, scale_preeq, scale_sim) \
            in enumerate(zip(condition_map_preeq,
                             condition_map_sim,
                             condition_scale_map_preeq,
                             condition_scale_map_sim)):
        if par_preeq != par_sim \
                and not (np.isnan(par_sim) and np.isnan(par_preeq)):
            # both identical or both nan is okay
            if np.isnan(par_sim):
                # unmapped for simulation
                par_sim[idx] = par_preeq
            elif np.isnan(par_preeq):
                # unmapped for preeq is okay
                pass
            else:
                raise ('Cannot handle different values for dynamic '
                       f'parameters: for condition {condition} '
                       f'parameter {idx} is {par_preeq} for preeq '
                       f'and {par_sim} for simulation.')
        if scale_preeq != scale_sim:
            # both identical is okay
            if np.isnan(par_sim):
                # unmapped for simulation
                scale_sim[idx] = scale_preeq
            elif np.isnan(par_preeq):
                # unmapped for preeq is okay
                pass
            else:
                raise ('Cannot handle different parameter scales '
                       f'parameters: for condition {condition} '
                       f'scale for parameter {idx} is '
                       f'{scale_preeq} for preeq '
                       f'and {scale_sim} for simulation.')
