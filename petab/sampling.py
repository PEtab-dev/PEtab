"""Functions related to parameter sampling"""

import numpy as np
import pandas as pd

from typing import Tuple

from . import parameters
from .C import *  # noqa: F403


def sample_from_prior(prior: Tuple[str, list, str, list],
                      n_starts: int) -> np.array:
    """Creates samples for one parameter based on prior

    Arguments:
        prior: A tuple as obtained from ``petab.parameter.get_priors_from_df``
        n_starts: Number of samples

    Returns:
        Array with sampled values
    """

    # unpack info
    p_type, p_params, scaling, bounds = prior

    # define a function to rescale the sampled points to parameter scale
    def scale(x):
        if scaling == LIN:
            return x
        if scaling == LOG:
            return np.log(x)
        if scaling == LOG10:
            return np.log10(x)
        raise NotImplementedError(
            f"Parameter priors on the parameter scale {scaling} are "
            "currently not implemented.")

    def clip_to_bounds(x: np.array):
        """Clip values in array x to bounds"""
        x = np.maximum(np.minimum(scale(bounds[1]), x), scale(bounds[0]))
        return x

    # define lambda functions for each parameter
    if p_type == UNIFORM:
        sp = scale((p_params[1] - p_params[0]) * np.random.random((
            n_starts,)) + p_params[0])

    elif p_type == PARAMETER_SCALE_UNIFORM:
        sp = (p_params[1] - p_params[0]) * np.random.random((n_starts,
                                                             )) + p_params[0]

    elif p_type == NORMAL:
        sp = scale(np.random.normal(loc=p_params[0], scale=p_params[1],
                                    size=(n_starts,)))

    elif p_type == LOG_NORMAL:
        sp = scale(np.exp(np.random.normal(
            loc=p_params[0], scale=p_params[1], size=(n_starts,))))

    elif p_type == PARAMETER_SCALE_NORMAL:
        sp = np.random.normal(loc=p_params[0], scale=p_params[1],
                              size=(n_starts,))

    elif p_type == LAPLACE:
        sp = scale(np.random.laplace(
            loc=p_params[0], scale=p_params[1], size=(n_starts,)))

    elif p_type == LOG_LAPLACE:
        sp = scale(np.exp(np.random.laplace(
            loc=p_params[0], scale=p_params[1], size=(n_starts,))))

    elif p_type == PARAMETER_SCALE_LAPLACE:
        sp = np.random.laplace(loc=p_params[0], scale=p_params[1],
                               size=(n_starts,))

    else:
        raise NotImplementedError(
            f"Parameter priors of type {prior[0]} are not implemented.")

    return clip_to_bounds(sp)


def sample_parameter_startpoints(parameter_df: pd.DataFrame,
                                 n_starts: int = 100,
                                 seed: int = None) -> np.array:
    """Create numpy.array with starting points for an optimization

    Arguments:
        parameter_df: PEtab parameter DataFrame
        n_starts: Number of points to be sampled
        seed: Random number generator seed (see numpy.random.seed)

    Returns:
        Array of sampled starting points with dimensions
        n_startpoints x n_optimization_parameters
    """
    if seed is not None:
        np.random.seed(seed)

    # get types and parameters of priors from dataframe
    prior_list = parameters.get_priors_from_df(
        parameter_df, mode=INITIALIZATION)

    startpoints = [sample_from_prior(prior, n_starts) for prior in prior_list]

    return np.array(startpoints).T
