.. _development:

PEtab development process
=========================

Motivation for this document / general remarks
++++++++++++++++++++++++++++++++++++++++++++++

Reproducibility and reusability of the results of data-based modeling
studies are essential. Yet, until recently, there was no broadly supported
format for the specification of parameter estimation problems in systems
biology. Therefore, we developed PEtab. Having released the specifications
for PEtab version 1.0, we would like to keep development of PEtab active by
attracting more users and tool developers. We acknowledge that it is
important for any potential contributors to know how PEtab is managed and
developed, which we will explain in the remainder of this document.

Values
++++++

We are committed to diversity, open communication, transparent processes,
democratic decision-making by the community and fostering a welcoming
environment. While we want to have clear processes, we don’t want to
overformalize things to avoid unnecessary slowdowns.

Roles within the PEtab community
++++++++++++++++++++++++++++++++

The following subsections describe the different roles in the development of
PEtab.

Anybody interested in PEtab
---------------------------

Input from every interested person is welcome.

Anyone may...

* propose changes to PEtab

PEtab forum
-----------

The PEtab forum includes anybody who is interested in PEtab and is
subscribed to the `PEtab mailing list <https://groups.google.com/g/petab-discuss>`_
using their real name. (Although anybody is invited to subscribe to the
mailing list with any name or email address, we require the use of real
names for participation in any votes. This is to ensure that every person
has only one vote.)

The PEtab forum ...

* votes for changes to PEtab
* nominates editors
* elects editors

PEtab editors
-------------

PEtab is meant to be a community effort. Decisions should therefore be made
as far as possible by a broad community interested in the use and
development of PEtab. Nevertheless, such a project cannot run fully
autonomously, but requires a core team of editors to take care of certain
management tasks. The PEtab editorial board is a team of 5 representatives
nominated and elected by the PEtab forum.

The duties / privileges of the editors include the following:

* organizing polls
* writing/updating specifications
* organizing and announcing annual meetings / hackathons
* promoting PEtab
* deciding minor PEtab issues among themselves
  ("minor" as defined by the editors but reasons for the decision need to be communicated)
* managing the PEtab mailing lists
* managing the PEtab GitHub organization and respective repositories
* delegating any of the above

Other
-----

Other roles may be created as required based on the decision of the editors by majority vote.

Communication channels
++++++++++++++++++++++

The main discussion channel should be the GitHub
`issues <https://github.com/PEtab-dev/PEtab/issues>`_ /
`discussion <https://github.com/PEtab-dev/PEtab/discussions>`_ pages.
Additionally, the `mailing list <https://groups.google.com/g/petab-discuss>`_
is used for the announcement of new releases, polls, and the likes and can be
used for discussions that seem unfit for GitHub. An archive of the mailing list
shall be publicly accessible.
The PEtab Editors can be contacted through
`https://groups.google.com/g/petab-editors <https://groups.google.com/g/petab-editors>`_,
which is only readable by the current Editors.
Regular, ideally non-virtual, PEtab hackathons are planned to happen at least
annually, e.g., in combination with
`COMBINE events <https://co.mbine.org/events/>`_.

Election of Editors
+++++++++++++++++++

Editors are elected for 3 years by the PEtab forum. Editors may serve
multiple terms, but there needs to be a break of 1 year between subsequent
terms. To maintain continuity, not all editors shall be replaced at the same
time. Editors may resign any time before the end of their term.

Whenever an Editor position becomes vacant:

* Editors announce upcoming elections and request nominations via the PEtab
  mailing list. The time given for nominations shall be no shorter than 10 days.
* Interested parties submit nominations including a short statement on the
  reason for nomination before the deadline. Self-nominations are allowed.
* Editors ask the nominees whether they accept the nomination (nominees are
  given 5 days to accept). This step may start already during the nomination
  phase.
* Editors announce the nominees who accepted their nomination along with the
  submitted statements and open the poll via the PEtab mailing list. The
  editors choose a sensible medium and deadline for the poll.
* The PEtab forum casts their votes secretly. (Votes may have to be open to the
  editors, as they need to verify that only qualified votes are counted.
  However, the editors are required to maintain confidentiality.) Every
  participant has 1 vote per vacant position.
* After passing the deadline, the editors count the votes and ask the
  editor-elect to accept or decline the election. No acceptance before the end
  of the deadline set by the editors, which shall not be less than 3 days, is
  considered decline.
* If an editor-elect declines, the position will be offered to the next
  candidate according to the number of votes. (If there is no candidate left
  with at least one vote, the election for the vacant position needs to be
  repeated.
* If there is a tie between candidates of which only a subset can become an
  editor, run-off elections including only those candidates have to be
  organized by the PEtab editors as soon as possible. Voters will again have a
  number of votes equal to the number of vacant positions.
* If the editor-elect accepts, the other editors announce the new editor on the
  PEtab mailing list. The editors shall furthermore announce the number of
  votes each nominee, elected or not, has received.

Special procedure for the first election (February, 2021):
----------------------------------------------------------

The first election was held among the authors of the original PEtab
publication. Nominees were not required to be among the authors. The election
was managed by two persons who were not among the candidates and were
coming from two different labs. To avoid a simultaneous replacement of all
of the editors elected during the first election, the first election was
subject to the following special rules: 2 persons were elected for 3
years, 2 persons for 2 years and one person for 1 year. The persons with
more votes were elected for a longer period (if they accepted
for the longer period). In case of an equal number of votes among any of the
top 5 candidates, there would have been run-off elections between those
candidates with equal numbers of votes. The editors-elect were given 3 working
days to accept the election.
If an editor would decide to hand over his editorial role before the end of
their term, an editor elected for a shorter term period could decide to take
over and extend their term to the end of the leaving editor's original term.

PEtab format development process
++++++++++++++++++++++++++++++++

We acknowledge that PEtab cannot accommodate everybody’s needs, but we are
committed to addressing current and future requirements in upcoming versions of
the PEtab format. Although we value backwards-compatibility, we don’t want to
exclude breaking changes if justified by the benefits.

Anybody is welcomed to propose changes or additions to PEtab. Any proposals
shall be made using GitHub issues. Benefits, problems, and potential
alternatives shall be discussed in the respective thread.

A proposal is considered accepted for inclusion in the next version of PEtab
if it’s endorsed by the majority of the PEtab editors and if distinct
developers of at least 2 tools provide a prototype implementation. For any
changes, respective test cases sufficiently covering the changes are to be
added to the `PEtab test suite <https://github.com/PEtab-dev/petab_test_suite>`_
prior to release.

Requirements for new releases:

* Updated format specifications
* Updated converter
* Updated validator
* Updated test suite
* Updated changelog

The PEtab editors jointly decide whether these requirements are met.

Upon a new release, the PEtab editors ensure that

* a new release is created in the GitHub repository
* the new version of the specifications is deposited at Zenodo
* the new release is announced on the PEtab mailing list

PEtab Extensions
----------------

An elaborate, monolithic format would make it difficult to understand and
implement support for PEtab, leading to a steep learning curve and discouraging
support in new toolboxes. To address this issue, the PEtab format is modular and
permits modifications through extensions that complement the core standard.
This modular specification evens the learning curve and provides toolbox
developers with more guidance on which features to implement to maximize
support for real world applications. Moreover, such modular extensions
facilitate and promote the use of specialized tools for specific, non-parameter
estimation tasks such as visualization.

Requirements for new extensions:

* Specifications in PEtab extensions take precedence over PEtab core, i.e., they
can ease or refine format restrictions imposed by PEtab core.
* PEtab extensions should extend PEtab core with new orthogonal features or
tasks, i.e., they should not make trivial changes to PEtab core.
* PEtab extensions must be named according to ^[a-zA-Z_-]\w*$
* PEtab extensions must be versioned using semantic versioning.
* PEtab extensions required for interpretation of a problem specification must
be specified in the PEtab-YAML files
* There is at least one tool that supports the proposed extension
* The authors provide a library that implements validation checks for the
proposed format.

Developers are free to develop any PEtab extension. To become an official
PEtab extension, it needs to go through the following process.

1. The developers write a proposal describing the motivation and specification
of the extension, following the respective issue template provided in this
repository.
1. The proposal is submitted as an issue in this repository.
1. The technical specification and documentation of the extension is submitted
as a pull request in this repository that references the respective issue.
1. The developers submit a pull request that adds test cases to validate support
for the extension in the https://github.com/PEtab-dev/petab_test_suite
repository. The external pull request must also reference the issue containing
the proposal.

The PEtab editors jointly decide whether an extension meets the requirements
described here. In case of a positive evaluation, they announce a poll for the
acceptance as official extension to the PEtab forum. All members of the PEtab
community are eligible to vote. If at least 50% of the votes are in favor,
the extension is accepted and the respective pull requests with specifications,
documentation and test cases are merged.

It is encouraged that extensions are informally discussed with the community
before initiating the process of becoming an official extension. Such
discussions can be conducted through the communication channels mentioned
above.

Versioning of the PEtab format
------------------------------

The PEtab specifications follow `semantic versioning <https://semver.org/>`_.
Any changes to the PEtab specifications require a new release. Any necessary
clarifications or corrections shall be collected on an Errata page until a new
version is released.

The time for a new PEtab release is left to the discretion of the editors.
However, accepted changes should be released within 2 months after acceptance.

With any new PEtab version it shall be ensured that a converter between the new
and the previous version(s) is available. Parallel maintenance of multiple
versions is not intended.

Generally, any parameter estimation problem that could have been specified
in an earlier version should be specifiable in a new version (potentially
requiring different syntax). Any changes to the PEtab specifications that
would remove certain features without adequate replacement require the
support of at least 4 out of the 5 editors.

Changes to these processes
++++++++++++++++++++++++++

Changes to the processes specified above require a public vote with
agreement of the majority of voters. Any other changes not directly
affecting those processes, such as changes to structure, orthography,
grammar, formatting, the preamble can be made by the editors any time.