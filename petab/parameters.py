"""Functions operating on the PEtab parameter table"""

import numbers
import pandas as pd
import numpy as np
from collections import OrderedDict
from typing import Iterable, Set, List, Tuple

import libsbml

from . import lint, core, measurements, sbml


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
        parameter_df.set_index(['parameterId'], inplace=True)
    except KeyError:
        raise KeyError(
            'Parameter table missing mandatory field `parameterId`.')

    return parameter_df


def get_optimization_parameters(parameter_df: pd.DataFrame) -> List[str]:
    """
    Get list of optimization parameter ids from parameter dataframe.

    Arguments:
        parameter_df: PEtab parameter DataFrame

    Returns:
        List of parameter IDs in the parameter table
    """
    return list(parameter_df.reset_index()['parameterId'])


def create_parameter_df(sbml_model: libsbml.Model,
                        condition_df: pd.DataFrame,
                        measurement_df: pd.DataFrame,
                        parameter_scale: str = 'log10',
                        lower_bound: Iterable = None,
                        upper_bound: Iterable = None) -> pd.DataFrame:
    """Create a new PEtab parameter table

    All table entries can be provided as string or list-like with length
    matching the number of parameters

    Arguments:
        sbml_model: SBML Model
        condition_df: PEtab condition DataFrame
        measurement_df: PEtab measurement DataFrame
        parameter_scale: parameter scaling
        lower_bound: lower bound for parameter value
        upper_bound: upper bound for parameter value

    Returns:
        The created parameter DataFrame
    """
    parameter_ids = list(get_required_parameters_for_parameter_table(
        sbml_model, condition_df, measurement_df))

    df = pd.DataFrame(
        data={
            'parameterId': parameter_ids,
            'parameterName': parameter_ids,
            'parameterScale': parameter_scale,
            'lowerBound': lower_bound,
            'upperBound': upper_bound,
            'nominalValue': np.nan,
            'estimate': 1,
            'priorType': '',
            'priorParameters': ''
        })
    df.set_index(['parameterId'], inplace=True)

    # For SBML model parameters, set nominal values as defined in the model
    for parameter_id in df.index:
        try:
            parameter = sbml_model.getParameter(parameter_id)
            if parameter:
                df.loc[parameter_id, 'nominalValue'] = parameter.getValue()
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
        parameter table
    """

    observables = sbml.get_observables(sbml_model)
    sigmas = sbml.get_sigmas(sbml_model)

    # collect placeholder parameters
    placeholders = set()
    for k, v in observables.items():
        placeholders |= measurements.get_placeholders(
            v['formula'],
            core.get_observable_id(k),
            'observable')
    for k, v in sigmas.items():
        placeholders |= measurements.get_placeholders(
            v, core.get_observable_id(k), 'noise')

    # grab all from model and measurement table
    # without condition table parameters
    # and observables assigment targets
    # and sigma assignment targets
    # and placeholder parameters (only partial overrides are not supported)

    # exclude rule targets
    assignment_targets = {ar.getVariable()
                          for ar in sbml_model.getListOfRules()}

    # should not go into parameter table
    blackset = set()
    # collect assignment targets
    blackset |= set(observables.keys())
    blackset |= placeholders
    blackset |= assignment_targets
    blackset |= set(condition_df.columns.values) - {'conditionName'}
    # use ordered dict as proxy for ordered set
    parameter_ids = OrderedDict.fromkeys(
        p.getId() for p in sbml_model.getListOfParameters()
        if p.getId() not in blackset)

    # Append parameters from measurement table,
    # unless they are fixed parameters
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

    # Append parameter overrides from condition table
    condition_parameters = list(
        set(condition_df.columns.values.tolist()) - {'conditionId',
                                                     'conditionName'})
    for overridee in condition_parameters:
        # non-numeric entries are parameter overrides
        overrides = condition_df[overridee][
            ~condition_df[overridee].apply(isinstance, args=(numbers.Number,))]
        for overrider in overrides:
            parameter_ids[overrider] = None

    return parameter_ids.keys()


def get_priors_from_df(parameter_df: pd.DataFrame
                       ) -> List[Tuple]:
    """Create list with information about the parameter priors

    Arguments:
        parameter_df: PEtab parameter table

    Returns:
        List with prior information.
    """

    # get types and parameters of priors from dataframe
    par_to_estimate = parameter_df.loc[parameter_df['estimate'] == 1]

    prior_list = []
    for _, row in par_to_estimate.iterrows():
        # retrieve info about type
        prior_type = str(row['priorType'])

        # retrieve info about parameters of priors, make it a tuple of floats
        tmp_pars = str(row['priorParameters']).split(';')
        prior_pars = tuple([float(entry) for entry in tmp_pars])

        # add parameter scale and bounds, as this may be needed
        par_scale = row['parameterScale']
        par_bounds = (row['lowerBound'], row['upperBound'])

        # if no prior is specified, we assume a non-informative (uniform) one
        if prior_type == 'nan':
            prior_type = 'parameterScaleUniform'
            prior_pars = (row['lowerBound'], row['upperBound'])

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

    if scale_str == 'lin' or not scale_str:
        return parameter
    if scale_str == 'log':
        return np.log(parameter)
    if scale_str == 'log10':
        return np.log10(parameter)
    raise ValueError("Invalid parameter scaling: " + scale_str)


def map_scale(parameters: Iterable[numbers.Number],
              scale_strs: Iterable[str]) -> Iterable[numbers.Number]:
    """As scale(), but for Iterables"""
    return map(lambda x: scale(x[0], x[1]), zip(parameters, scale_strs))
