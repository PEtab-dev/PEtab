import libsbml
import sys
import os

sys.path.append(os.getcwd())
import petab  # noqa: E402


def test_assignment_rules_to_dict():
    # Create Sbml model with one parameter and one assignment rule
    document = libsbml.SBMLDocument(3, 1)
    model = document.createModel()
    petab.sbml.add_model_output(sbml_model=model,
                                observable_id='1',
                                observable_name='Observable 1',
                                formula='a+b')

    expected = {
        'observable_1': {
            'name': 'Observable 1',
            'formula': 'a + b'
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
