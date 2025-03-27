================
Software support
================

Where PEtab is supported (in alphabetical order):

* `AMICI <https://github.com/ICB-DCM/AMICI/>`__
  (`Example <https://github.com/ICB-DCM/AMICI/blob/master/python/examples/example_petab/petab.ipynb>`__)

* A PEtab -> `COPASI <http://copasi.org/>`__
  `converter <https://github.com/copasi/python-petab-importer>`__

* `d2d <https://github.com/Data2Dynamics/d2d/>`__
  (`HOWTO <https://github.com/Data2Dynamics/d2d/wiki/Support-for-PEtab>`__)

* `dMod <https://github.com/dkaschek/dMod/>`__
  (`HOWTO <https://github.com/dkaschek/dMod/wiki/Support-for-PEtab>`__)

* `MEIGO <https://github.com/gingproc-IIM-CSIC/MEIGO64>`__
  (`HOWTO <https://github.com/gingproc-IIM-CSIC/MEIGO64/tree/master/MEIGO/PEtabMEIGO>`__)

* `parPE <https://github.com/ICB-DCM/parPE/>`__

* `PEtab.jl <https://github.com/sebapersson/PEtab.jl>`__
  (`HOWTO <https://sebapersson.github.io/PEtab.jl/stable/>`__)

* `PumasQSP.jl <https://help.juliahub.com/pumasqsp/stable/>`__
  (`HOWTO <https://help.juliahub.com/pumasqsp/stable/tutorials/petabimport/>`__)

* `pyABC <https://github.com/ICB-DCM/pyABC/>`__
  (`Example <https://pyabc.readthedocs.io/en/latest/examples/petab.html>`__)

* `pyPESTO <https://github.com/ICB-DCM/pyPESTO/>`__
  (`Example <https://pypesto.readthedocs.io/en/latest/example/petab_import.html>`__)

* `SBML2Julia <https://github.com/paulflang/SBML2Julia>`__
  (`Tutorial <https://sbml2julia.readthedocs.io/en/latest/python_api.html>`__)

If your project or tool is using PEtab, and you would like to have it listed
here, please `let us know <https://github.com/PEtab-dev/PEtab/issues>`__.

PEtab features supported in different tools
===========================================

The following table provides an overview of supported PEtab features in
different tools, based on passed test cases of the
`PEtab test suite <https://github.com/PEtab-dev/petab_test_suite>`__:

..
   START TABLE Tool support (GENERATED, DO NOT EDIT, INSTEAD EDIT IN PEtab/doc/src)
.. list-table:: Tool support
   :header-rows: 1

   * - | ID
     - | Test
     - | AMICI;`>=0.11.19`
     - | Copasi
     - | D2D
     - | dMod
     - | MEIGO
     - | parPE;`develop`
     - | PEtab.jl;`>=1.1.0`
     - | PumasQSP
     - | pyABC;`>=0.10.1`
     - | pyPESTO;`>=0.0.11`
     - | SBML2Julia
   * - 1
     - Basic simulation
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - +++
     - +++
     - +++
     - +++
   * - 2
     - Multiple simulation conditions
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - +++
     - +++
     - +++
     - +++
   * - 3
     - Numeric observable parameter overrides in measurement table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++
   * - 4
     - Parametric observable parameter overrides in measurement table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - +++
     - +++
     - +++
     - +++
   * - 5
     - Parametric overrides in condition table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - +++
     - +++
     - +++
     - +++
   * - 6
     - Time-point specific overrides in the measurement table
     - ---
     - ---
     - +++
     - +++
     - +++
     - ---
     - +++
     - ---
     - ---
     - ---
     - +++
   * - 7
     - Observable transformations to log10 scale
     - +++
     - +++
     - +++
     - ++-
     - +++
     - --+
     - +++
     - +-+
     - +++
     - +++
     - +++
   * - 8
     - Replicate measurements
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - +++
     - +++
     - +++
     - +++
   * - 9
     - Pre-equilibration
     - +++
     - ---
     - +++
     - +++
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++
   * - 10
     - Partial pre-equilibration
     - +++
     - ---
     - +++
     - +++
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++
   * - 11
     - Numeric initial concentration in condition table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - +++
     - +++
     - +++
     - +++
   * - 12
     - Numeric initial compartment sizes in condition table
     - ---
     - +++
     - +++
     - +++
     - +++
     - ---
     - +++
     - ---
     - ---
     - ---
     - +++
   * - 13
     - Parametric initial concentrations in condition table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++
   * - 14
     - Numeric noise parameter overrides in measurement table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++
   * - 15
     - Parametric noise parameter overrides in measurement table
     - +++
     - +++
     - +++
     - +++
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++
   * - 16
     - Observable transformations to log scale
     - +++
     - +++
     - +++
     - ++-
     - +++
     - --+
     - +++
     - ---
     - +++
     - +++
     - +++

..
   END TABLE Tool support


Legend:

* First character indicates whether computing simulated data is supported
  and simulations are correct (+) or not (-).
* Second character indicates whether computing chi2 values
  of residuals are supported and correct (+) or not (-).
* Third character indicates whether computing likelihoods is supported
  and correct (+) or not (-).
