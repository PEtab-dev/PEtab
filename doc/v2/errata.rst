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
  ``nominalValue`` remains ``NUMERIC``, i.e., finite.
* If priors are specified for any parameter, the default
  ``uniform(lowerBound, upperBound)`` prior for the remaining parameters is
  improper for infinite bounds. Therefore, in this case, ``priorDistribution``
  must be specified for every estimated parameter with an infinite bound.
