"""Functions for direct access of SBML models"""

import libsbml
import math
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def assignment_rules_to_dict(
        sbml_model: libsbml.Model, filter_function=lambda *_: True,
        remove: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Turn assignment rules into dictionary.

    Parameters
    ----------

    sbml_model:
        an sbml model instance.
    filter_function:
        callback function taking assignment variable as input
        and returning True/False to indicate if the respective rule should be
        turned into an observable.
    remove:
        Remove the all matching assignment rules from the model

    Returns
    -------

    A dictionary(assigneeId:{
        'name': assigneeName,
        'formula': formulaString
    })
    """
    result = {}

    # iterate over rules
    for rule in sbml_model.getListOfRules():
        if rule.getTypeCode() != libsbml.SBML_ASSIGNMENT_RULE:
            continue
        assignee = rule.getVariable()
        parameter = sbml_model.getParameter(assignee)
        # filter
        if parameter and filter_function(parameter):
            result[assignee] = {
                'name': parameter.getName(),
                'formula': libsbml.formulaToL3String(rule.getMath())
            }

    # remove from model?
    if remove:
        for parameter_id in result:
            sbml_model.removeRuleByVariable(parameter_id)
            sbml_model.removeParameter(parameter_id)

    return result


def constant_species_to_parameters(sbml_model: libsbml.Model) -> list:
    """Convert constant species in the SBML model to constant parameters.

    This can be used e.g. for setting up models with condition-specific
    constant species for PEtab, since there it is not possible to specify
    constant species in the condition table.

    Arguments:
        sbml_model: libsbml model instance

    Returns:
        species IDs that have been turned into constants

    Raises:

    """
    transformables = []
    for species in sbml_model.getListOfSpecies():
        if not species.getConstant() and not species.getBoundaryCondition():
            continue

        if species.getHasOnlySubstanceUnits():
            logger.warning(
                f"Ignoring {species.getId()} which has only substance units."
                " Conversion not yet implemented.")
            continue

        if math.isnan(species.getInitialConcentration()):
            logger.warning(
                f"Ignoring {species.getId()} which has no initial "
                "concentration. Amount conversion not yet implemented.")
            continue

        transformables.append(species.getId())

    # Must not remove species while iterating over getListOfSpecies()
    for speciesId in transformables:
        species = sbml_model.removeSpecies(speciesId)
        par = sbml_model.createParameter()
        par.setId(species.getId())
        par.setName(species.getName())
        par.setConstant(True)
        par.setValue(species.getInitialConcentration())
        par.setUnits(species.getUnits())

    # Remove from reactants and products
    for reaction in sbml_model.getListOfReactions():
        for speciesId in transformables:
            reaction.removeReactant(speciesId)
            reaction.removeProduct(speciesId)
            reaction.removeModifier(speciesId)

    return transformables


def is_sbml_consistent(sbml_document: libsbml.SBMLDocument,
                       check_units: bool = False):
    """Check for SBML validity / consistency

    Arguments:
        sbml_document: SBML document to check
        check_units: Also check for unit-related issues
    Returns:
        False if problems were detected, otherwise True
    """

    if not check_units:
        sbml_document.setConsistencyChecks(
            libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, False)

    has_problems = sbml_document.checkConsistency()
    if has_problems:
        log_sbml_errors(sbml_document)
        logger.warning(
            'WARNING: Generated invalid SBML model. Check messages above.')

    return not has_problems


def log_sbml_errors(sbml_document: libsbml.SBMLDocument,
                    minimum_severity=libsbml.LIBSBML_SEV_WARNING) -> None:
    """Log libsbml errors

    Arguments:
        sbml_document: SBML document to check
        minimum_severity: Minimum severity level to report (see libsbml)
    """

    for error_idx in range(sbml_document.getNumErrors()):
        error = sbml_document.getError(error_idx)
        if error.getSeverity() >= minimum_severity:
            category = error.getCategoryAsString()
            severity = error.getSeverityAsString()
            message = error.getMessage()
            if severity == libsbml.LIBSBML_SEV_INFO:
                logger.info(f'libSBML {severity} ({category}): {message}')
            elif severity == libsbml.LIBSBML_SEV_WARNING:
                logger.warning(f'libSBML {severity} ({category}): {message}')
            else:
                logger.error(f'libSBML {severity} ({category}): {message}')


def globalize_parameters(sbml_model: libsbml.Model,
                         prepend_reaction_id: bool = False) -> None:
    """Turn all local parameters into global parameters with the same
    properties

    Local parameters are currently ignored by other PEtab functions. Use this
    function to convert them to global parameters. There may exist local
    parameters with identical IDs within different kinetic laws. This is not
    checked here. If in doubt that local parameter IDs are unique, enable
    `prepend_reaction_id` to create global parameters named
    ${reaction_id}_${local_parameter_id}.

    Arguments:
        sbml_model:
            The SBML model to operate on
        prepend_reaction_id:
            Prepend reaction id of local parameter when
            creating global parameters
    """
    for reaction in sbml_model.getListOfReactions():
        law = reaction.getKineticLaw()
        # copy first so we can delete in the following loop
        local_parameters = [local_parameter for local_parameter
                            in law.getListOfParameters()]
        for lp in local_parameters:
            if prepend_reaction_id:
                parameter_id = f'{reaction.getId()}_{lp.getId()}'
            else:
                parameter_id = lp.getId()

            # Create global
            p = sbml_model.createParameter()
            p.setId(parameter_id)
            p.setName(lp.getName())
            p.setConstant(lp.getConstant())
            p.setValue(lp.getValue())
            p.setUnits(lp.getUnits())

            # removeParameter, not removeLocalParameter!
            law.removeParameter(lp.getId())


def add_global_parameter(sbml_model: libsbml.Model,
                         parameter_id: str,
                         parameter_name: str = None,
                         constant: bool = False,
                         units: str = 'dimensionless',
                         value: float = 0.0) -> libsbml.Parameter:
    """Add new global parameter to SBML model"""

    if parameter_name is None:
        parameter_name = parameter_id

    p = sbml_model.createParameter()
    p.setId(parameter_id)
    p.setName(parameter_name)
    p.setConstant(constant)
    p.setValue(value)
    p.setUnits(units)
    return p


def create_assigment_rule(sbml_model: libsbml.Model,
                          assignee_id: str,
                          formula: str,
                          rule_id: str = None,
                          rule_name: str = None) -> libsbml.AssignmentRule:
    """Create SBML AssignmentRule

    Arguments:
        sbml_model: Model to add output to
        assignee_id: Target of assignment
        formula: Formula string for model output
        rule_id: SBML id for created rule
        rule_name: SBML name for created rule
    """
    if rule_id is None:
        rule_id = assignee_id

    if rule_name is None:
        rule_name = rule_id

    rule = sbml_model.createAssignmentRule()
    rule.setId(rule_id)
    rule.setName(rule_name)
    rule.setVariable(assignee_id)
    rule.setFormula(formula)

    return rule


def add_model_output(sbml_model: libsbml.Model,
                     observable_id: str,
                     formula: str,
                     observable_name: str = None):
    """Add PEtab-style output to model

    We expect that all formula parameters are added to the model elsewhere.

    Arguments:
        sbml_model: Model to add output to
        formula: Formula string for model output
        observable_id: ID without 'observable_' prefix
        observable_name: Any observable name
    """

    if observable_name is None:
        observable_name = observable_id

    prefixed_id = f'observable_{observable_id}'
    add_global_parameter(sbml_model, prefixed_id, observable_name)
    create_assigment_rule(sbml_model=sbml_model,
                          assignee_id=prefixed_id,
                          formula=formula)


def add_model_output_sigma(sbml_model: libsbml.Model,
                           observable_id: str,
                           formula: str):
    """Add PEtab-style sigma for the given observable id

    We expect that all formula parameters are added to the model elsewhere.

    Arguments:
        sbml_model: Model to add to
        observable_id: Observable id for which to add sigma
        formula: Formula for sigma
    """
    add_global_parameter(sbml_model, f'sigma_{observable_id}')
    create_assigment_rule(sbml_model, f'sigma_{observable_id}', formula)


def add_model_output_with_sigma(
        sbml_model: libsbml.Model,
        observable_id: str,
        observable_formula: str,
        observable_name: str = None):
    """Add PEtab-style output and corresponding sigma with single
    (newly created) parameter

    We expect that all formula parameters are added to the model elsewhere.

    Arguments:
        sbml_model: Model to add output to
        observable_formula: Formula string for model output
        observable_id: ID without 'observable_' prefix
        observable_name: Any name
    """
    add_model_output(sbml_model=sbml_model,
                     observable_id=observable_id,
                     observable_name=observable_name,
                     formula=observable_formula)

    noise_parameter_id = f'noiseParameter1_{observable_id}'
    add_global_parameter(sbml_model=sbml_model,
                         parameter_id=noise_parameter_id)

    add_model_output_sigma(sbml_model=sbml_model,
                           observable_id=observable_id,
                           formula=noise_parameter_id)
