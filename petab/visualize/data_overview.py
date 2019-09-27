"""
Functions for creating an overview report of a PEtab problem
"""

import petab
import os
import pandas as pd
from shutil import copyfile


def create_report(problem: petab.Problem, model_name: str) -> None:
    """Create an HTML overview data / model overview report

    Arguments:
        problem: PEtab problem
        model_name: Name of the model, used for file name for report
    """

    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'templates')
    template_file = "report.html"

    data_per_observable = get_data_per_observable(problem.measurement_df)

    # Setup template engine
    import jinja2
    template_loader = jinja2.FileSystemLoader(
        searchpath=template_dir)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(template_file)

    # Render and save
    output_text = template.render(problem=problem, model_name=model_name,
                                  data_per_observable=data_per_observable)
    with open(model_name + '.html', 'w') as html_file:
        html_file.write(output_text)
    copyfile(os.path.join(template_dir, 'mystyle.css'), 'mystyle.css')


def get_data_per_observable(measurement_df: pd.DataFrame) -> pd.DataFrame:
    """Get table with number of data points per observable and condition

    Arguments:
        measurement_df: PEtab measurement data frame
    """

    my_measurements = measurement_df.copy()

    my_measurements.preequilibrationConditionId.fillna('', inplace=True)

    data_per_observable = pd.pivot_table(
        my_measurements, values='measurement', aggfunc='count',
        index=['simulationConditionId', 'preequilibrationConditionId'],
        columns=['observableId'], fill_value=0)

    # Add row and column sums
    data_per_observable.loc['SUM', :] = data_per_observable.sum(axis=0).values
    data_per_observable['SUM'] = data_per_observable.sum(axis=1).values

    data_per_observable = data_per_observable.astype(int)

    return data_per_observable


if __name__ == '__main__':
    # Example data from the repository for testing
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', '..', 'doc/example/example_Fujita/')
    problem = petab.Problem.from_files(
        sbml_file=os.path.join(root_path, 'Fujita_model.xml'),
        condition_file=os.path.join(root_path, 'Fujita_experimentalCondition.tsv'),
        measurement_file=os.path.join(root_path, 'Fujita_measurementData.tsv'),
        parameter_file=os.path.join(root_path, 'Fujita_parameters.tsv'),
    )
    create_report(problem, 'Fujita')
