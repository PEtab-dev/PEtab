"""Functions operating on the PEtab parameter table"""

import numbers
import pandas as pd
import numpy as np
from collections import OrderedDict
from typing import Iterable, Set, List, Tuple

import libsbml

from . import lint, core, measurements, sbml, conditions
from .C import *  # noqa: F403


def get_parameter_df(parameter_file_name: str) -> pd.DataFrame:
    """
    Read the provided parameter file into a ``pandas.Dataframe``.

    Arguments:
        parameter_file_name: Name of the file to read from.

    Returns:
        Parameter DataFrame
    """

    parameter_df = pd.read_csv(parameter_file_name, sep='\t')
    lint.assert_no_leading_trailing_whitespace(
        parameter_df.columns.values, "parameter")

    try:
        parameter_df.set_index([PARAMETER_ID], inplace=True)
    except KeyError:
        raise KeyError(
            f"Parameter table missing mandatory field {PARAMETER_ID}.")

    return parameter_df


def write_parameter_df(df: pd.DataFrame, filename: str) -> None:
    """Write PEtab parameter table

    Arguments:
        df: PEtab parameter table
        filename: Destination file name
    """
    with open(filename, 'w') as fh:
        df.to_csv(fh, sep='\t', index=True)


def get_optimization_parameters(parameter_df: pd.DataFrame) -> List[str]:
    """
    Get list of optimization parameter ids from parameter dataframe.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Returns:
        List of parameter IDs in the parameter table
    """
    return list(parameter_df.reset_index()[PARAMETER_ID])


def create_parameter_df(sbml_model: libsbml.Model,
                        condition_df: pd.DataFrame,
                        measurement_df: pd.DataFrame,
                        include_optional: bool = False,
                        parameter_scale: str = LOG10,
                        lower_bound: Iterable = None,
                        upper_bound: Iterable = None) -> pd.DataFrame:
    """Create a new PEtab parameter table

    All table entries can be provided as string or list-like with length
    matching the number of parameters

    Arguments:
        sbml_model: SBML Model
        condition_df: PEtab condition DataFrame
        measurement_df: PEtab measurement DataFrame
        include_optional: By default this only returns parameters that are
            required to be present in the parameter table. If set to True,
            this returns all parameters that are allowed to be present in the
            parameter table (i.e. also including parameters specified in the
            SBML model).
        parameter_scale: parameter scaling
        lower_bound: lower bound for parameter value
        upper_bound: upper bound for parameter value

    Returns:
        The created parameter DataFrame
    """

    if include_optional:
        parameter_ids = list(get_valid_parameters_for_parameter_table(
            sbml_model=sbml_model, condition_df=condition_df,
            measurement_df=measurement_df))
    else:
        parameter_ids = list(get_required_parameters_for_parameter_table(
            sbml_model=sbml_model, condition_df=condition_df,
            measurement_df=measurement_df))

    df = pd.DataFrame(
        data={
            PARAMETER_ID: parameter_ids,
            PARAMETER_NAME: parameter_ids,
            PARAMETER_SCALE: parameter_scale,
            LOWER_BOUND: lower_bound,
            UPPER_BOUND: upper_bound,
            NOMINAL_VALUE: np.nan,
            ESTIMATE: 1,
            INITIALIZATION_PRIOR_TYPE: '',
            INITIALIZATION_PRIOR_PARAMETERS: '',
            OBJECTIVE_PRIOR_TYPE: '',
            OBJECTIVE_PRIOR_PARAMETERS: '',
        })
    df.set_index([PARAMETER_ID], inplace=True)

    # For SBML model parameters, set nominal values as defined in the model
    for parameter_id in df.index:
        try:
            parameter = sbml_model.getParameter(parameter_id)
            if parameter:
                df.loc[parameter_id, NOMINAL_VALUE] = parameter.getValue()
        except ValueError:
            # parameter was introduced as condition-specific override and
            # is potentially not present in the model
            pass
    return df


def get_required_parameters_for_parameter_table(
        sbml_model: libsbml.Model,
        condition_df: pd.DataFrame,
        measurement_df: pd.DataFrame) -> Set[str]:
    """
    Get set of parameters which need to go into the parameter table

    Arguments:
        sbml_model: PEtab SBML model
        condition_df: PEtab condition table
        measurement_df: PEtab measurement table

    Returns:
        Set of parameter IDs which PEtab requires to be present in the
        parameter table. That is all {observable,noise}Parameters from the
        measurement table as well as all parametric condition table overrides
        that are not defined in the SBML model.
    """

    # use ordered dict as proxy for ordered set
    parameter_ids = OrderedDict()

    # Add parameters from measurement table, unless they are fixed parameters
    def append_overrides(overrides):
        for p in overrides:
            if isinstance(p, str) and p not in condition_df.columns:
                parameter_ids[p] = None

    for _, row in measurement_df.iterrows():
        # we trust that the number of overrides matches
        append_overrides(measurements.split_parameter_replacement_list(
            row.observableParameters))
        append_overrides(measurements.split_parameter_replacement_list(
            row.noiseParameters))

    # Add condition table parametric overrides unless already defined in the
    # SBML model
    for p in conditions.get_parametric_overrides(condition_df):
        if sbml_model.getParameter(p) is None:
            parameter_ids[p] = None

    return parameter_ids.keys()


def get_valid_parameters_for_parameter_table(
        sbml_model: libsbml.Model,
        condition_df: pd.DataFrame,
        measurement_df: pd.DataFrame) -> Set[str]:
    """
    Get set of parameters which may be present inside the parameter table

    Arguments:
        sbml_model: PEtab SBML model
        condition_df: PEtab condition table
        measurement_df: PEtab measurement table

    Returns:
        Set of parameter IDs which PEtab allows to be present in the
        parameter table.
    """

    # - grab all model parameters
    # - grab all parameters from measurement table
    # - grab all parametric overrides from condition table
    # - remove parameters for which condition table columns exist
    # - remove observables assigment targets
    # - remove sigma assignment targets
    # - remove placeholder parameters
    #   (only partial overrides are not supported)

    observables = sbml.get_observables(sbml_model)
    sigmas = sbml.get_sigmas(sbml_model)

    # collect placeholder parameters overwritten by
    # {observable,noise}Parameters
    placeholders = set()
    for k, v in observables.items():
        placeholders |= measurements.get_placeholders(
            v['formula'],
            core.get_observable_id(k),
            'observable')
    for k, v in sigmas.items():
        placeholders |= measurements.get_placeholders(
            v, core.get_observable_id(k), 'noise')

    # exclude rule targets
    assignment_targets = {ar.getVariable()
                          for ar in sbml_model.getListOfRules()}

    # must not go into parameter table
    blackset = set()
    # collect assignment targets
    blackset |= set(observables.keys())
    blackset |= placeholders
    blackset |= assignment_targets
    blackset |= set(condition_df.columns.values) - {CONDITION_NAME}

    # use ordered dict as proxy for ordered set
    parameter_ids = OrderedDict.fromkeys(
        p.getId() for p in sbml_model.getListOfParameters()
        if p.getId() not in blackset)

    # Append parameters from measurement table, unless they occur as condition
    # table columns
    def append_overrides(overrides):
        for p in overrides:
            if isinstance(p, str) and p not in blackset:
                parameter_ids[p] = None

    for _, row in measurement_df.iterrows():
        # we trust that the number of overrides matches
        append_overrides(measurements.split_parameter_replacement_list(
            row.observableParameters))
        append_overrides(measurements.split_parameter_replacement_list(
            row.noiseParameters))

    # Append parameter overrides from condition table
    for p in conditions.get_parametric_overrides(condition_df):
        parameter_ids[p] = None

    return parameter_ids.keys()


def get_priors_from_df(parameter_df: pd.DataFrame,
                       mode: str) -> List[Tuple]:
    """Create list with information about the parameter priors

    Arguments:
        parameter_df: PEtab parameter table
        mode: 'initialization' or 'objective'

    Returns:
        List with prior information.
    """

    # get types and parameters of priors from dataframe
    par_to_estimate = parameter_df.loc[parameter_df[ESTIMATE] == 1]

    prior_list = []
    for _, row in par_to_estimate.iterrows():
        # retrieve info about type
        prior_type = str(row.get(f'{mode}PriorType', PARAMETER_SCALE_UNIFORM))

        # retrieve info about parameters of priors, make it a tuple of floats
        pars_str = str(row.get(f'{mode}PriorParameters',
                               f'{row[LOWER_BOUND]};{row[UPPER_BOUND]}'))
        prior_pars = tuple([float(entry) for entry in pars_str.split(';')])

        # add parameter scale and bounds, as this may be needed
        par_scale = row[PARAMETER_SCALE]
        par_bounds = (row[LOWER_BOUND], row[UPPER_BOUND])

        # if no prior is specified, we assume a non-informative (uniform) one
        if prior_type == 'nan':
            prior_type = PARAMETER_SCALE_UNIFORM
            prior_pars = (row[LOWER_BOUND], row[UPPER_BOUND])

        prior_list.append((prior_type, prior_pars, par_scale, par_bounds))

    return prior_list


def parameter_id_is_valid(parameter_id: str) -> bool:
    """Check whether parameter_id is a valid PEtab parameter ID

    This should pretty much correspond to what is allowed for SBML identifiers.

    TODO(#179) improve checking

    Arguments:
        parameter_id: Parameter ID to validate

    Returns:
        ``True`` if valid, ``False`` otherwise
    """

    return parameter_id != ''


def scale(parameter: numbers.Number, scale_str: 'str') -> numbers.Number:
    """Scale parameter according to scale_str

    Arguments:
        parameter:
            Parameter to be scaled
        scale_str:
            One of 'lin' (synonymous with ''), 'log', 'log10'
    """

    if scale_str == LIN or not scale_str:
        return parameter
    if scale_str == LOG:
        return np.log(parameter)
    if scale_str == LOG10:
        return np.log10(parameter)
    raise ValueError("Invalid parameter scaling: " + scale_str)


def map_scale(parameters: Iterable[numbers.Number],
              scale_strs: Iterable[str]) -> Iterable[numbers.Number]:
    """As scale(), but for Iterables"""
    return map(lambda x: scale(x[0], x[1]), zip(parameters, scale_strs))
