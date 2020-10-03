"""Test for petab.yaml"""
import pytest

import petab
import petab.simulate

try:
    import amici
except ImportError:
    with_AMICI = False
else:
    with_AMICI = True

def test_synthetic_data_AMICI():
    if not with_AMICI:
        return

    petab_yaml_filepath = '../../../petab/conversion_reaction.yaml'
    petab_problem = petab.Problem.from_yaml(petab_yaml_filepath)
    simulator = petab.simulate.AmiciSimulator(petab_problem)
    simulation_df = simulator.simulate(noise=True)
    simulator.clean_working_dir()
