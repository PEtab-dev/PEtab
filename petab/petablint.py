#!/usr/bin/env python3

"""Command line tool to check for correct format"""

import argparse
import logging
import os
import sys

import petab
from colorama import (init as init_colorama, Fore)

logger = logging.getLogger(__name__)


class LintFormatter(logging.Formatter):
    """Custom log formatter"""
    formats = {
        logging.DEBUG: Fore.CYAN + '%(message)s',
        logging.INFO: Fore.GREEN + '%(message)s',
        logging.WARN: Fore.YELLOW + '%(message)s',
        logging.ERROR: Fore.RED + '%(message)s',
    }

    def format(self, record):
        # pylint: disable=protected-access
        format_orig = self._style._fmt
        self._style._fmt = LintFormatter.formats.get(record.levelno, self._fmt)
        result = logging.Formatter.format(self, record)
        self._style._fmt = format_orig
        return result


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
    parser.add_argument('-o', '--observables', dest='observable_file_name',
                        help='Observable table')
    parser.add_argument('-m', '--measurements', dest='measurement_file_name',
                        help='Measurement table')
    parser.add_argument('-c', '--conditions', dest='condition_file_name',
                        help='Conditions table')
    parser.add_argument('-p', '--parameters', dest='parameter_file_name',
                        help='Parameter table')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-y', '--yaml', dest='yaml_file_name',
                       help='PEtab YAML problem filename')

    # or with model name, following default naming
    group.add_argument('-n', '--model-name', dest='model_name',
                       help='Model name where all files are in the working '
                            'directory and follow PEtab naming convention. '
                            'Specifying -[smcp] will override defaults')
    parser.add_argument('-d', '--directory', dest='directory',
                        default=os.getcwd())
    args = parser.parse_args()

    if args.model_name:
        if not args.sbml_file_name:
            args.sbml_file_name = petab.get_default_sbml_file_name(
                args.model_name,
                folder=args.directory,
            )
        if not args.measurement_file_name:
            args.measurement_file_name = \
                petab.get_default_measurement_file_name(
                    args.model_name,
                    folder=args.directory,
                )
        if not args.condition_file_name:
            args.condition_file_name = petab.get_default_condition_file_name(
                args.model_name,
                folder=args.directory,
            )
        if not args.parameter_file_name:
            args.parameter_file_name = petab.get_default_parameter_file_name(
                args.model_name,
                folder=args.directory,
            )

    if (args.yaml_file_name
            and any((args.sbml_file_name, args.condition_file_name,
                     args.measurement_file_name, args.parameter_file_name))):
        parser.error('When providing a yaml file, no other files may '
                     'be specified.')

    if (not args.model_name
            and not any([args.sbml_file_name, args.condition_file_name,
                         args.measurement_file_name, args.parameter_file_name,
                         args.observable_file_name, args.yaml_file_name])):
        parser.error('Neither model name nor any filename specified. '
                     'What shall I do?')

    return args


def main():
    """Run PEtab validator"""
    args = parse_cli_args()
    init_colorama(autoreset=True)

    ch = logging.StreamHandler()
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.WARN)
    ch.setFormatter(LintFormatter())
    logging.basicConfig(level=logging.DEBUG, handlers=[ch])

    if args.yaml_file_name:
        from petab.yaml import validate
        from jsonschema.exceptions import ValidationError
        try:
            validate(args.yaml_file_name)
        except ValidationError as e:
            logger.error("Provided YAML file does not adhere to PEtab "
                         f"schema: {e}")
            sys.exit(1)

        if petab.is_composite_problem(args.yaml_file_name):
            # TODO: further checking:
            #  https://github.com/ICB-DCM/PEtab/issues/191
            #  problem = petab.CompositeProblem.from_yaml(args.yaml_file_name)
            return

        problem = petab.Problem.from_yaml(args.yaml_file_name)

    else:
        logger.debug('Looking for...')
        if args.sbml_file_name:
            logger.debug(f'\tSBML model: {args.sbml_file_name}')
        if args.condition_file_name:
            logger.debug(f'\tCondition table: {args.condition_file_name}')
        if args.observable_file_name:
            logger.debug(f'\tObservable table: {args.observable_file_name}')
        if args.measurement_file_name:
            logger.debug(f'\tMeasurement table: {args.measurement_file_name}')
        if args.parameter_file_name:
            logger.debug(f'\tParameter table: {args.parameter_file_name}')

        try:
            problem = petab.Problem.from_files(
                sbml_file=args.sbml_file_name,
                condition_file=args.condition_file_name,
                measurement_file=args.measurement_file_name,
                parameter_file=args.parameter_file_name,
                observable_files=args.observable_file_name
            )
        except FileNotFoundError as e:
            logger.error(e)
            sys.exit(1)

    ret = petab.lint.lint_problem(problem)
    sys.exit(ret)


if __name__ == '__main__':
    main()
