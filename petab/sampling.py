"""Functions related to parameter sampling"""

import numpy as np
import pandas as pd

from .parameters import get_priors_from_df


def sample_from_prior(prior: tuple,
                      n_starts: int):
    """Creates samples based on prior

    Arguments:
        prior: @type tuple
        n_starts: @type int
    """

    # unpack info
    p_type, p_params, scaling, bounds = prior

    # define a function to rescale the sampled points to parameter scale
    def scale(x):
        if scaling == 'lin':
            return x
        elif scaling == 'log':
            return np.log(x)
        elif scaling == 'log10':
            return np.log10(x)
        else:
            raise NotImplementedError('Parameter priors on the parameter '
                                      'scale ' + scaling + ' are currently '
                                      'not implemented.')

    def clip_to_bounds(x):
        tmp_x = [min([bounds[1], ix]) for ix in x]
        tmp_x = [max([bounds[0], ix]) for ix in tmp_x]
        return np.array(tmp_x)

    # define lambda functions for each parameter
    if p_type == 'uniform':
        sp = scale((p_params[1] - p_params[0]) * np.random.random((
             n_starts,)) + p_params[0])

    elif p_type == 'parameterScaleUniform':
        sp = (p_params[1] - p_params[0]) * np.random.random((n_starts,
                                                             )) + p_params[0]

    elif p_type == 'normal':
        sp = scale(np.random.normal(loc=p_params[0], scale=p_params[1],
                                    size=(n_starts,)))

    elif p_type == 'logNormal':
        sp = scale(np.exp(np.random.normal(
             loc=p_params[0], scale=p_params[1], size=(n_starts,))))

    elif p_type == 'parameterScaleNormal':
        sp = np.random.normal(loc=p_params[0], scale=p_params[1],
                              size=(n_starts,))

    elif p_type == 'laplace':
        sp = scale(np.random.laplace(
             loc=p_params[0], scale=p_params[1], size=(n_starts,)))

    elif p_type == 'logLaplace':
        sp = scale(np.exp(np.random.laplace(
             loc=p_params[0], scale=p_params[1], size=(n_starts,))))

    elif p_type == 'parameterScaleLaplace':
        sp = np.random.laplace(loc=p_params[0], scale=p_params[1],
                               size=(n_starts,))

    else:
        raise NotImplementedError('Parameter prs of type ' + prior[0] +
                                  ' are currently not implemented.')

    return clip_to_bounds(sp)


def sample_parameter_startpoints(parameter_df: pd.DataFrame,
                                 n_starts: int = 100):
    """Create numpy.array with starting points for an optimization

    Dimension of output: n_optimization_parameters x n_startpoints

    Arguments:
        parameter_df: @type pandas.DataFrame
        n_starts: @type int
    """

    # get types and parameters of priors from dataframe
    prior_list = get_priors_from_df(parameter_df)

    startpoints = [sample_from_prior(prior, n_starts) for prior in prior_list]

    return np.array(startpoints)
