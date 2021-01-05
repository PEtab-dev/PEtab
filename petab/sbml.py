"""Functions for interacting with SBML models"""
from warnings import warn
import logging
from pandas.io.common import get_handle, is_url, is_file_like
import re
from typing import Dict, Any, List, Union, Tuple
import libsbml

logger = logging.getLogger(__name__)


def assignment_rules_to_dict(
        sbml_model: libsbml.Model, filter_function=lambda *_: True,
        remove: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Turn assignment rules into dictionary.

    Parameters:
        sbml_model:
            a sbml model instance.
        filter_function:
            callback function taking assignment variable as input
            and returning True/False to indicate if the respective rule should
            be turned into an observable.
        remove:
            Remove the all matching assignment rules from the model

    Returns:
        ::

            {
                assigneeId:
                {
                    'name': assigneeName,
                    'formula': formulaString
                }
            }

    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

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


def is_sbml_consistent(sbml_document: libsbml.SBMLDocument,
                       check_units: bool = False) -> bool:
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

    warn("This function will be removed in future releases.",
         DeprecationWarning)

    for reaction in sbml_model.getListOfReactions():
        law = reaction.getKineticLaw()
        # copy first so we can delete in the following loop
        local_parameters = list(local_parameter for local_parameter
                                in law.getListOfParameters())
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
    """Add new global parameter to SBML model

    Arguments:
        sbml_model: SBML model
        parameter_id: ID of the new parameter
        parameter_name: Name of the new parameter
        constant: Is parameter constant?
        units: SBML unit ID
        value: parameter value

    Returns:
        The created parameter
    """

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

    Returns:
        The created ``AssignmentRule``
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

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
                     observable_name: str = None) -> None:
    """Add PEtab-style output to model

    We expect that all formula parameters are added to the model elsewhere.

    Arguments:
        sbml_model: Model to add output to
        formula: Formula string for model output
        observable_id: ID without "observable\\_" prefix
        observable_name: Any observable name
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    if observable_name is None:
        observable_name = observable_id

    prefixed_id = f'observable_{observable_id}'
    add_global_parameter(sbml_model, prefixed_id, observable_name)
    create_assigment_rule(sbml_model=sbml_model,
                          assignee_id=prefixed_id,
                          formula=formula)


def add_model_output_sigma(sbml_model: libsbml.Model,
                           observable_id: str,
                           formula: str) -> None:
    """Add PEtab-style sigma for the given observable id

    We expect that all formula parameters are added to the model elsewhere.

    Arguments:
        sbml_model: Model to add to
        observable_id: Observable id for which to add sigma
        formula: Formula for sigma
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    add_global_parameter(sbml_model, f'sigma_{observable_id}')
    create_assigment_rule(sbml_model, f'sigma_{observable_id}', formula)


def add_model_output_with_sigma(
        sbml_model: libsbml.Model,
        observable_id: str,
        observable_formula: str,
        observable_name: str = None) -> None:
    """Add PEtab-style output and corresponding sigma with single
    (newly created) parameter

    We expect that all formula parameters are added to the model elsewhere.

    Arguments:
        sbml_model:
            Model to add output to
        observable_formula:
            Formula string for model output
        observable_id:
            ID without "observable\\_" prefix
        observable_name:
            Any name
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

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


def sbml_parameter_is_observable(sbml_parameter: libsbml.Parameter) -> bool:
    """
    Returns whether the ``libsbml.Parameter`` ``sbml_parameter``
    matches the defined observable format.
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    return sbml_parameter.getId().startswith('observable_')


def sbml_parameter_is_sigma(sbml_parameter: libsbml.Parameter) -> bool:
    """
    Returns whether the ``libsbml.Parameter`` ``sbml_parameter``
    matches the defined sigma format.
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    return sbml_parameter.getId().startswith('sigma_')


def get_observables(sbml_model: libsbml.Model, remove: bool = False) -> dict:
    """
    Get observables defined in SBML model according to PEtab format.

    Returns:
        Dictionary of observable definitions.
        See `assignment_rules_to_dict` for details.
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    observables = assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_observable,
        remove=remove
    )
    return observables


def get_sigmas(sbml_model: libsbml.Model, remove: bool = False) -> dict:
    """
    Get sigmas defined in SBML model according to PEtab format.

    Returns:
        Dictionary of sigma definitions.

        Keys are observable IDs, for values see `assignment_rules_to_dict` for
        details.
    """
    warn("This function will be removed in future releases.",
         DeprecationWarning)

    sigmas = assignment_rules_to_dict(
        sbml_model,
        filter_function=sbml_parameter_is_sigma,
        remove=remove
    )
    # set correct observable name
    sigmas = {re.sub('^sigma_', 'observable_', key): value['formula']
              for key, value in sigmas.items()}
    return sigmas


def get_model_parameters(sbml_model: libsbml.Model, with_values=False
                         ) -> Union[List[str], Dict[str, float]]:
    """Return SBML model parameters which are not AssignmentRule
    targets for observables or sigmas

    Arguments:
        sbml_model: SBML model
        with_values: If false, returns list of SBML model parameter IDs which
        are not AssignmentRule targets for observables or sigmas. If true,
        returns a dictionary with those parameter IDs as keys and parameter
        values from the SBML model as values.
    """
    if not with_values:
        return [p.getId() for p in sbml_model.getListOfParameters()
                if sbml_model.getAssignmentRuleByVariable(p.getId()) is None]

    return {p.getId(): p.getValue()
            for p in sbml_model.getListOfParameters()
            if sbml_model.getAssignmentRuleByVariable(p.getId()) is None}


def write_sbml(sbml_doc: libsbml.SBMLDocument, filename: str) -> None:
    """Write PEtab visualization table

    Arguments:
        sbml_doc: SBML document containing the SBML model
        filename: Destination file name
    """
    sbml_writer = libsbml.SBMLWriter()
    ret = sbml_writer.writeSBMLToFile(sbml_doc, filename)
    if not ret:
        raise RuntimeError(f"libSBML reported error {ret} when trying to "
                           f"create SBML file {filename}.")


def get_sbml_model(
        filepath_or_buffer
) -> Tuple[libsbml.SBMLReader, libsbml.SBMLDocument, libsbml.Model]:
    """Get an SBML model from file or URL or file handle

    :param filepath_or_buffer:
        File or URL or file handle to read the model from
    :return: The SBML document, model and reader
    """
    if is_file_like(filepath_or_buffer) or is_url(filepath_or_buffer):
        handle = get_handle(filepath_or_buffer, mode='r').handle
        # URL or already opened file, we will load the model from a string
        return load_sbml_from_string(''.join(handle))

    return load_sbml_from_file(filepath_or_buffer)


def load_sbml_from_string(
        sbml_string: str
) -> Tuple[libsbml.SBMLReader, libsbml.SBMLDocument, libsbml.Model]:
    """Load SBML model from string

    :param sbml_string: Model as XML string
    :return: The SBML document, model and reader
    """

    sbml_reader = libsbml.SBMLReader()
    sbml_document = \
        sbml_reader.readSBMLFromString(sbml_string)
    sbml_model = sbml_document.getModel()

    return sbml_reader, sbml_document, sbml_model


def load_sbml_from_file(
        sbml_file: str
) -> Tuple[libsbml.SBMLReader, libsbml.SBMLDocument, libsbml.Model]:
    """Load SBML model from file

    :param sbml_file: Filename of the SBML file
    :return: The SBML document, model and reader
    """

    sbml_reader = libsbml.SBMLReader()
    sbml_document = sbml_reader.readSBML(sbml_file)
    sbml_model = sbml_document.getModel()

    return sbml_reader, sbml_document, sbml_model
