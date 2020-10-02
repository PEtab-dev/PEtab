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
    noise_formulas:
        Noise formulas as specified in PEtab observables table.
    petab_problem:
        Instance of `petab.Problem`.
    simulation_df:
        A PEtab measurements table that contains simulated data, generated by
        the `Simulator.simulate()` method.
    working_dir:
        The directory that will store any simulation-specific files. For
        example, compiled model files.
    """
    def __init__(self,
                 petab_problem: petab.Problem,
                 working_dir: Optional[str] = None):
        """
        Initializes the simulator with sufficient information to perform
        a simulation. If no working directory is specified, a temporary one is
        created.

        Arguments:
            working_dir: all files output by the simulator will be saved here
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
        Deletes the temporary directory (and its contents) that was created
        by `self.__init__()`.
        """
        shutil.rmtree(self.working_dir)

    @abc.abstractmethod
    def simulate(self):
        """
        Returns simulated data as a list of PEtab measurement dataframes.
        """

    def simulation_noise(self):
        """
        Returns a noise value for each simulated value.
        Requires `self.simulation_df` (set with e.g. `self.simulate()`).
        """
        noises = []
        for (_, measurement_row), simulation in zip(
                self.petab_problem.measurement_df.iterrows(),
                self.simulation_df[petab.C.MEASUREMENT]):
            noises.append(sample_noise(
                self.petab_problem,
                measurement_row,
                simulation,
                self.noise_formulas,
                self.rng,
            ))
        return noises

def sample_noise(
        petab_problem: petab.Problem,
        measurement_row: pd.Series,
        simulation: float,
        noise_formulas: Optional[Dict[str, sp.Expr]] = None,
        rng: Optional[np.random.Generator] = None,
):
    """
    Returns a sample from a PEtab noise distribution.
    TODO: rewrite to accept a PEtab problem, measurement row and simulation
          value instead?
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
        simulation
    )

    # TODO replace petab.C.NORMAL with some petab.C.DEFAULT_NOISE(==petab.C.NORMAL)?
    noise_distribution = (
        petab_problem
        .observable_df
        .loc[measurement_row[petab.C.OBSERVABLE_ID]]
        .get(petab.C.NOISE_DISTRIBUTION, petab.C.NORMAL)
    )

    # TODO check in a nicer way?
    assert noise_distribution in ['normal', 'laplace']

    # TODO write own method?
    # below is e.g.: `np.random.normal(loc=simulation, scale=noise_value)`
    return getattr(rng, noise_distribution)(simulation, noise_value)
