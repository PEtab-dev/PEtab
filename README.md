![CI tests](https://github.com/PEtab-dev/PEtab/workflows/CI%20tests/badge.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/fd7dd5cee68e449983be5c43f230c7f3)](https://www.codacy.com/gh/PEtab-dev/PEtab?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PEtab-dev/PEtab&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/PEtab-dev/PEtab/branch/master/graph/badge.svg)](https://codecov.io/gh/PEtab-dev/PEtab)
[![PyPI version](https://badge.fury.io/py/petab.svg)](https://badge.fury.io/py/petab)

# PEtab -- a data format for specifying parameter estimation problems in systems biology

![Logo](doc/logo/PEtab.png)

*PEtab* is a data format for specifying parameter estimation problems in systems biology.
This repository provides extensive documentation and a Python library for easy
access and validation of *PEtab* files.

## About PEtab

PEtab is built around [SBML](http://sbml.org/) and based on tab-separated values 
(TSV) files. It is meant as a standardized way to provide information for 
parameter estimation, which is out of the current scope of SBML. This includes
for example:

  - Specifying and linking measurements to models

    - Defining model outputs

    - Specifying noise models

  - Specifying parameter bounds for optimization

  - Specifying multiple simulation condition with potentially shared parameters

## Documentation

Documentation of the PEtab data format and Python library is available at
[https://petab.readthedocs.io/en/latest/](https://petab.readthedocs.io/en/latest/).

## Examples

A wide range of PEtab examples can be found in the systems biology optimization
[benchmark problem collection](https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab).


## PEtab support in systems biology tools

Where PEtab is supported:


  - A PEtab -> [COPASI](http://copasi.org/)
    [converter](https://github.com/copasi/python-petab-importer)

  - [d2d](https://github.com/Data2Dynamics/d2d/)

  - [dMod](https://github.com/dkaschek/dMod/)

  - [meigo](http://gingproc.iim.csic.es/meigo.html)

  - [AMICI](https://github.com/ICB-DCM/AMICI/)

  - [pyPESTO](https://github.com/ICB-DCM/pyPESTO/)

  - [pyABC](https://github.com/ICB-DCM/pyABC/)

If your project or tool is using PEtab, and you would like to have it listed
here, please let us know.

### PEtab features supported in different tools

The following list provides an overview of supported PEtab features in
different tools, based on passed test cases of the
[PEtab test suite](https://github.com/PEtab-dev/petab_test_suite):

| ID | Test                                                           | AMICI<br>*`develop`* | AMIGO | Copasi | D2D | dMod |
|----|----------------------------------------------------------------|-------|-------|--------|-----|------|
| 1  | Basic simulation                                               | +++   |       |        |     |      |
| 2  | Multiple simulation conditions                                 | +++   |       |        |     |      |
| 3  | Numeric observable parameter overrides in measurement table    | +++   |       |        |     |      |
| 4  | Parametric observable parameter overrides in measurement table | +++   |       |        |     |      |
| 5  | Parametric overrides in condition table                        | +++   |       |        |     |      |
| 6  | Time-point specific overrides in the measurement table         | ---   |       |        |     |      |
| 7  | Observable transformations (lin, log, log10)                   | +-+   |       |        |     |      |
| 8  | Replicate measurements                                         | +++   |       |        |     |      |
| 9  | Pre-equilibration                                              | +++   |       |        |     |      |
| 10 | Partial pre-equilibration                                      | +++   |       |        |     |      |
| 11 | Numeric initial concentration in condition table               | +++   |       |        |     |      |
| 12 | Numeric initial compartment sizes in condition table           | ---   |       |        |     |      |
| 13 | Parametric initial concentrations in condition table           | +++   |       |        |     |      |
| 14 | Numeric noise parameter overrides in measurement table         | +++   |       |        |     |      |
| 15 | Parametric noise parameter overrides in measurement table      | +++   |       |        |     |      |

    Legend:
    * First character indicates whether simulations the respective features is supported and simulations are correct (+) or not (-)
    * Second character indicates whether computing residuals are supported and correct (+) or not (-)
    * Third character indicates whether computing likelihood is supported and correct (+) or not (-)

## Using PEtab

If you would like to use PEtab yourself, please have a look at 
[doc/documentation_data_format.md](doc/documentation_data_format.md) or at
the example models provided in the 
[benchmark collection](https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab).

To convert your existing parameter estimation problem to the PEtab format, you 
will have to:

1. Specify your model in SBML

1. Set up model outputs and noise model using `AssignmentRule`s as described in 
  the PEtab documentation

1. Create a condition table, if appropriate

1. Create a table of observables

1. Create a table of measurements

1. Create a parameter table

If you are using Python, some handy functions of the
[PEtab library](https://petab.readthedocs.io/en/latest/modules.html) can help
you with that. This include also a PEtab validator called `petablint` which
you can use to check if your files adhere to the PEtab standard. If you have 
further questions regarding PEtab, feel free to post an 
[issue](https://github.com/PEtab-dev/PEtab/issues) at our github repository.

## PEtab Python library

PEtab comes with a Python package for creating, checking, and working with 
PEtab files. This library is available on pypi and the easiest way to install 
it is running

    pip3 install petab
    
It will require Python>=3.6 to run.

Development versions of the PEtab library can be installed using

    pip3 install https://github.com/PEtab-dev/PEtab/archive/develop.zip

(replace `develop` by the branch or commit you would like to install).

When setting up a new parameter estimation problem, the most useful tools will
be:

  - The **PEtab validator**, which is now automatically installed using Python
    entrypoints to be available as a shell command from anywhere called
    `petablint`

  - `petab.create_parameter_df` to create the parameter table, once you
    have set up the model, condition table, observable table and measurement
    table

  - `petab.create_combine_archive` to create a
    [COMBINE Archive](https://combinearchive.org/index/) from PEtab files

## Extending PEtab

We are aware of the fact that PEtab may not serve everybody's needs. If you 
have a suggestion of how to extend PEtab, feel free to post an issue at our 
github repository.
