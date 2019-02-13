import libsbml
import sys
import os

sys.path.append(os.getcwd())
import petab  # noqa: E402


def test_constant_species_to_parameters():
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    model.setTimeUnits("second")
    model.setExtentUnits("mole")
    model.setSubstanceUnits('mole')

    s = model.createSpecies()
    s.setId('x1')
    s.setConstant(True)
    s.setInitialConcentration(1.0)

    petab.constant_species_to_parameters(model)

    assert len(list(model.getListOfParameters())) == 1
    assert len(list(model.getListOfSpecies())) == 0


def test_assignment_rules_to_dict():
    # Create Sbml model with one parameter and one assignment rule
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    p = model.createParameter()
    p.setId('observable_1')
    p.setName('Observable 1')
    rule = model.createAssignmentRule()
    rule.setId('assignmentRuleIdDoesntMatter')
    rule.setVariable('observable_1')
    rule.setFormula('a+b')

    expected = {
        'observable_1': {
            'name': 'Observable 1',
            'formula': 'a+b'
        }
    }

    actual = petab.assignment_rules_to_dict(model, remove=False)
    assert actual == expected
    assert model.getAssignmentRuleByVariable('observable_1') is not None
    assert len(model.getListOfParameters()) == 1

    actual = petab.assignment_rules_to_dict(model, remove=True)
    assert actual == expected
    assert model.getAssignmentRuleByVariable('observable_1') is None
    assert len(model.getListOfParameters()) == 0
