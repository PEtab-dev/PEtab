"""PEtab core functions (or functions that don't fit anywhere else)"""

import logging
import os
from typing import Iterable, Optional, Callable, Union, Any
from warnings import warn

import numpy as np
import pandas as pd

from . import yaml
from .C import *  # noqa: F403

logger = logging.getLogger(__name__)


def get_simulation_df(simulation_file: str) -> pd.DataFrame:
    """Read PEtab simulation table

    Arguments:
        simulation_file: URL or filename of PEtab simulation table

    Returns:
        Simulation DataFrame
    """
    return pd.read_csv(simulation_file, sep="\t", index_col=None)


def write_simulation_df(df: pd.DataFrame, filename: str) -> None:
    """Write PEtab simulation table

    Arguments:
        df: PEtab simulation table
        filename: Destination file name
    """
    with open(filename, 'w') as fh:
        df.to_csv(fh, sep='\t', index=False)


def get_visualization_df(visualization_file: str) -> pd.DataFrame:
    """Read PEtab visualization table

    Arguments:
        visualization_file: URL or filename of PEtab visualization table

    Returns:
        Visualization DataFrame
    """
    return pd.read_csv(visualization_file, sep="\t", index_col=None)


def write_visualization_df(df: pd.DataFrame, filename: str) -> None:
    """Write PEtab visualization table

    Arguments:
        df: PEtab visualization table
        filename: Destination file name
    """
    with open(filename, 'w') as fh:
        df.to_csv(fh, sep='\t', index=False)


def get_notnull_columns(df: pd.DataFrame, candidates: Iterable):
    """
    Return list of ``df``-columns in ``candidates`` which are not all null/nan.

    The output can e.g. be used as input for ``pandas.DataFrame.groupby``.

    Arguments:
        df:
            Dataframe
        candidates:
            Columns of ``df`` to consider
    """
    return [col for col in candidates
            if col in df and not np.all(df[col].isnull())]


def get_observable_id(parameter_id: str) -> str:
    """Get PEtab observable ID from PEtab-style sigma or observable
    `AssignmentRule`-target ``parameter_id``.

    e.g. for 'observable_obs1' -> 'obs1', for 'sigma_obs1' -> 'obs1'

    Arguments:
        parameter_id: Some parameter ID

    Returns:
        Observable ID
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    if parameter_id.startswith(r'observable_'):
        return parameter_id[len('observable_'):]

    if parameter_id.startswith(r'sigma_'):
        return parameter_id[len('sigma_'):]

    raise ValueError('Cannot extract observable id from: ' + parameter_id)


def flatten_timepoint_specific_output_overrides(
        petab_problem: 'petab.problem.Problem') -> None:
    """Flatten timepoint-specific output parameter overrides.

    If the PEtab problem definition has timepoint-specific
    `observableParameters` or `noiseParameters` for the same observable,
    replace those by replicating the respective observable.

    This is a helper function for some tools which may not support such
    timepoint-specific mappings. The observable table and measurement table
    are modified in place.

    Arguments:
        petab_problem:
            PEtab problem to work on
    """

    # Create empty df -> to be filled with replicate-specific observables
    df_new = pd.DataFrame()

    # Get observableId, preequilibrationConditionId
    # and simulationConditionId columns in measurement df
    df = petab_problem.measurement_df[
        [OBSERVABLE_ID,
         PREEQUILIBRATION_CONDITION_ID,
         SIMULATION_CONDITION_ID]
    ]
    # Get unique combinations of observableId, preequilibrationConditionId
    # and simulationConditionId
    df_unique_values = df.drop_duplicates()

    # replaced observables: new ID => old ID
    replacements = dict()
    # Loop over each unique combination
    for nrow in range(len(df_unique_values.index)):
        df = petab_problem.measurement_df.loc[
            (petab_problem.measurement_df[OBSERVABLE_ID] ==
             df_unique_values.loc[nrow, OBSERVABLE_ID])
            & (petab_problem.measurement_df[PREEQUILIBRATION_CONDITION_ID] <=
               df_unique_values.loc[nrow, PREEQUILIBRATION_CONDITION_ID])
            & (petab_problem.measurement_df[SIMULATION_CONDITION_ID] <=
               df_unique_values.loc[nrow, SIMULATION_CONDITION_ID])
        ]

        # Get list of unique observable parameters
        unique_sc = df[OBSERVABLE_PARAMETERS].unique()
        # Get list of unique noise parameters
        unique_noise = df[NOISE_PARAMETERS].unique()

        # Loop
        for i_noise, cur_noise in enumerate(unique_noise):
            for i_sc, cur_sc in enumerate(unique_sc):
                # Find the position of all instances of cur_noise
                # and unique_sc[j] in their corresponding column
                # (full-string matches are denoted by zero)
                idxs = (
                    df[NOISE_PARAMETERS].str.find(cur_noise) +
                    df[OBSERVABLE_PARAMETERS].str.find(cur_sc)
                )
                tmp_ = df.loc[idxs == 0, OBSERVABLE_ID]
                # Create replicate-specific observable name
                tmp = tmp_ + "_" + str(i_noise + i_sc + 1)
                # Check if replicate-specific observable name already exists
                # in df. If true, rename replicate-specific observable
                counter = 2
                while (df[OBSERVABLE_ID].str.find(
                        tmp.to_string()
                ) == 0).any():
                    tmp = tmp_ + counter*"_" + str(i_noise + i_sc + 1)
                    counter += 1
                if not tmp_.empty and not tmp_.empty:
                    replacements[tmp.values[0]] = tmp_.values[0]
                df.loc[idxs == 0, OBSERVABLE_ID] = tmp
                # Append the result in a new df
                df_new = df_new.append(df.loc[idxs == 0])
                # Restore the observable name in the original df
                # (for continuation of the loop)
                df.loc[idxs == 0, OBSERVABLE_ID] = tmp

    # Update/Redefine measurement df with replicate-specific observables
    petab_problem.measurement_df = df_new

    # Update observables table
    for replacement, replacee in replacements.items():
        new_obs = petab_problem.observable_df.loc[replacee].copy()
        new_obs.name = replacement
        new_obs[OBSERVABLE_FORMULA] = new_obs[OBSERVABLE_FORMULA].replace(
            replacee, replacement)
        new_obs[NOISE_FORMULA] = new_obs[NOISE_FORMULA].replace(
            replacee, replacement)
        petab_problem.observable_df = petab_problem.observable_df.append(
            new_obs
        )

    petab_problem.observable_df.drop(index=set(replacements.values()),
                                     inplace=True)


def concat_tables(
        tables: Union[str, pd.DataFrame, Iterable[Union[pd.DataFrame, str]]],
        file_parser: Optional[Callable] = None
) -> pd.DataFrame:
    """Concatenate DataFrames provided as DataFrames or filenames, and a parser

    Arguments:
        tables:
            Iterable of tables to join, as DataFrame or filename.
        file_parser:
            Function used to read the table in case filenames are provided,
            accepting a filename as only argument.

    Returns:
        The concatenated DataFrames
    """

    if isinstance(tables, pd.DataFrame):
        return tables

    if isinstance(tables, str):
        return file_parser(tables)

    df = pd.DataFrame()

    for tmp_df in tables:
        # load from file, if necessary
        if isinstance(tmp_df, str):
            tmp_df = file_parser(tmp_df)

        df = df.append(tmp_df, sort=False,
                       ignore_index=isinstance(tmp_df.index, pd.RangeIndex))

    return df


def to_float_if_float(x: Any) -> Any:
    """Return input as float if possible, otherwise return as is

    Arguments:
        x: Anything

    Returns:
        ``x`` as float if possible, otherwise ``x``
    """

    try:
        return float(x)
    except (ValueError, TypeError):
        return x


def is_empty(val) -> bool:
    """Check if the value `val`, e.g. a table entry, is empty.

    Arguments:
        val: The value to check.

    Returns:
        empty: Whether the field is to be considered empty.
    """
    return val == '' or pd.isnull(val)


def create_combine_archive(
        yaml_file: str, filename: str,
        family_name: Optional[str] = None,
        given_name: Optional[str] = None,
        email: Optional[str] = None,
        organization: Optional[str] = None,
) -> None:
    """Create COMBINE archive (http://co.mbine.org/documents/archive) based
    on PEtab YAML file.

    Arguments:
        yaml_file: Path to PEtab YAML file
        family_name: Family name of archive creator
        given_name: Given name of archive creator
        email: E-mail address of archive creator
        organization: Organization of archive creator
    """

    path_prefix = os.path.dirname(yaml_file)
    yaml_config = yaml.load_yaml(yaml_file)

    # function-level import, because module-level import interfered with
    # other SWIG interfaces
    import libcombine

    def _add_file_metadata(location: str, description: str = ""):
        """Add metadata to the added file"""
        omex_description = libcombine.OmexDescription()
        omex_description.setAbout(location)
        omex_description.setDescription(description)
        omex_description.setCreated(
            libcombine.OmexDescription.getCurrentDateAndTime())
        archive.addMetadata(location, omex_description)

    archive = libcombine.CombineArchive()

    # Add PEtab files and metadata
    archive.addFile(
        yaml_file,
        os.path.basename(yaml_file),
        libcombine.KnownFormats.lookupFormat("yaml"),
        True
    )
    _add_file_metadata(location=os.path.basename(yaml_file),
                       description="PEtab YAML file")
    archive.addFile(
        os.path.join(path_prefix, yaml_config[PARAMETER_FILE]),
        yaml_config[PARAMETER_FILE],
        libcombine.KnownFormats.lookupFormat("tsv"),
        False
    )
    _add_file_metadata(location=yaml_config[PARAMETER_FILE],
                       description="PEtab parameter file")
    for problem in yaml_config[PROBLEMS]:
        for sbml_file in problem[SBML_FILES]:
            archive.addFile(
                os.path.join(path_prefix, sbml_file),
                sbml_file,
                libcombine.KnownFormats.lookupFormat("sbml"),
                False
            )
            _add_file_metadata(location=sbml_file, description="SBML model")

        for field in [MEASUREMENT_FILES, OBSERVABLE_FILES,
                      VISUALIZATION_FILES, CONDITION_FILES]:
            if field not in problem:
                continue

            for file in problem[field]:
                archive.addFile(
                    os.path.join(path_prefix, file),
                    file,
                    libcombine.KnownFormats.lookupFormat("tsv"),
                    False
                )
                desc = field.split("_")[0]
                _add_file_metadata(location=file,
                                   description=f"PEtab {desc} file")

    # Add archive metadata
    description = libcombine.OmexDescription()
    description.setAbout(".")
    description.setDescription("PEtab archive")
    description.setCreated(libcombine.OmexDescription.getCurrentDateAndTime())

    # Add creator info
    creator = libcombine.VCard()
    if family_name:
        creator.setFamilyName(family_name)
    if given_name:
        creator.setGivenName(given_name)
    if email:
        creator.setEmail(email)
    if organization:
        creator.setOrganization(organization)
    description.addCreator(creator)

    archive.addMetadata(".", description)
    archive.writeToFile(filename)
