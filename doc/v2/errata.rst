.. _v2_errata:

PEtab 2.0 errata
================

This page lists corrections and clarifications to the
:ref:`PEtab 2.0.0 specification <v2_spec>`.
Errata resolve errors, inconsistencies, or ambiguities in the specification
and apply to the version they are listed for. Implementations of that version
should follow them.

Errata are classified as:

* *editorial*: wording, formatting, or typos without effect on the meaning
  of the specification,
* *clarification*: resolves an ambiguity without changing the intended
  meaning,
* *technical*: resolves an error or inconsistency that affects the
  interpretation of PEtab problems.

The specification text has been updated accordingly.

.. _v2_errata_e1:

E1: Infinite parameter bounds
-----------------------------

:Type: technical
:Affects: :ref:`v2_parameter_table`, :ref:`v2_objective_function`
:Discussion: `#682 <https://github.com/PEtab-dev/PEtab/issues/682>`__

**Problem:**
``lowerBound`` and ``upperBound`` were specified as ``NUMERIC``, which
excludes infinite values. At the same time, the ``priorDistribution``
description states that a non-truncated prior can be obtained by setting the
parameter bounds to the prior's domain (e.g., ``0`` and ``inf`` for
``log-normal``), which requires infinite bounds.

**Resolution:**

* ``lowerBound`` may be ``-inf``, ``upperBound`` may be ``inf``.
  ``inf`` as lower bound and ``-inf`` as upper bound remain invalid.
  ``nominalValue`` is addressed by :ref:`erratum E3 <v2_errata_e3>`.
* If priors are specified for any parameter, the default
  ``uniform(lowerBound, upperBound)`` prior for the remaining parameters is
  improper for infinite bounds. Therefore, in this case, a proper prior
  must be specified for every estimated parameter with an infinite bound.

.. _v2_errata_e2:

E2: Priors of non-estimated parameters
--------------------------------------

:Type: clarification
:Affects: :ref:`v2_parameter_table`, :ref:`v2_objective_function`
:Discussion: `#686 <https://github.com/PEtab-dev/PEtab/pull/686>`__

**Problem:**
The ``priorDistribution`` description did not specify whether priors of
parameters with ``estimate==false`` are used. It stated that, if priors are
specified for a subset of parameters, the other parameters default to a
``uniform(lowerBound, upperBound)`` prior. For parameters with
``estimate==false``, ``lowerBound`` and ``upperBound`` are optional, so this
default prior may be undefined. The :ref:`v2_objective_function` section, in
contrast, defines the prior only for the estimated parameters.

**Resolution:**

* Priors are only used for parameters with ``estimate==true``.
  For parameters with ``estimate==false``, ``priorDistribution`` and
  ``priorParameters`` are ignored.
* The default ``uniform(lowerBound, upperBound)`` prior applies only to
  estimated parameters, and only if priors are specified for any estimated
  parameter.

.. _v2_errata_e3:

E3: Infinite parameter values
-----------------------------

:Type: technical
:Affects: :ref:`v2_parameter_table`, :ref:`v2_measurement_table`
:Discussion: `#685 <https://github.com/PEtab-dev/PEtab/issues/685>`__,
  `#687 <https://github.com/PEtab-dev/PEtab/pull/687>`__

**Problem:**
``nominalValue`` was specified as ``NUMERIC``, which excludes infinite
values. At the same time, the list of changes from PEtab 1 states that the
effect of the removed ``parameterScale`` column can be obtained by
transforming the model parameters in the model file. This does not hold for
fixed parameters on the boundary of their domain: in PEtab 1, a parameter
``k1`` with ``parameterScale=log`` can be fixed to ``nominalValue=0``
(nominal values are on linear scale). For a model reparameterized in terms of
``log_k1``, the corresponding nominal value is ``-inf``.

The same applies to numeric values in ``observableParameters`` and
``noiseParameters`` in the measurement table, which were specified as
``NUMERIC``. Since these entries may also reference parameters from the
parameter table, an infinite value could be given via a parameter, but not
directly.

**Resolution:**

* ``nominalValue`` may be ``inf`` or ``-inf``. ``NaN`` remains invalid.
* Numeric values in ``observableParameters`` and ``noiseParameters`` may be
  ``inf`` or ``-inf``. ``NaN`` remains invalid.
* For parameters with ``estimate==false``, infinite nominal values are applied
  as specified.
* For parameters with ``estimate==true``, ``nominalValue`` does not affect the
  problem definition, so infinite values have no further implications.
