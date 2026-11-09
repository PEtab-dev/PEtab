.. _v2_migration_guide:

Upgrading from PEtab v1
=======================

.. note::

   This guide is non-normative. It explains what the changes from PEtab v1
   mean for an existing PEtab v1 problem, and how to convert such a problem to
   PEtab v2 so that it still describes the same estimation problem.
   The :ref:`PEtab 2.0 specification <v2_spec>` is authoritative;
   its section :ref:`v2_changes` lists all changes.

Overview
--------

Most changes between PEtab v1 and v2 are structural: the same information is
written differently, and a conversion is purely mechanical.
A few changes affect the objective function, its optimum, or the prior
distribution. These require a decision during the conversion.
The most important one is the removal of ``parameterScale``
(:ref:`v2_migration_parameter_scale`).

PEtab v1 never defined the objective function. It specified the likelihood,
but not how priors on log-scaled parameters enter the objective, and tools
implemented this differently. PEtab v2 defines the
:ref:`objective function <v2_objective_function>` completely.
In this guide, a conversion is called *faithful* if the v2 problem has the
same likelihood and the same optimum as the v1 problem, and, for problems
with priors, the same prior distribution and the same objective function up
to an additive constant. "The same" refers to how the v1 problem was
evaluated by the tools that created it (:ref:`v2_migration_v1_tools`).

Quick path
~~~~~~~~~~

For a typical v1 problem (SBML model, parameters estimated on ``log10``
scale):

1. Convert with the `libpetab-python
   <https://github.com/PEtab-dev/libpetab-python>`__ function
   ``petab.v2.petab1to2`` (version 0.10.0 or later):

   .. code-block:: python

      from petab.v2 import petab1to2

      petab1to2("v1/problem.yaml", output_dir="v2", reparametrize="all")

   Pass ``reparametrize="all"`` explicitly. The default, ``"none"``, keeps
   all parameters on linear scale and moves the optimum for parameters with
   ``parameterScale*`` priors.
   With ``"all"``, every estimated ``log10``-scaled parameter ``k`` is
   replaced by a parameter ``log10_k`` with log-transformed bounds, nominal
   value and prior, and the model computes ``k = 10^log10_k``
   (``log_k`` and ``exp(log_k)`` for ``log`` scale). Parameters with a
   linear-scale prior (``normal``, ``laplace``, ``logNormal``,
   ``logLaplace``, ``uniform``) stay on linear scale. A lower bound of
   ``0`` becomes ``-inf``.
   The options are compared in :ref:`v2_migration_petab1to2`. In short:

   * No priors: ``"all"`` keeps gradients with respect to the
     log-transformed value, optimization scale and start point sampling
     as in v1. ``"none"`` gives the same optimum, but the parameters are
     then estimated on linear scale.
   * ``parameterScale*`` priors: ``"all"`` (or ``"priors"``). ``"none"``
     moves the optimum.
   * Only linear-scale priors: these parameters are not reparametrized by
     any option.

2. Read the warnings and do what ``petab1to2`` does not do:

   * Rewrite ``observableFormula`` expressions that reference other
     observables (:ref:`v2_migration_structural`).
   * If the conversion fails because a measurement table placeholder receives
     overrides that cannot be log-transformed, split the affected observable
     first (:ref:`v2_migration_reparametrization`).
   * Configure non-default initialization priors in the tool
     (:ref:`v2_migration_init_priors`).

3. Adjust the tool settings. Optimization scale and start point sampling are
   no longer part of the problem. The reparametrized parameters are already
   log-transformed and must not be log-transformed again by the tool.

4. Check the result as described in :ref:`v2_migration_verification`.

The rest of this guide explains the individual changes and how to perform a
conversion by hand.

Notation
--------

As in the :ref:`v2 specification <v2_objective_function>`, :math:`\theta`
denotes the vector of parameters as they appear in the parameter table,
and :math:`x` a single such parameter. In PEtab v1, these are the values on
linear scale, which is what ``lowerBound``, ``upperBound`` and
``nominalValue`` refer to.
:math:`\tilde{x}` denotes the value of a v1 parameter on its
``parameterScale``, i.e., :math:`\tilde{x} = \log_{10} x` for ``log10``,
:math:`\tilde{x} = \ln x` for ``log``, and :math:`\tilde{x} = x` for ``lin``.
:math:`\tilde{\theta}` is the respective vector.
For example, a ``log10``-scaled parameter with ``nominalValue`` ``100`` has
:math:`x = 100` and :math:`\tilde{x} = 2`.
A parameter with ``parameterScale`` ``log`` or ``log10`` is called
*log-scaled* below. Formulas are written for ``log10``; for ``log``,
:math:`\ln 10` becomes :math:`1`, and ``log10_k`` with ``k = 10^log10_k``
becomes ``log_k`` with ``k = exp(log_k)``.

.. _v2_migration_structural:

Structural changes
------------------

The following changes only affect how a problem is written.
``petab1to2`` handles all of them, except where noted.

.. list-table::
   :header-rows: 1
   :widths: 25 40 35

   * - PEtab v1
     - PEtab v2
     - Notes, manual steps
   * - Optional YAML file with a ``problems`` list
     - Mandatory :ref:`YAML file <v2_problem_yaml>` with a flat structure
       and ``model_files`` entries with ``location`` and ``language``
     -
   * - Condition table in wide format, one column per overridden entity
     - :ref:`Condition table <v2_condition_table>` in long format,
       one row per ``conditionId``, ``targetId`` and ``targetValue``
     - Conditions that don't change anything are not needed anymore.
       The condition table is optional.
   * - ``simulationConditionId`` and ``preequilibrationConditionId``
       in the measurement table
     - ``experimentId`` in the :ref:`measurement table <v2_measurement_table>`
       and an :ref:`experiment table <v2_experiment_table>`
     - A pre-equilibration condition becomes a period starting at
       ``-inf``, the simulation condition a period starting at ``0``.
       Measurements without any condition don't need an experiment.
   * - ``observableParameter${n}_${observableId}`` and
       ``noiseParameter${n}_${observableId}`` placeholders by naming
       convention
     - Placeholders declared in the ``observablePlaceholders`` and
       ``noisePlaceholders`` columns of the
       :ref:`observable table <v2_observable_table>`
     - The v1 names remain valid placeholder IDs.
   * - ``observableTransformation`` (``lin``, ``log``, ``log10``) and
       ``noiseDistribution`` (``normal``, ``laplace``)
     - A single ``noiseDistribution`` column (``normal``, ``log-normal``,
       ``laplace``, ``log-laplace``)
     - ``log10`` requires a rescaled noise formula, which ``petab1to2``
       inserts, see :ref:`v2_migration_log10_observables`.
   * - ``estimate`` as ``0`` / ``1``
     - ``estimate`` as ``false`` / ``true``
     -
   * - ``objectivePriorType`` and ``objectivePriorParameters``
     - ``priorDistribution`` and ``priorParameters``
     - The set of distributions changed. ``logNormal`` becomes
       ``log-normal``, ``logLaplace`` becomes ``log-laplace``.
       For the ``parameterScale*`` priors,
       see :ref:`v2_migration_parameter_scale`.
   * - Visualization table
     - Removed
     - Visualization files are not part of a PEtab v2 problem.
   * - Observable IDs allowed in ``observableFormula``
     - Not allowed; only an observable's own ID may be used in its
       ``noiseFormula``
     - **By hand:** substitute the referenced observable's formula.
       ``petab1to2`` does not do this.

.. _v2_migration_parameter_scale:

Parameter scaling
-----------------

In short: PEtab v2 has no ``parameterScale``. A parameter ``k`` that was
estimated on ``log10`` scale in v1 is still estimated on ``log10`` scale in
v2 by making the log-transformed value the parameter: ``log10_k`` is listed
in the parameter table, and the model computes ``k = 10^log10_k``.
For a faithful conversion, this reparametrization is recommended for all
``log``- and ``log10``-scaled parameters, except those with a linear-scale
prior (``normal``, ``laplace``, ``logNormal``, ``logLaplace``, ``uniform``).
The steps are described in :ref:`v2_migration_reparametrization`;
``petab1to2`` performs them with ``reparametrize="all"``
(:ref:`v2_migration_petab1to2`). The following subsections explain why.

What PEtab v1 specified
~~~~~~~~~~~~~~~~~~~~~~~

In PEtab v1, every parameter had a ``parameterScale`` of ``lin``, ``log`` or
``log10``, the "scale of the parameter to be used during parameter
estimation". Bounds and nominal values were always given on linear scale.
Priors came in two groups:

* ``uniform``, ``normal``, ``laplace``, ``logNormal`` and ``logLaplace``
  were defined "on linear parameters", with prior parameters on linear scale.
* ``parameterScaleUniform``, ``parameterScaleNormal`` and
  ``parameterScaleLaplace`` were defined "on original parameter scale", with
  prior parameters on parameter scale. For example, ``parameterScaleNormal``
  with parameters ``mu;sigma`` on a ``log10``-scaled parameter means
  :math:`\log_{10} x \sim \mathcal{N}(\mu, \sigma^2)`.
* The default was ``parameterScaleUniform`` within the bounds, described as
  "equivalent to no prior".

In addition, ``initializationPriorType`` specified how start points for
optimization were sampled, with the same default.

Two things were not specified. First, the objective function itself.
Second, and as a consequence, how a prior on a log-scaled parameter enters
it: as a density over the scaled parameter :math:`\tilde{x}`, or as a
density over :math:`x`. The two differ by the Jacobian of the scale
transformation, which adds :math:`\ln(x \ln 10)` to the negative log-prior
for ``log10``. This term is not constant, so the two readings have
different optima.

.. _v2_migration_v1_tools:

How PEtab v1 tools implemented it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following describes the behavior of some tools at the linked commits.
Other tools have not been surveyed.

* **D2D** and **pyPESTO** evaluate ``parameterScale*`` priors as densities
  over the scaled parameter :math:`\tilde{x}`, without a Jacobian
  (D2D `arCollectRes.m <https://github.com/Data2Dynamics/d2d/blob/10d06626320f799583c74339c7a5b0050e3cbf39/arFramework3/Subfunctions/arCollectRes.m#L344-L345>`__,
  pyPESTO `priors.py <https://github.com/ICB-DCM/pyPESTO/blob/4b5fbacd35770727518c0faf1a43eea053419f83/pypesto/objective/priors.py#L297-L339>`__).
  pyPESTO evaluates the linear-scale priors (``normal``, ``logNormal``, ...)
  as densities over :math:`x`, also without a Jacobian.
  Problems that were created with these tools have their published optima
  under this reading. This was confirmed for the problems with priors in the
  `benchmark collection <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/issues/333>`__.
* **libpetab-python**'s v1 ``Prior`` class evaluates all priors as densities
  over :math:`x`, with the Jacobian
  (`priors.py <https://github.com/PEtab-dev/libpetab-python/blob/68f8b6938088695634906990c37ef33bd5aa9d58/petab/v1/priors.py#L118-L149>`__).
  For a ``parameterScaleNormal`` prior on a ``log10``-scaled parameter,
  this is a log-normal density over :math:`x`, and the optimum differs from
  the D2D/pyPESTO one.
* Gradients are commonly reported with respect to the scaled parameters
  :math:`\tilde{\theta}` (e.g., AMICI, pyPESTO), and start points are
  sampled on the parameter scale. Optimizer steps and convergence criteria
  depend on which variable the gradient refers to.

For log-scaled parameters with priors, objective values and optima therefore
differ between v1 tools. Gradients with respect to :math:`\tilde{x}` and
with respect to :math:`x` differ by the factor :math:`x \ln 10` for a
``log10``-scaled parameter. This guide follows the D2D/pyPESTO reading.

What PEtab v2 specifies
~~~~~~~~~~~~~~~~~~~~~~~

PEtab v2 has no ``parameterScale``. The parameters in the parameter table
are the estimated parameters; bounds, nominal values and priors all refer
to them. :ref:`Priors <v2_prior_distributions>` are densities over the
parameter as it appears in the table, and the
:ref:`objective function <v2_objective_function>` is fully defined.
How a tool optimizes or samples internally is not part of the problem.

Estimating a parameter on ``log10`` scale is still possible, by making the
log-transformed value the parameter: a new parameter ``log10_k`` is
estimated, and the model computes ``k = 10^log10_k``.
This is what the :ref:`specification <v2_changes>` refers to with
"the model parameters can be transformed in the model file".

Consequences for a conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Parameters without a prior.** The likelihood does not depend on how a
parameter is parametrized. Keeping :math:`x` as the estimated parameter
changes nothing numerically. What changes is the meaning of the gradient
(now with respect to :math:`x` instead of :math:`\tilde{x}`), and that
optimization scale and start point sampling become tool settings.
Reparametrizing to :math:`\tilde{x}` keeps all of these as they were.
The v1 default prior (flat in :math:`\tilde{x}`) is then also kept,
see :ref:`v2_migration_default_prior`.

**Parameters with a** ``parameterScale*`` **prior.** The v1 prior is a
density over :math:`\tilde{x}`. A v2 prior is a density over the estimated
parameter. If :math:`x` stays the estimated parameter, no v2 prior preserves
both the prior distribution and the optimum. The following table compares
the possible v2 encodings for the example of a ``parameterScaleNormal``
prior with parameters ``mu;sigma`` on a ``log10``-scaled parameter:

.. list-table::
   :header-rows: 1
   :widths: 30 25 25 20

   * - v2 encoding of ``parameterScaleNormal(mu, sigma)`` on ``log10`` scale
     - Prior distribution
     - Optimum and objective
     - Gradient with respect to
   * - ``log-normal(mu*ln10, sigma*ln10)`` on :math:`x`
     - Preserved
     - The objective differs by :math:`\ln(x \ln 10)`; the maximum a
       posteriori (MAP) estimate of :math:`\log_{10} x` moves by up to
       :math:`-\sigma^2 \ln 10`
     - :math:`x` instead of :math:`\tilde{x}`
   * - ``log-normal`` on :math:`x` with a shifted mean,
       ``(mu + sigma^2*ln10)*ln10``
     - Changed; the prior no longer states the intended belief
     - Objective preserved up to a constant
     - :math:`x` instead of :math:`\tilde{x}`
   * - ``normal(mu, sigma)`` on the new parameter :math:`\tilde{x}`
       (reparametrization)
     - Preserved
     - Preserved, up to the constant from
       :ref:`truncation <v2_migration_truncation>`
     - :math:`\tilde{x}`, as in v1

If :math:`x` stays the estimated parameter, the objective gains
:math:`\ln(x \ln 10)`, linear in :math:`\tilde{x}` with slope :math:`\ln 10`,
which pushes the fit towards smaller :math:`\tilde{x}`. The prior mode in
:math:`\tilde{x}` moves from :math:`\mu` to :math:`\mu - \sigma^2 \ln 10`,
and the MAP estimate by the same amount where the data do not constrain the
parameter, less where they do: by 0.09 orders of magnitude for
:math:`\sigma = 0.2`, but by 20.7 for :math:`\sigma = 3`, which usually puts
the fit at the lower bound. The posterior is still the same distribution:
the probability of any parameter range, e.g., :math:`P(a < x < b)`, is
unchanged, and samples of :math:`x` are samples of :math:`\tilde{x}` after
taking :math:`\log_{10}`. Sampling results therefore agree. Only the density
values differ, by the factor :math:`x \ln 10`, and with them the location of
the maximum, so MAP estimates and profiles move.

**Parameters with a linear-scale prior** (``normal``, ``laplace``,
``logNormal``, ``logLaplace``, ``uniform``). Under the pyPESTO reading, the
prior is a density over :math:`x`. The corresponding v2 prior on :math:`x`
gives the same objective. These parameters are therefore *not*
reparametrized. For ``uniform``, ``normal`` and ``laplace``, this is the
only option: PEtab v2 has no distribution for the logarithm of a uniform,
normal or Laplace variable, so these priors cannot be expressed over
:math:`\tilde{x}`. (``logNormal`` and ``logLaplace`` could become
``normal`` and ``laplace`` on :math:`\tilde{x}`, which keeps the
distribution but moves the optimum, by the same argument as above.)

**Recommendation.** Estimate the variable over which the v1 prior was a
density: :math:`\tilde{x}` for ``parameterScale*`` priors, :math:`x` for
linear-scale priors. Parameters without a prior can be handled either way.
Reparametrizing them to :math:`\tilde{x}` keeps gradients with respect to
:math:`\tilde{x}`, start point sampling and default prior as in v1, and is
recommended for a faithful conversion. This corresponds to ``reparametrize="all"`` in
:ref:`petab1to2 <v2_migration_petab1to2>`.

.. _v2_migration_reparametrization:

Reparametrizing a parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following describes how to replace a ``log10``-scaled parameter ``k`` by
``log10_k``, with ``k = 10^log10_k``. For ``log`` scale, use ``log_k`` and
``exp(log_k)``.

**Parameter table.** Replace the row for ``k`` by a row for ``log10_k`` with
the log-transformed bounds and nominal value. For example:

.. list-table::
   :header-rows: 1
   :widths: 8 22 14 14 16 10 16

   * -
     - ``parameterId``
     - ``lowerBound``
     - ``upperBound``
     - ``nominalValue``
     - ``estimate``
     - ``parameterScale``
   * - v1
     - ``k_phos``
     - ``1e-5``
     - ``1e3``
     - ``100``
     - ``1``
     - ``log10``
   * - v2
     - ``log10_k_phos``
     - ``-5``
     - ``3``
     - ``2``
     - ``true``
     - (removed)

The prior, if any, becomes a prior on ``log10_k``:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - v1 prior on ``k`` (``log10`` scale)
     - v2 prior on ``log10_k``
   * - ``parameterScaleNormal`` ``mu;sigma``
     - ``normal`` ``mu;sigma``
   * - ``parameterScaleLaplace`` ``mu;sigma``
     - ``laplace`` ``mu;sigma``
   * - ``parameterScaleUniform`` ``a;b``
     - ``uniform`` ``a;b``
   * - none (v1 default)
     - none, or ``uniform`` ``log10(lb);log10(ub)``
       (see :ref:`v2_migration_default_prior`)

Only ``parameterScale*`` priors convert this way. A v1 ``uniform``,
``normal`` or ``laplace`` prior on a log-scaled parameter has no
counterpart on ``log10_k``, since PEtab v2 has no distribution for the
logarithm of such a variable. These parameters, and those with
``logNormal`` or ``logLaplace`` priors, stay on linear scale
(see :ref:`v2_migration_v1_tools`).

PEtab v1 allowed a lower bound of ``0`` for log-scaled parameters with an
initialization prior. The lower bound of ``log10_k`` is then ``-inf``,
which is valid since :ref:`erratum E1 <v2_errata_e1>`. If any estimated
parameter has a prior, ``log10_k`` needs an explicit proper prior, since
the default ``uniform(-inf, ub)`` would be improper. For a parameter
without a ``parameterScale*`` prior, this means either choosing a prior,
which changes the problem, or leaving the parameter on linear scale.

**Model.** If ``k`` is a model parameter, add a constant parameter
``log10_k`` to the model and define ``k`` by an SBML *initial assignment*
``k = 10^log10_k``, replacing any existing initial assignment for ``k``.
``k`` stays a constant parameter and can still be used as a condition
target. For the example above:

.. code-block:: xml

   <parameter id="log10_k_phos" value="2" constant="true"/>
   <parameter id="k_phos" value="100" constant="true"/>
   <initialAssignment symbol="k_phos">
     <math xmlns="http://www.w3.org/1998/Math/MathML">
       <apply><power/><cn>10</cn><ci>log10_k_phos</ci></apply>
     </math>
   </initialAssignment>

Alternatives:

* An *assignment rule* ``k = 10^log10_k`` also works, but makes ``k`` a
  non-constant entity. It can then no longer be the target of a condition or
  of an event assignment, and must not appear in the parameter table.
  Its only advantage is robustness in tools that don't re-evaluate initial
  assignments after parameter changes.
* Substituting ``10^log10_k`` for ``k`` in all model expressions and removing
  ``k`` changes every kinetic law in which ``k`` occurs and loses its
  annotations.
* Defining ``k`` in the condition table for every experiment spreads the
  model definition over the experiments.

**Observable and noise formulas, condition table.** Replace ``k`` by
``10^log10_k`` in ``observableFormula``, ``noiseFormula`` and ``targetValue``
expressions. This is required if ``k`` is not a model parameter, and
otherwise harmless, as the model already defines ``k``.

**Measurement table overrides.** Values in ``observableParameters`` and
``noiseParameters`` cannot be expressions, so ``10^log10_k`` cannot be
substituted there. Instead, transform the placeholder: replace the
placeholder ``ph`` by ``10^ph`` in the observable or noise formula, and
log-transform all overrides of that placeholder: ``k`` becomes ``log10_k``,
and a number ``c`` becomes ``log10(c)``. For example, an estimated noise
parameter ``sd`` on ``log10`` scale:

.. list-table::
   :header-rows: 1
   :widths: 10 45 45

   * -
     - v1
     - v2
   * - Observable table
     - ``noiseFormula``: ``noiseParameter1_obs``
     - ``noiseFormula``: ``10^noiseParameter1_obs``;
       ``noisePlaceholders``: ``noiseParameter1_obs``
   * - Measurement table
     - ``noiseParameters``: ``sd``
     - ``noiseParameters``: ``log10_sd``
   * - Parameter table
     - ``sd``, bounds ``1e-5`` to ``1e5``
     - ``log10_sd``, bounds ``-5`` to ``5``

This requires that *all* overrides of that placeholder can be
log-transformed: reparametrized parameters or positive numbers. If the same
placeholder also receives non-positive numbers, or parameters that are not
reparametrized, split the observable into copies, such that each copy's
placeholder only receives overrides that can be log-transformed, or none at
all. Alternatively, leave the affected parameters on linear scale; this is
only an option for parameters without a ``parameterScale*`` prior.

.. _v2_migration_petab1to2:

With libpetab-python
~~~~~~~~~~~~~~~~~~~~

``petab1to2`` applies the above through its ``reparametrize`` argument:

* ``"none"`` (default): no reparametrization. All parameters are estimated
  on linear scale. ``parameterScaleNormal`` and ``parameterScaleLaplace``
  priors on log-scaled parameters are converted to ``log-normal`` and
  ``log-laplace`` priors on :math:`x`, which preserves the distribution but
  moves the optimum, as described above. The v1 default prior becomes
  ``uniform`` within the bounds. This is appropriate for problems without
  priors, if gradients with respect to :math:`x` instead of
  :math:`\tilde{x}` and estimation on linear scale are acceptable.
* ``"priors"``: reparametrizes the estimated log-scaled parameters with
  ``parameterScale*`` priors, and any log-scaled parameters that share a
  measurement table placeholder with them.
* ``"all"``: reparametrizes all estimated log-scaled parameters, except those
  with linear-scale priors. Recommended for a faithful conversion.

A lower bound of ``0`` becomes ``-inf``. If the parameter would then have
an improper default prior, it is left on linear scale, with a warning.
The same applies to parameters without a ``parameterScale*`` prior
whose placeholder cannot be log-transformed. If a parameter *with* such a
prior shares a placeholder with overrides that cannot be log-transformed,
the conversion fails, and the affected observable needs to be split by hand
first, as described above. Non-estimated log-scaled parameters are only
reparametrized if they share a placeholder with reparametrized ones.

The underlying function ``petab.v2.reparametrize_log`` can also be applied to
an existing v2 problem. It returns a reparametrized copy and the mapping of
old to new parameter IDs:

.. code-block:: python

   import petab.v2

   problem = petab.v2.Problem.from_yaml("v2/problem.yaml")
   problem_log, id_map = petab.v2.reparametrize_log(
       problem, ["k_phos", "sd_pSTAT5A_rel"], base=10
   )
   problem_log.to_files("v2_log/")

Other changes affecting the objective function
----------------------------------------------

.. _v2_migration_log10_observables:

``log10``-transformed observables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PEtab v2 has no ``log10`` noise distributions. The v1 ``log10``-normal
distribution of :math:`m` with noise parameter :math:`\sigma` is the v2
``log-normal`` distribution with noise parameter :math:`\sigma \ln 10`,
with identical density, since :math:`\ln m = \ln 10 \cdot \log_{10} m`.
The same holds for ``log10``-Laplace and ``log-laplace``.

To keep estimated noise parameters and noise overrides in the measurement
table unchanged, put the factor into the noise formula:
``noiseFormula`` ``sigma`` becomes ``ln(10) * (sigma)``. ``petab1to2`` does
this and warns about it. Parameters in such noise formulas keep their v1
meaning: they refer to the ``log10``-transformed observable.

.. _v2_migration_init_priors:

Initialization priors
~~~~~~~~~~~~~~~~~~~~~

``initializationPriorType`` and ``initializationPriorParameters`` are
removed. How start points are sampled is a tool setting. The v1 default,
uniform on parameter scale within the bounds, is reproduced by sampling the
reparametrized parameters uniformly within their (log-transformed) bounds.
Non-default initialization priors have no v2 counterpart and must be
configured in the tool.

.. _v2_migration_truncation:

Bounds truncate priors
~~~~~~~~~~~~~~~~~~~~~~

In PEtab v2, a prior with support beyond the parameter bounds is
:ref:`truncated and renormalized <v2_prior_distributions>`. This adds the
constant :math:`-\ln Z` to the objective, with
:math:`Z = \text{CDF}(\text{upperBound}) - \text{CDF}(\text{lowerBound})`
of the non-truncated prior. PEtab v1 did not specify this, and tools did
not necessarily renormalize. The optimum is unaffected. For priors that are
narrow compared to the bounds, :math:`Z \approx 1`; for wide priors, the
constant can be of order 1 per prior. A prior is not truncated if the bounds
cover its domain, e.g., ``-inf`` and ``inf`` for ``normal``
(:ref:`erratum E1 <v2_errata_e1>`).

.. _v2_migration_default_prior:

Default prior
~~~~~~~~~~~~~

In PEtab v2, if any estimated parameter has a prior, the other estimated
parameters default to ``uniform`` within their bounds, which contributes
:math:`\ln(\text{upperBound} - \text{lowerBound})` per parameter.
Parameters with an infinite bound must then have an explicit proper prior
(:ref:`erratum E1 <v2_errata_e1>`). Priors of non-estimated parameters are
ignored (:ref:`erratum E2 <v2_errata_e2>`). The v1
default ``parameterScaleUniform`` contributed nothing. The constant does not
affect the optimum, but it does depend on the bounds, which matters when
objective values are compared between models with different bounds or
different numbers of parameters.

As a prior distribution, the v2 default is uniform in the *estimated*
parameter. For a parameter that was ``log10``-scaled in v1 and is not
reparametrized, with bounds such as ``1e-5`` to ``1e3``, this puts most of
the probability mass in the top decade, while the v1 default was uniform in
:math:`\log_{10} x`. For reparametrized parameters, the v2 default is
uniform in ``log10_k``, as in v1. This matters for Bayesian inference, not
for optimization.

Summary of objective constants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After a conversion with ``reparametrize="all"``, the v2 objective differs
from the v1 objective in the D2D/pyPESTO reading only by additive constants:

* :math:`-\ln Z_i` for every truncated prior :math:`i`;
* :math:`\ln(\text{ub}_j - \text{lb}_j)` for every estimated parameter
  :math:`j` without an explicit prior, if any estimated parameter has a
  prior;
* the normalization constants of the priors and noise distributions that a
  v1 tool may or may not have included.

Without reparametrization, the objective additionally differs by the
non-constant Jacobian term for every log-scaled parameter with a
``parameterScale*`` prior, :math:`\ln(x \ln 10)` for ``log10`` scale.

.. _v2_migration_verification:

Verifying a conversion
----------------------

A converted problem should be checked against the original with the tools
that were used with the v1 problem:

1. Validate both problems (``petablint``).
2. Simulate both at the nominal parameters. The simulated values for all
   measurements must agree to solver tolerance.
3. Compare the negative log-likelihood. It must agree to solver tolerance;
   there is no constant from the conversion.
4. Compare the log-prior, evaluated for v1 as a density over
   :math:`\tilde{\theta}`. The difference must be the constant from the
   truncation and default priors above.
5. Compare the gradient. For reparametrized parameters, the v1 gradient
   with respect to :math:`\tilde{x}` equals the v2 gradient with respect to
   ``log10_k``. For parameters that were ``log10``-scaled in v1 and are not
   reparametrized, the v1 gradient equals the v2 gradient with respect to
   :math:`x` times :math:`x \ln 10`. For v1 ``lin`` parameters, the
   gradients agree directly.
6. Repeat steps 2 to 5 at a second parameter vector, e.g., moved some way
   towards the center of the bounds, so that the gradient is not zero and
   the comparison is not specific to the optimum.

For an example, see ``Schwen_PONE2014`` in the benchmark collection, a
problem with ``parameterScaleNormal`` priors and ``log10``-transformed
observables: the
`v1 <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/tree/8823e6d803c137b7ca1f0588701d124ca8d21387/problems/Schwen_PONE2014/v1>`__
and
`v2 <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/tree/8823e6d803c137b7ca1f0588701d124ca8d21387/problems/Schwen_PONE2014/v2>`__
encodings, and the comparison of both in
`Benchmark-Models-PEtab#336 <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/pull/336>`__.
