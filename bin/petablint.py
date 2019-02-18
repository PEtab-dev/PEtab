#!/usr/bin/env python3

"""Command line tool to check for correct format"""

import argparse
import petab
import sys
import logging
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
        # TODO: we should also allow running (limited) tests on a subset of
        # files
        parser.error('When not specifying a model name, sbml, '
                     'condition and measurement file must be specified')

    return args


def main():
    args = parse_cli_args()
    init_colorama(autoreset=True)

    ch = logging.StreamHandler()
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.WARN)
    ch.setFormatter(LintFormatter())
    logging.basicConfig(level=logging.DEBUG, handlers=[ch])

    logger.debug('Looking for...')
    if args.sbml_file_name:
        logger.debug('\tSBML model: ' + args.sbml_file_name)
    if args.condition_file_name:
        logger.debug('\tCondition table: ' + args.condition_file_name)
    if args.measurement_file_name:
        logger.debug('\tMeasurement table: ' + args.measurement_file_name)
    if args.parameter_file_name:
        logger.debug('\tParameter table: ' + args.parameter_file_name)

    try:
        problem = petab.Problem.from_files(
            sbml_file=args.sbml_file_name,
            condition_file=args.condition_file_name,
            measurement_file=args.measurement_file_name,
            parameter_file=args.parameter_file_name)
    except FileNotFoundError as e:
        logger.error(e)
        sys.exit(1)

    ret = petab.lint.lint_problem(problem)
    sys.exit(ret)


if __name__ == '__main__':
    main()
