#!/usr/bin/env python3

"""Command line tool to check for correct format"""

import argparse
import petab


def parse_cli_args():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description='Check if a set of files adheres to the PEtab format.')

    # General options:
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='More verbose output')

    # Call with set of files
    parser.add_argument('-s', '--sbml', dest='sbml_file_name',
                        help='SBML model filename')
    parser.add_argument('-m', '--measurements', dest='measurement_file_name',
                        help='Measurement table')
    parser.add_argument('-c', '--conditions', dest='condition_file_name',
                        help='Conditions table')
    parser.add_argument('-p', '--parameters', dest='parameter_file_name',
                        help='Parameter table')

    # or with model name, following default naming
    parser.add_argument('-n', '--model-name', dest='model_name',
                       help='Model name where all files are in the working '
                            'directory and follow PEtab naming convention. '
                            'Specifying -[smcp] will override defaults')
    args = parser.parse_args()

    if args.model_name:
        if not args.sbml_file_name:
            args.sbml_file_name = petab.get_default_sbml_file_name(
                args.model_name)
        if not args.measurement_file_name:
            args.measurement_file_name = \
                petab.get_default_measurement_file_name(args.model_name)
        if not args.condition_file_name:
            args.condition_file_name = petab.get_default_condition_file_name(
                args.model_name)
        if not args.parameter_file_name:
            args.parameter_file_name = petab.get_default_parameter_file_name(
                args.model_name)

    if not args.model_name and \
            (not args.sbml_file_name
             or not args.condition_file_name
             or not args.measurement_file_name):
        # TODO: we should also allow running (limited) tests on a subset of files
        parser.error('When not specifying a model name, sbml, '
                     'condition and measurement file must be specified')

    return args


def main():
    args = parse_cli_args()

    if args.verbose:
        print('Checking...')
        print('\tSBML model:', args.sbml_file_name)
        print('\tCondition table:', args.condition_file_name)
        print('\tMeasurement table:', args.measurement_file_name)
        print('\tParameter table:', args.parameter_file_name)

    problem = petab.Problem(args.sbml_file_name,
                            args.condition_file_name,
                            args.measurement_file_name,
                            args.parameter_file_name)

    petab.lint.lint_problem(problem)


if __name__ == '__main__':
    main()
