#!/usr/bin/env python3

"""Command line tool to check for correct format"""

import argparse
import sys
import os
sys.path.append(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0])
import petab


def parse_cli_args():
    """Parse command line argumentss"""

    parser = argparse.ArgumentParser(
        description='Check if a set of files adheres to the PEtab format.')

    parser.add_argument('-s', '--sbml', dest='sbml_file_name',
                        help='SBML model filename', required=True)
    parser.add_argument('-m', '--measurements', dest='measurement_file_name',
                        help='Measurement table', required=True)
    parser.add_argument('-c', '--conditions', dest='condition_file_name',
                        help='Conditions table', required=True)
    parser.add_argument('-p', dest='parameter_file_name',
                        help='Parameter table', required=True)

    args = parser.parse_args()

    return args


def main():
    args = parse_cli_args()

    problem = petab.OptimizationProblem(args.sbml_file_name,
                                        args.measurement_file_name,
                                        args.condition_file_name,
                                        args.parameter_file_name)


    # TODO: extend
    petab.lint.check_measurement_df(problem.measurement_df)
    petab.lint.check_condition_df(problem.condition_df)
    petab.lint.check_parameter_df(problem.parameter_df)
    petab.lint.parameterId_is_string(problem.parameter_df)
    petab.lint.parameterScale_is_valid(problem.parameter_df)
    petab.lint.assert_measured_observables_present_in_model(problem.measurement_df, problem.sbml_model)
    petab.lint.assert_overrides_match_parameter_count(problem.measurement_df,
                                                      petab.get_observables(problem.sbml_model, remove=False),
                                                      petab.get_sigmas(problem.sbml_model, remove=False))


if __name__ == '__main__':
    main()
