"""Functions for direct access of SBML models"""
import libsbml
import math


def assignment_rules_to_dict(
        sbml_model, filter_function=lambda *_: True, remove=False):
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
                'formula': rule.getFormula()
            }

    # remove from model?
    if remove:
        for parameter_id in result:
            sbml_model.removeRuleByVariable(parameter_id)
            sbml_model.removeParameter(parameter_id)

    return result


def constant_species_to_parameters(sbml_model):
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
            print(f"Ignoring {species.getId()} which has only substance units."
                  " Conversion not yet implemented.")
            continue
        if math.isnan(species.getInitialConcentration()):
            print(f"Ignoring {species.getId()} which has no initial "
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

    return transformables
