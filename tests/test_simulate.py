"""Tests for petab/simulate.py."""
import functools
import numpy as np
import pandas as pd
import pathlib
import pytest
import scipy.stats
from typing import Callable

import petab
from petab.C import MEASUREMENT


class TestSimulator(petab.simulate.Simulator):
    """Dummy simulator."""

    __test__ = False

    def simulate_without_noise(self) -> pd.DataFrame:
        """Dummy simulation."""
        return self.petab_problem.measurement_df


@pytest.fixture
def petab_problem() -> petab.Problem:
    """Create a PEtab problem for use in tests."""
    petab_yaml_path = pathlib.Path(__file__).parent.absolute() / \
        '../doc/example/example_Fujita/Fujita.yaml'
    return petab.Problem.from_yaml(str(petab_yaml_path))


def test_remove_working_dir(petab_problem):
    """Test creation and removal of a non-empty temporary working directory."""
    simulator = TestSimulator(petab_problem)
    # The working directory exists
    assert pathlib.Path(simulator.working_dir).is_dir()
    synthetic_data_df = simulator.simulate()
    synthetic_data_df.to_csv(f'{simulator.working_dir}/test.csv', sep='\t')
    simulator.remove_working_dir()
    # The (non-empty) working directory is removed
    assert not pathlib.Path(simulator.working_dir).is_dir()

    # Test creation and removal of a specified working directory
    working_dir = 'tests/test_simulate_working_dir'
    simulator = TestSimulator(petab_problem, working_dir=working_dir)
    # The working directory is as specified
    assert working_dir == str(simulator.working_dir)
    # The working directory exists
    assert pathlib.Path(simulator.working_dir).is_dir()
    # A user-specified working directory should not be removed unless
    # `force=True`.
    simulator.remove_working_dir()
    # The user-specified working directory is not removed without `force=True`
    assert pathlib.Path(simulator.working_dir).is_dir()
    simulator.remove_working_dir(force=True)
    # The user-specified working directory is removed with `force=True`
    assert not pathlib.Path(simulator.working_dir).is_dir()

    # Test creation and removal of a specified non-empty working directory
    simulator = TestSimulator(petab_problem, working_dir=working_dir)
    synthetic_data_df = simulator.simulate()
    synthetic_data_df.to_csv(f'{simulator.working_dir}/test.csv', sep='\t')
    simulator.remove_working_dir(force=True)
    # The non-empty, user-specified directory is removed with `force=True`
    assert not pathlib.Path(simulator.working_dir).is_dir()


def test_zero_bounded(petab_problem):
    """Test `zero_bounded` argument of `sample_noise`."""
    positive = np.spacing(1)
    negative = -positive

    simulator = TestSimulator(petab_problem)

    # Set approximately half of the measurements to negative values, and the
    # rest to positive values.
    n_measurements = len(petab_problem.measurement_df)
    neg_indices = range(round(n_measurements / 2))
    pos_indices = range(len(neg_indices), n_measurements)
    measurements = [
        negative if index in neg_indices else
        (positive if index in pos_indices else np.nan)
        for index in range(n_measurements)
    ]
    synthetic_data_df = simulator.simulate().assign(**{
        petab.C.MEASUREMENT: measurements
    })
    # All measurements are non-zero
    assert (synthetic_data_df['measurement'] != 0).all()
    # No measurements are NaN
    assert not (np.isnan(synthetic_data_df['measurement'])).any()

    synthetic_data_df_with_noise = simulator.add_noise(
        synthetic_data_df,
    )
    # Both negative and positive values are returned by default.
    # This test will occasionally fail.
    assert all([
        (synthetic_data_df_with_noise['measurement'] <= 0).any(),
        (synthetic_data_df_with_noise['measurement'] >= 0).any(),
    ])

    synthetic_data_df_with_noise = simulator.add_noise(
        synthetic_data_df,
        zero_bounded=True,
    )
    # Values with noise that are different in sign to values without noise
    # are zeroed.
    # This test will occasionally fail.
    assert all([
        (synthetic_data_df_with_noise['measurement'][neg_indices] <= 0).all(),
        (synthetic_data_df_with_noise['measurement'][pos_indices] >= 0).all(),
        (synthetic_data_df_with_noise['measurement'][neg_indices] == 0).any(),
        (synthetic_data_df_with_noise['measurement'][pos_indices] == 0).any(),
        (synthetic_data_df_with_noise['measurement'][neg_indices] < 0).any(),
        (synthetic_data_df_with_noise['measurement'][pos_indices] > 0).any(),
    ])


def test_add_noise(petab_problem):
    """Test the noise generating method."""

    tested_noise_distributions = {'normal', 'laplace'}
    assert set(petab.C.NOISE_MODELS) == tested_noise_distributions, (
        'The noise generation methods have only been tested for '
        f'{tested_noise_distributions}. Please edit this test '
        'to include this distribution in its tested distributions. The '
        'appropriate SciPy distribution will need to be added to '
        '`petab_numpy2scipy_distribution` in `_test_add_noise`.'
    )

    for distribution in tested_noise_distributions:
        petab_problem.observable_df[petab.C.NOISE_DISTRIBUTION] = distribution
        _test_add_noise(petab_problem)


def _test_add_noise(petab_problem) -> None:
    """Test the noise generating method."""
    n_samples = 100
    noise_scaling_factor = 0.5
    ks_1samp_pvalue_threshold = 0.05
    minimum_fraction_above_threshold = 0.9
    petab_numpy2scipy_distribution = {
        'normal': 'norm',
        'laplace': 'laplace',
    }

    simulator = TestSimulator(petab_problem)
    synthetic_data_df = simulator.simulate()

    # Generate samples of noisy data
    samples = []
    for _ in range(n_samples):
        samples.append(
            simulator.add_noise(
                synthetic_data_df,
                noise_scaling_factor=noise_scaling_factor,
            )[MEASUREMENT]
        )
    samples = np.array(samples)

    expected_noise_values = [
        noise_scaling_factor *
        petab.calculate.evaluate_noise_formula(
            row,
            simulator.noise_formulas,
            petab_problem.parameter_df,
            row[MEASUREMENT],
        )
        for _, row in synthetic_data_df.iterrows()
    ]
    expected_noise_distributions = [
        petab_problem
        .observable_df
        .loc[row[petab.C.OBSERVABLE_ID]]
        .get(petab.C.NOISE_DISTRIBUTION, petab.C.NORMAL)
        for _, row in synthetic_data_df.iterrows()
    ]

    def row2cdf(row, index) -> Callable:
        """
        Get and customize the appropriate cumulative distribution function from
        `scipy.stats`.

        Arguments:
            row:
                A row from a PEtab measurement table.
            index:
                The index of the row.

        Returns:
            The appropriate SciPy cumulative distribution function, setup to
            produce noisy simulated data.
        """
        return functools.partial(
            getattr(
                scipy.stats,
                petab_numpy2scipy_distribution[
                    expected_noise_distributions[index]]
            ).cdf, loc=row[MEASUREMENT], scale=expected_noise_values[index])

    # Test whether the distribution of the samples is equal to the expected
    # distribution, for each measurement.
    results = []
    for index, row in synthetic_data_df.iterrows():
        r = scipy.stats.ks_1samp(
            samples[:, index],
            row2cdf(row, index)
        )
        results.append(r)
    observed_fraction_above_threshold = (
        sum(r.pvalue > ks_1samp_pvalue_threshold for r in results) /
        len(results)
    )
    # Sufficient distributions of measurement samples are sufficiently similar
    # to the expected distribution
    assert (
        observed_fraction_above_threshold > minimum_fraction_above_threshold)

    simulator.remove_working_dir()
    assert not pathlib.Path(simulator.working_dir).is_dir()
