try:
    import amici
except ImportError:
    raise ImportError(
        "Requested simulation with AMICI, but AMICI was not found."
        "Install with `pip install amici`. https://github.com/AMICI-dev/AMICI"
    )

import amici.petab_import
import amici.petab_objective

from .simulator import Simulator

class AmiciSimulator(Simulator):
    """
    amici_model:
        Instance of an `amici.amici.ModelPtr` object (TODO confirm).
    """
    def simulate(self):
        """
        See Simulator.simulate() docstring.
        """
        if 'amici_model' not in dir(self):
            self.model_output_dir = self.working_dir + '/amici_models'
            # TODO don't compute sensitivities
            # TODO allow amici_model to be passed as argument
            self.amici_model = amici.petab_import.import_petab_problem(
                self.petab_problem,
                model_output_dir=self.model_output_dir
            )

        # TODO allow specification of solver?
        result = amici.petab_objective.simulate_petab(
            self.petab_problem,
            self.amici_model,
        )

        # TODO use `rdatas_to_simulation_df` instead?
        self.simulation_df = amici.petab_objective.rdatas_to_measurement_df(
            result['rdatas'],
            self.amici_model,
            self.petab_problem.measurement_df,
        )

        noise = self.simulation_noise()
        self.simulation_df['measurement'] = noise

        return self.simulation_df

    def set_model(self, amici_model: amici.amici.ModelPtr):
        self.amici_model = amici_model
