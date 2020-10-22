import abc
import numpy as np
import pathlib
import pandas as pd
import petab
import shutil
import sympy as sp
import tempfile
from typing import Dict, Optional, Union


class Simulator(abc.ABC):
    """
    Base class that specific simulators should inherit.
    Specific simulators should minimally implement the
    `simulate_without_noise` method.
    Example (AMICI): https://bit.ly/33SUSG4

    Attributes:
        noise_formulas:
            The formulae that will be used to calculate the scale of noise
            distributions.
        petab_problem:
            A PEtab problem, which will be simulated.
        rng:
            A NumPy random generator, used to sample from noise distributions.
        temporary_working_dir:
            Whether `working_dir` is a temporary directory, which can be
            deleted without significant consequence.
        working_dir:
            All simulator-specific output files will be saved here. This
            directory and its contents may be modified and deleted, and
            should be considered ephemeral.
    """
    def __init__(self,
                 petab_problem: petab.Problem,
                 working_dir: Optional[Union[pathlib.Path, str]] = None):
        """
        Initialize the simulator with sufficient information to perform a
        simulation. If no working directory is specified, a temporary one is
        created.

        Arguments:
            petab_problem:
                A PEtab problem.
            working_dir:
                All simulator-specific output files will be saved here. This
                directory and its contents may be modified and deleted, and
                should be considered ephemeral.
        """
        self.petab_problem = petab_problem

        self.temporary_working_dir = False
        if working_dir is None:
            working_dir = tempfile.mkdtemp()
            self.temporary_working_dir = True
        if not isinstance(working_dir, pathlib.Path):
            working_dir = pathlib.Path(working_dir)
        self.working_dir = working_dir
        self.working_dir.mkdir(parents=True, exist_ok=True)

        self.noise_formulas = petab.calculate.get_symbolic_noise_formulas(
            self.petab_problem.observable_df)
        self.rng = np.random.default_rng()

    def remove_working_dir(self, force: bool = False, **kwargs) -> None:
        """
        Remove the simulator working directory and all files within (see the
        `__init__` method arguments).

        Arguments:
            force:
                If True, the working directory is removed regardless of
                whether it is a temporary directory.
        """
        if force or self.temporary_working_dir:
            shutil.rmtree(self.working_dir, **kwargs)
            if self.working_dir.is_dir():
                print('Failed to remove the working directory: '
                      + str(self.working_dir))
        else:
            print('By default, specified working directories are not removed. '
                  'Please call this method with `force=True`, or manually '
                  f'delete the working directory: {self.working_dir}')

    @abc.abstractmethod
    def simulate_without_noise(self) -> pd.DataFrame:
        """
        Simulate a PEtab problem. This is an abstract method that should be
        implemented in a simulation package. Links to examples of this are in
        the class docstring.

        Returns:
            Simulated data, as a PEtab measurements table, which should be
            equivalent to replacing all values in the `petab.C.MEASUREMENT`
            column of the measurements table (of the PEtab problem supplied to
            the `__init__` method), with simulated values.
        """

    def simulate(
            self,
            noise: bool = False,
            noise_scaling_factor: float = 1,
            **kwargs
    ) -> pd.DataFrame:
        """Simulate a PEtab problem, optionally with noise.

        Arguments:
            noise: If True, noise is added to simulated data.
            noise_scaling_factor:
                A multiplier of the scale of the noise distribution.

        Returns:
            Simulated data, as a PEtab measurements table.
        """
        simulation_df = self.simulate_without_noise(**kwargs)
        if noise:
            simulation_df = self.add_noise(simulation_df, noise_scaling_factor)
        return simulation_df

    def add_noise(
            self,
            simulation_df: pd.DataFrame,
            noise_scaling_factor: float = 1,
    ) -> pd.DataFrame:
        """Add noise to simulated data.

        Arguments:
            simulation_df:
                A PEtab measurements table that contains simulated data.
            noise_scaling_factor:
                A multiplier of the scale of the noise distribution.

        Returns:
            Simulated data with noise, as a PEtab measurements table.
        """
        simulation_df_with_noise = simulation_df.copy()
        simulation_df_with_noise[petab.C.MEASUREMENT] = [
            sample_noise(
                self.petab_problem,
                row,
                row[petab.C.MEASUREMENT],
                self.noise_formulas,
                self.rng,
                noise_scaling_factor,
            )
            for _, row in simulation_df_with_noise.iterrows()
        ]
        return simulation_df_with_noise


def sample_noise(
        petab_problem: petab.Problem,
        measurement_row: pd.Series,
        simulated_value: float,
        noise_formulas: Optional[Dict[str, sp.Expr]] = None,
        rng: Optional[np.random.Generator] = None,
        noise_scaling_factor: float = 1,
) -> float:
    """Generate a sample from a PEtab noise distribution.

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
        noise_scaling_factor:
            A multiplier of the scale of the noise distribution.

    Returns:
        The sample from the PEtab noise distribution.
    """
    if noise_formulas is None:
        noise_formulas = petab.calculate.get_symbolic_noise_formulas(
            petab_problem.observable_df)
    if rng is None:
        rng = np.random.default_rng()

    noise_value = petab.calculate.evaluate_noise_formula(
        measurement_row,
        noise_formulas,
        petab_problem.parameter_df,
        simulated_value
    )

    # default noise distribution is petab.C.NORMAL
    noise_distribution = (
        petab_problem
        .observable_df
        .loc[measurement_row[petab.C.OBSERVABLE_ID]]
        .get(petab.C.NOISE_DISTRIBUTION, petab.C.NORMAL)
    )
    # an empty noise distribution column in an observables table can result in
    # `noise_distribution == float('nan')`
    if pd.isna(noise_distribution):
        noise_distribution = petab.C.NORMAL

    # below is e.g.: `np.random.normal(loc=simulation, scale=noise_value)`
    return getattr(rng, noise_distribution)(
        loc=simulated_value,
        scale=noise_value * noise_scaling_factor
    )
