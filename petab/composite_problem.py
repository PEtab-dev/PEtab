"""PEtab problems consisting of multiple models"""
import os
from typing import List, Union, Dict

import pandas as pd

from . import parameters
from . import problem
from . import yaml


class CompositeProblem:
    """Representation of a PEtab problem consisting of multiple models

    Attributes:
        problems:
            List ``petab.Problems``
        parameter_df:
            PEtab parameter DataFrame
    """

    def __init__(
            self,
            parameter_df: pd.DataFrame = None,
            problems: List[problem.Problem] = None):
        """Constructor

        Arguments:
            parameter_df:
                see CompositeProblem.parameter_df
            problems:
                see CompositeProblem.problems
        """
        self.problems: List[problem.Problem] = problems
        self.parameter_df: pd.DataFrame = parameter_df

    @staticmethod
    def from_yaml(yaml_config: Union[Dict, str]
                  ) -> 'CompositeProblem':
        """Create from YAML file

        Factory method to create a CompositeProblem instance from a PEtab
        YAML config file

        Arguments:
            yaml_config: PEtab configuration as dictionary or YAML file name
        """

        if isinstance(yaml_config, str):
            path_prefix = os.path.dirname(yaml_config)
            yaml_config = yaml.load_yaml(yaml_config)
        else:
            path_prefix = ""

        parameter_df = parameters.get_parameter_df(
            os.path.join(path_prefix, yaml_config['parameter_file']))

        problems = []
        for problem_config in yaml_config['problems']:
            yaml.assert_single_condition_and_sbml_file(problem_config)

            # don't set parameter file if we have multiple models
            cur_problem = problem.Problem.from_files(
                sbml_file=os.path.join(
                    path_prefix, problem_config['sbml_files'][0]),
                measurement_file=os.path.join(
                    path_prefix, problem_config['measurement_files']),
                condition_file=os.path.join(
                    path_prefix, problem_config['condition_files'][0]),
            )
            problems.append(cur_problem)

        return CompositeProblem(parameter_df=parameter_df,
                                problems=problems)
