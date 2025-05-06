"""This contains the pedantic schema for the petab Result datastructure."""
from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


class VersionedMetadata(BaseModel, extra="allow"):
    """Any kind of Metadata (e.g. packages) including version.

    Additonal info may be added.
    """

    id: str
    version: str


class PetabProblemSnapshot(BaseModel):
    """The PEtab problem as it was used for result generation.

    Extensive description of the PEtab data format can be found
    at https://petab.readthedocs.io/en/latest/documentation_data_format.html.
    """

    measurement_df: list[dict]
    observable_df: list[dict]
    condition_df: list[dict]
    parameter_df: list[dict]
    sbml_file: str = Field(description="SMBL model as a string representation")


class OptimizationResult(BaseModel):
    """The result of a single optimization."""

    id: str = Field(
        description="Unique identifier for the optimization result. "
        "Multi-start local optimizations should be separated for "
        "each startpoint."
    )
    optimizer: VersionedMetadata = Field(
        description="Metadata on the optimizer used."
    )
    startpoint: Union[list[float], list[list[float]]] = Field(
        description="Starting point(s) for the optimization. May be multiple in"
        "case of swarm based optimizers. Dimension: (n_parameters) | (n_starts, n_parameters)"
    )
    endpoint: list[float] = Field(
        description="End point of the "
        "optimization. Dimension: (n_parameters)"
    )
    fval: float = Field(description="Final value of the objective function.")
    fval0: Optional[float] = Field(
        None, description="Initial value of the objective function."
    )
    grad: Optional[list[float]] = Field(
        None, description="Gradient at the endpoint. Dimension: (n_parameters)"
    )
    hess: Optional[list[list[float]]] = Field(
        None,
        description="Hessian at the endpoint. Dimension: (n_parameters, n_parameters)",
    )
    history: Optional[str] = Field(
        None,
        description="Link to file of History of the optimization process",
    )


class SamplingResult(BaseModel):
    """Sampling result for a single sampling execution with one or more chains."""

    id: str = Field(description="Unique identifier for the sampling result")
    sampler: VersionedMetadata
    sampler_settings: dict = Field(description="Settings for the sampler")
    parameter_startpoints: Optional[
        Union[list[list[float]], list[float]]
    ] = Field(
        None,
        description="Dimension: (n_chains, n_parameters) or (n_parameters)",
    )
    samples: Optional[
        Union[list[list[list[float]]], list[list[float]]]
    ] = Field(
        None,
        description="Dimension: (n_chains, n_samples, n_parameters) or (n_samples, n_parameters)",
    )
    parameter_trace: Optional[
        Union[list[list[list[float]]], list[list[float]]]
    ] = Field(
        None,
        description="Dimension (n_chains, trace_length, n_parameters) or (trace_length, n_parameters)",
    )
    log_posterior_trace: Optional[
        Union[list[list[float]], list[float]]
    ] = Field(
        None,
        description="Dimension: (n_chains, trace_length) or (trace_length)",
    )
    number_of_chains: Optional[int] = Field(
        None, description="Number of chains used in the sampling"
    )
    burn_in: Optional[int] = Field(
        None, description="Number of burn-in samples"
    )
    thinning: Optional[int] = Field(None, description="Thinning factor")


class ProfilingResult(BaseModel):
    """Profiling result for a single parameter profile."""

    id: str = Field(description="Unique identifier for the profiling result")
    profile_method: VersionedMetadata
    profile_settings: dict
    profile_parameter_id: str = Field(
        description="ID of the profiled parameter"
    )
    profile_startpoint: Optional[list[float]] = Field(
        None, description="Parameter vector from which the profile was started"
    )
    profile_parameter_trace: Optional[list[list[float]]] = Field(
        None, description="Dimension: (trace_length, n_parameters)"
    )
    profile_objective_trace: Optional[list[float]] = Field(
        None, description="Dimension: (trace_length)"
    )
    profile_confidence_interval: Optional[tuple[float, float]] = Field(
        None, description="Confidence interval for the profile"
    )
    profile_confidence_level: Optional[float] = Field(
        None, description="Confidence level for the profile"
    )


class OptimizeResult(BaseModel):
    """Optimization result for multiple optimization starts."""

    optimization_result: list[OptimizationResult]


class SampleResult(BaseModel):
    """Sample result for multiple sampling executions."""

    sampling_results: list[SamplingResult]


class ProfileResult(BaseModel):
    """Profile results for multiple parameters and/or methods."""

    profile_results: list[ProfilingResult]


class Result(BaseModel):
    """The result object structure."""

    system: VersionedMetadata = Field(description="System metadata")
    programming_language: VersionedMetadata = Field(
        description="Programming language."
    )
    tool_origin: VersionedMetadata = Field(
        description="Origin tool in which " "the result was " "created."
    )
    date: Optional[datetime] = Field(None, description="Time of saving.")
    author: Optional[str] = Field(
        None,
        description="The name of the author responsible for the result.",
    )
    petab_problem_snapshot: PetabProblemSnapshot = Field(
        description="Snapshot of the PEtab problem"
    )
    optimization_result: Optional[OptimizeResult] = Field(
        None, description="Optimization results"
    )
    sample_result: Optional[SampleResult] = Field(
        None, description="Sampling results"
    )
    profile_result: Optional[ProfileResult] = Field(
        None, description="Profiling results"
    )
