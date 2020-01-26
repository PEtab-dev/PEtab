"""Functions for migrating PEtab files from different versions"""

import logging
import pandas as pd

from . import Problem
from . import get_notnull_columns
from .C import *
from .lint import lint_problem
from .measurements import get_placeholders
from .core import get_observable_id
from .sbml import get_sigmas, get_observables


def sbml_observables_to_table(problem: Problem):
    """Transform PEtab files where observables are defined inside the SBML
    model to the newer format where they are specified in a separate table.

    For details see https://github.com/ICB-DCM/PEtab/issues/241.

    Modifies ``problem`` in place. Does not alter any files.

    Assumes the input is adheres to the PEtab format. You may want to check
    that with ``petablint`` from PEtab 0.0.2.
    """

    logging.basicConfig(level=logging.DEBUG)

    # Ensure all measurements for the same observable have the same
    # observableTransformation and noiseModel

    measurement_df = problem.measurement_df
    grouping_cols = get_notnull_columns(
        measurement_df, [OBSERVABLE_ID, OBSERVABLE_TRANSFORMATION,
                         NOISE_DISTRIBUTION])
    grouped = measurement_df.groupby(grouping_cols).count().reset_index()

    if len(grouped[OBSERVABLE_ID]) != len(grouped[OBSERVABLE_ID]):
        raise ValueError("In order to create an observable table, all "
                         "measurements for the same observable must have the "
                         "same observableTransformation and noiseModel."
                         "Multiple observableTransformation and noiseModel "
                         "has to be handled by different observables.")

    # get observables and sigmas from SBML file and directly remove them
    observables = get_observables(problem.sbml_model, remove=True)
    sigmas = get_sigmas(problem.sbml_model, remove=True)
    assert observables.keys() == sigmas.keys()

    if not observables:
        raise RuntimeError("No observables in SBML model to convert. "
                           "Has this model already been processed?")

    # Create observable dataframe and add to `problem`

    for obs_id, noise in sigmas.items():
        observables[obs_id][NOISE_FORMULA] = noise

    # set observableTransformation and noiseModel
    for obs_id_long in observables:
        obs_id = get_observable_id(obs_id_long)
        cur_mes_df = measurement_df[measurement_df[OBSERVABLE_ID] == obs_id]
        if cur_mes_df.empty:
            # observable defined, but no measurements
            continue

        if OBSERVABLE_TRANSFORMATION in cur_mes_df:
            observables[obs_id_long][OBSERVABLE_TRANSFORMATION] = \
                cur_mes_df[OBSERVABLE_TRANSFORMATION].values[0]
        else:
            observables[obs_id_long][OBSERVABLE_TRANSFORMATION] = LIN

        if NOISE_DISTRIBUTION in cur_mes_df:
            observables[obs_id_long][NOISE_DISTRIBUTION] = \
                cur_mes_df[NOISE_DISTRIBUTION].values[0]
        else:
            observables[obs_id_long][NOISE_DISTRIBUTION] = NORMAL

    observable_df = pd.DataFrame(observables).transpose().reset_index()
    observable_df.rename(columns={"index": OBSERVABLE_ID,
                                  "name": OBSERVABLE_NAME,
                                  "formula": OBSERVABLE_FORMULA},
                         errors="raise", inplace=True)
    observable_df[OBSERVABLE_ID] = observable_df[OBSERVABLE_ID].apply(
        get_observable_id)
    observable_df.set_index([OBSERVABLE_ID], inplace=True)
    observable_df = observable_df.sort_index()
    problem.observable_df = observable_df

    # remove observableParameters and noiseParameters from SBML file
    # noise and observable parameters and AssignmentRules have already been
    # removed
    sbml_model = problem.sbml_model
    placeholders = set()
    for k, v in observables.items():
        placeholders |= get_placeholders(
            v['formula'],
            get_observable_id(k),
            'observable')
    for k, v in sigmas.items():
        placeholders |= get_placeholders(
            v, get_observable_id(k), 'noise')
    for placeholder in placeholders:
        ret = sbml_model.removeParameter(placeholder)
        if not ret:
            raise RuntimeError("Unknown problem when trying to remove "
                               f"placeholder parameter {placeholder}.")

    # drop obsolete measurement columns
    if OBSERVABLE_TRANSFORMATION in measurement_df:
        measurement_df.drop(OBSERVABLE_TRANSFORMATION, axis=1, inplace=True)
    if NOISE_DISTRIBUTION in measurement_df:
        measurement_df.drop(NOISE_DISTRIBUTION, axis=1, inplace=True)

    if lint_problem(problem):
        raise RuntimeError("Unknown error converting PEtab problem to "
                           "observable table based format.")
