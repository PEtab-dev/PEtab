import abc
import numpy as np
import pandas as pd
import petab
import shutil
import sympy as sp
import tempfile
from typing import Dict, Optional


class Simulator(abc.ABC):
    """
    Base class that specific simulators should inherit.
    Specific simulators should minimally implement the
    `_simulate_without_noise` method.
    TODO link to amici.petab_simulate.PEtabSimulation as example
    """
    def __init__(self,
                 petab_problem: petab.Problem,
                 working_dir: Optional[str] = None):
        """
        Initializes the simulator with sufficient information to perform
        a simulation. If no working directory is specified, a temporary one is
        created.

        Arguments:
            petab_problem:
                A PEtab problem.
            working_dir:
                All simulator-specific output files will be saved here.
        """
        self.petab_problem = petab_problem
        if working_dir is None:
            working_dir = tempfile.mkdtemp()
        self.working_dir = working_dir
        self.noise_formulas = petab.calculate.get_symbolic_noise_formulas(
                self.petab_problem.observable_df)
        self.rng = np.random.default_rng()

    def clean_working_dir(self):
        """
        Deletes simulator-specific output files and their parent folder (see
        the `__init__` method arguments).
        """
        shutil.rmtree(self.working_dir)

    @abc.abstractmethod
    def _simulate_without_noise(self):
        """
        Returns:
            Simulated data, as a PEtab measurements table, which should be
            equivalent to replacing all values in the `petab.C.MEASUREMENT`
            column of the measurements table (of the PEtab problem supplied to
            the `__init__` method), with simulated values.
        """

    def simulate(self, noise=False, **kwargs):
        """
        Returns simulated data as a list of PEtab measurement dataframes.

        Arguments:
            noise: If True, noise is added to simulated data.

        Returns:
            Simulated data, as a PEtab measurements table.
        """
        simulation_df = self._simulate_without_noise(**kwargs)
        if noise:
            simulation_df = self._add_noise(simulation_df)
        return simulation_df

    def _add_noise(self, simulation_df):
        """
        Returns a noise value for each simulated value.

        Arguments:
            simulation_df:
                A PEtab measurements table that contains simulated data.

        Returns:
            Simulated data with noise, as a PEtab measurements table.
        """
        simulation_df_with_noise = simulation_df.copy()
        for (_, measurement_row), (index, simulation_row) in zip(
                self.petab_problem.measurement_df.iterrows(),
                simulation_df.iterrows()):
            simulation_df_with_noise.loc[index, petab.C.MEASUREMENT] = \
                sample_noise(
                    self.petab_problem,
                    measurement_row,
                    simulation_row[petab.C.MEASUREMENT],
                    self.noise_formulas,
                    self.rng,
                )
        return simulation_df_with_noise


def sample_noise(
        petab_problem: petab.Problem,
        measurement_row: pd.Series,
        simulated_value: float,
        noise_formulas: Optional[Dict[str, sp.Expr]] = None,
        rng: Optional[np.random.Generator] = None,
):
    """
    Returns a sample from a PEtab noise distribution.

    Arguments:
        petab_problem:
            The PEtab problem used to generate the simulated value.
            Instance of `petab.Problem`.
        measurement_row:
            The row in the PEtab problem measurement table that corresponds
            to the simulated value.
        simulated_value:
            A simulated value without noise.
        noise_formulas:
            Processed noise formulas from the PEtab observables table, in the
            form output by the `petab.calculate.get_symbolic_noise_formulas`
            method.
        rng:
            A NumPy random generator.
    """
    if rng is None:
        rng = np.random.default_rng()
    if noise_formulas is None:
        noise_formulas = petab.calculate.get_symbolic_noise_formulas(
            petab_problem.observable_df)

    noise_value = petab.calculate.evaluate_noise_formula(
        measurement_row,
        noise_formulas,
        petab_problem.parameter_df,
        simulated_value
    )

    # TODO replace petab.C.NORMAL with e.g.
    #      petab.C.DEFAULT_NOISE(==petab.C.NORMAL)?
    noise_distribution = (
        petab_problem
        .observable_df
        .loc[measurement_row[petab.C.OBSERVABLE_ID]]
        .get(petab.C.NOISE_DISTRIBUTION, petab.C.NORMAL)
    )

    # TODO check in a nicer way?
    # TODO unnecessary to check this? would be checked elsewhere with e.g.
    #      petablint?
    if noise_distribution not in petab.C.NOISE_MODELS:
        raise KeyError('Untested noise distribution.')

    # TODO write own method?
    # below is e.g.: `np.random.normal(loc=simulation, scale=noise_value)`
    return getattr(rng, noise_distribution)(simulated_value, noise_value)
