"""PEtab Problem class"""

import os
from warnings import warn

import pandas as pd
import libsbml
from typing import Optional, List, Union, Dict, Iterable
from . import (parameter_mapping, measurements, conditions, parameters,
               sampling, sbml, yaml, core, observables)
from .C import *  # noqa: F403


class Problem:
    """
    PEtab parameter estimation problem as defined by

    - SBML model
    - condition table
    - measurement table
    - parameter table
    - observables table

    Optionally it may contain visualization tables.

    Attributes:
        condition_df: PEtab condition table
        measurement_df: PEtab measurement table
        parameter_df: PEtab parameter table
        observable_df: PEtab observable table
        visualization_df: PEtab visualization table
        sbml_reader: Stored to keep object alive.
        sbml_document: Stored to keep object alive.
        sbml_model: PEtab SBML model
    """

    def __init__(self,
                 sbml_model: libsbml.Model = None,
                 sbml_reader: libsbml.SBMLReader = None,
                 sbml_document: libsbml.SBMLDocument = None,
                 condition_df: pd.DataFrame = None,
                 measurement_df: pd.DataFrame = None,
                 parameter_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 observable_df: pd.DataFrame = None):

        self.condition_df: Optional[pd.DataFrame] = condition_df
        self.measurement_df: Optional[pd.DataFrame] = measurement_df
        self.parameter_df: Optional[pd.DataFrame] = parameter_df
        self.visualization_df: Optional[pd.DataFrame] = visualization_df
        self.observable_df: Optional[pd.DataFrame] = observable_df

        self.sbml_reader: Optional[libsbml.SBMLReader] = sbml_reader
        self.sbml_document: Optional[libsbml.SBMLDocument] = sbml_document
        self.sbml_model: Optional[libsbml.Model] = sbml_model

    def __getstate__(self):
        """Return state for pickling"""
        state = self.__dict__.copy()

        # libsbml stuff cannot be serialized directly
        if self.sbml_model:
            sbml_document = self.sbml_model.getSBMLDocument()
            sbml_writer = libsbml.SBMLWriter()
            state['sbml_string'] = sbml_writer.writeSBMLToString(sbml_document)

        exclude = ['sbml_reader', 'sbml_document', 'sbml_model']
        for key in exclude:
            state.pop(key)

        return state

    def __setstate__(self, state):
        """Set state after unpickling"""
        # load SBML model from pickled string
        sbml_string = state.pop('sbml_string', None)
        if sbml_string:
            self.sbml_reader = libsbml.SBMLReader()
            self.sbml_document = \
                self.sbml_reader.readSBMLFromString(sbml_string)
            self.sbml_model = self.sbml_document.getModel()

        self.__dict__.update(state)

    @staticmethod
    def from_files(sbml_file: str = None,
                   condition_file: str = None,
                   measurement_file: Union[str, Iterable[str]] = None,
                   parameter_file: str = None,
                   visualization_files: Union[str, Iterable[str]] = None,
                   observable_files: Union[str, Iterable[str]] = None
                   ) -> 'Problem':
        """
        Factory method to load model and tables from files.

        Arguments:
            sbml_file: PEtab SBML model
            condition_file: PEtab condition table
            measurement_file: PEtab measurement table
            parameter_file: PEtab parameter table
            visualization_files: PEtab visualization tables
            observable_files: PEtab observables tables
        """

        sbml_model = sbml_document = sbml_reader = None
        condition_df = measurement_df = parameter_df = visualization_df = None
        observable_df = None

        if condition_file:
            condition_df = conditions.get_condition_df(condition_file)

        if measurement_file:
            # If there are multiple tables, we will merge them
            measurement_df = core.concat_tables(
                measurement_file, measurements.get_measurement_df)

        if parameter_file:
            parameter_df = parameters.get_parameter_df(parameter_file)

        if sbml_file:
            sbml_reader = libsbml.SBMLReader()
            sbml_document = sbml_reader.readSBML(sbml_file)
            sbml_model = sbml_document.getModel()

        if visualization_files:
            # If there are multiple tables, we will merge them
            visualization_df = core.concat_tables(
                visualization_files, core.get_visualization_df)

        if observable_files:
            # If there are multiple tables, we will merge them
            observable_df = core.concat_tables(
                observable_files, observables.get_observable_df)

        return Problem(condition_df=condition_df,
                       measurement_df=measurement_df,
                       parameter_df=parameter_df,
                       observable_df=observable_df,
                       sbml_model=sbml_model,
                       sbml_document=sbml_document,
                       sbml_reader=sbml_reader,
                       visualization_df=visualization_df)

    @staticmethod
    def from_yaml(yaml_config: Union[Dict, str]) -> 'Problem':
        """
        Factory method to load model and tables as specified by YAML file.

        Arguments:
            yaml_config: PEtab configuration as dictionary or YAML file name
        """
        if isinstance(yaml_config, str):
            path_prefix = os.path.dirname(yaml_config)
            yaml_config = yaml.load_yaml(yaml_config)
        else:
            path_prefix = ""

        if yaml.is_composite_problem(yaml_config):
            raise ValueError('petab.Problem.from_yaml() can only be used for '
                             'yaml files comprising a single model. '
                             'Consider using '
                             'petab.CompositeProblem.from_yaml() instead.')

        problem0 = yaml_config['problems'][0]

        yaml.assert_single_condition_and_sbml_file(problem0)

        return Problem.from_files(
            sbml_file=os.path.join(path_prefix, problem0[SBML_FILES][0]),
            measurement_file=[os.path.join(path_prefix, f)
                              for f in problem0[MEASUREMENT_FILES]],
            condition_file=os.path.join(
                path_prefix, problem0[CONDITION_FILES][0]),
            parameter_file=os.path.join(
                path_prefix, yaml_config[PARAMETER_FILE]),
            visualization_files=[
                os.path.join(path_prefix, f)
                for f in problem0.get(VISUALIZATION_FILES, [])],
            observable_files=[
                os.path.join(path_prefix, f)
                for f in problem0.get(OBSERVABLE_FILES, [])]
        )

    @staticmethod
    def from_folder(folder: str, model_name: str = None) -> 'Problem':
        """
        Factory method to use the standard folder structure
        and file names, i.e.

        ::

            ${model_name}/
              +-- experimentalCondition_${model_name}.tsv
              +-- measurementData_${model_name}.tsv
              +-- model_${model_name}.xml
              +-- parameters_${model_name}.tsv

        Arguments:
            folder:
                Path to the directory in which the files are located.
            model_name:
                If specified, overrides the model component in the file names.
                Defaults to the last component of ``folder``.
        """

        folder = os.path.abspath(folder)
        if model_name is None:
            model_name = os.path.split(folder)[-1]

        return Problem.from_files(
            condition_file=get_default_condition_file_name(model_name, folder),
            measurement_file=get_default_measurement_file_name(model_name,
                                                               folder),
            parameter_file=get_default_parameter_file_name(model_name, folder),
            sbml_file=get_default_sbml_file_name(model_name, folder),
        )

    def to_files(self,
                 sbml_file: Optional[str] = None,
                 condition_file: Optional[str] = None,
                 measurement_file: Optional[str] = None,
                 parameter_file: Optional[str] = None,
                 visualization_file: Optional[str] = None,
                 observable_file: Optional[str] = None) -> None:
        """
        Write PEtab tables to files for this problem

        Writes PEtab files for those entities for which a destination was
        passed.

        NOTE: If this instance was created from multiple measurement or
        visualization tables, they will be merged and written to a single file.

        Arguments:
            sbml_file: SBML model destination
            condition_file: Condition table destination
            measurement_file: Measurement table destination
            parameter_file: Parameter table destination
            visualization_file: Visualization table destination
            observable_file: Observables table destination

        Raises:
            ValueError: If a destination was provided for a non-existing
            entity.
        """

        if sbml_file:
            if self.sbml_document is not None:
                sbml.write_sbml(self.sbml_document, sbml_file)
            else:
                raise ValueError("Unable to save SBML model with no "
                                 "sbml_doc set.")

        def error(name: str) -> ValueError:
            return ValueError(f"Unable to save non-existent {name} table")

        if condition_file:
            if self.condition_df is not None:
                conditions.write_condition_df(self.condition_df,
                                              condition_file)
            else:
                raise error("condition")

        if measurement_file:
            if self.measurement_df is not None:
                measurements.write_measurement_df(self.measurement_df,
                                                  measurement_file)
            else:
                raise error("measurement")

        if parameter_file:
            if self.parameter_df is not None:
                parameters.write_parameter_df(self.parameter_df,
                                              parameter_file)
            else:
                raise error("parameter")

        if observable_file:
            if self.observable_df is not None:
                observables.write_observable_df(self.observable_df,
                                                observable_file)
            else:
                raise error("observable")

        if visualization_file:
            if self.visualization_df is not None:
                core.write_visualization_df(self.visualization_df,
                                            visualization_file)
            else:
                raise error("visualization")

    def get_optimization_parameters(self):
        """
        Return list of optimization parameter IDs.

        See get_optimization_parameters.
        """
        return parameters.get_optimization_parameters(self.parameter_df)

    def get_dynamic_simulation_parameters(self):
        """See `get_model_parameters`"""
        return sbml.get_model_parameters(self.sbml_model)

    def get_observables(self, remove: bool = False):
        """
        Returns dictionary of observables definitions
        See `assignment_rules_to_dict` for details.
        """
        warn("This function will be removed in future releases.",
             DeprecationWarning)

        return sbml.get_observables(sbml_model=self.sbml_model, remove=remove)

    def get_sigmas(self, remove: bool = False):
        """
        Return dictionary of observableId => sigma as defined in the SBML
        model.
        This does not include parameter mappings defined in the measurement
        table.
        """
        warn("This function will be removed in future releases.",
             DeprecationWarning)

        return sbml.get_sigmas(sbml_model=self.sbml_model, remove=remove)

    def get_noise_distributions(self):
        """
        See `get_noise_distributions`.
        """
        return measurements.get_noise_distributions(
            measurement_df=self.measurement_df)

    @property
    def x_ids(self) -> List[str]:
        """Parameter table parameter IDs"""
        return list(self.parameter_df.reset_index()[PARAMETER_ID])

    @property
    def x_nominal(self) -> List:
        """Parameter table nominal values"""
        return list(self.parameter_df[NOMINAL_VALUE])

    @property
    def lb(self) -> List:
        """Parameter table lower bounds"""
        return list(self.parameter_df[LOWER_BOUND])

    @property
    def ub(self) -> List:
        """Parameter table upper bounds"""
        return list(self.parameter_df[UPPER_BOUND])

    @property
    def x_nominal_scaled(self) -> List:
        """Parameter table nominal values with applied parameter scaling"""
        return list(parameters.map_scale(self.parameter_df[NOMINAL_VALUE],
                                         self.parameter_df[PARAMETER_SCALE]))

    @property
    def lb_scaled(self) -> List:
        """Parameter table lower bounds with applied parameter scaling"""
        return list(parameters.map_scale(self.parameter_df[LOWER_BOUND],
                                         self.parameter_df[PARAMETER_SCALE]))

    @property
    def ub_scaled(self) -> List:
        """Parameter table upper bounds with applied parameter scaling"""
        return list(parameters.map_scale(self.parameter_df[UPPER_BOUND],
                                         self.parameter_df[PARAMETER_SCALE]))

    @property
    def x_fixed_indices(self) -> List[int]:
        """Parameter table non-estimated parameter indices"""
        estimated = list(self.parameter_df[ESTIMATE])
        return [j for j, val in enumerate(estimated) if val == 0]

    @property
    def x_fixed_vals(self) -> List:
        """Nominal values for parameter table non-estimated parameters"""
        return [self.x_nominal[val] for val in self.x_fixed_indices]

    def get_simulation_conditions_from_measurement_df(self):
        """See petab.get_simulation_conditions"""
        return measurements.get_simulation_conditions(self.measurement_df)

    def get_optimization_to_simulation_parameter_mapping(
            self, warn_unmapped: bool = True):
        """
        See get_simulation_to_optimization_parameter_mapping.
        """
        return parameter_mapping\
            .get_optimization_to_simulation_parameter_mapping(
                self.condition_df,
                self.measurement_df,
                self.parameter_df,
                self.sbml_model,
                warn_unmapped=warn_unmapped)

    def create_parameter_df(self, *args, **kwargs):
        """Create a new PEtab parameter table

        See create_parameter_df
        """
        return parameters.create_parameter_df(
            self.sbml_model,
            self.condition_df,
            self.measurement_df,
            *args, **kwargs)

    def sample_parameter_startpoints(self, n_starts: int = 100):
        """Create starting points for optimization

        See sample_parameter_startpoints
        """
        return sampling.sample_parameter_startpoints(
            self.parameter_df, n_starts=n_starts)


def get_default_condition_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"experimentalCondition_{model_name}.tsv")


def get_default_measurement_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"measurementData_{model_name}.tsv")


def get_default_parameter_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"parameters_{model_name}.tsv")


def get_default_sbml_file_name(model_name: str, folder: str = ''):
    """Get file name according to proposed convention"""
    return os.path.join(folder, f"model_{model_name}.xml")
