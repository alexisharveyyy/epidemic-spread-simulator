"""Pydantic v2 request models for the epidemic simulator API.

All models use Pydantic v2 syntax: `model_config = ConfigDict(...)` and
`@model_validator(mode="after")` for cross-field validation.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants import (
    DEFAULT_BETA,
    DEFAULT_EXPORT_CSV,
    DEFAULT_GAMMA,
    DEFAULT_INITIAL_INFECTED,
    DEFAULT_POPULATION,
    DEFAULT_TIME_DAYS,
    MAX_DAYS,
    MAX_POPULATION,
    SPREAD_MAX_DAY,
)


class SimulationRequest(BaseModel):
    """Parameters for a single SIR simulation run."""

    population: int = Field(default=DEFAULT_POPULATION, ge=2, le=MAX_POPULATION)
    beta: float = Field(default=DEFAULT_BETA, gt=0.0, lt=1.0)
    gamma: float = Field(default=DEFAULT_GAMMA, gt=0.0, lt=1.0)
    initial_infected: int = Field(default=DEFAULT_INITIAL_INFECTED, ge=1)
    initial_recovered: int = Field(default=0, ge=0)
    days: int = Field(default=DEFAULT_TIME_DAYS, ge=1, le=MAX_DAYS)
    export_csv: bool = Field(default=DEFAULT_EXPORT_CSV)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "population": 100000,
                "beta": 0.3,
                "gamma": 0.1,
                "initial_infected": 10,
                "initial_recovered": 0,
                "days": 160,
                "export_csv": False,
            }
        }
    )

    @model_validator(mode="after")
    def _validate_initial_compartments(self) -> "SimulationRequest":
        # The vaccination page seeds `initial_recovered` with a chosen
        # immune fraction. The combined size of the non-susceptible
        # compartments must leave at least one susceptible person, otherwise
        # the simulation is trivially complete and the ODE solver returns a
        # degenerate result.
        if self.initial_infected + self.initial_recovered >= self.population:
            raise ValueError(
                "initial_infected + initial_recovered must be strictly "
                "less than population"
            )
        return self


class SpreadRequest(BaseModel):
    """Parameters for a geographic spread map preview."""

    origin_lat: float = Field(ge=-90, le=90)
    origin_lng: float = Field(ge=-180, le=180)
    day: int = Field(ge=0, le=SPREAD_MAX_DAY)
    beta: float = Field(gt=0.0, lt=1.0)
    gamma: float = Field(gt=0.0, lt=1.0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_lat": 35.68,
                "origin_lng": 139.69,
                "day": 30,
                "beta": 0.3,
                "gamma": 0.1,
            }
        }
    )


class SensitivityRequest(BaseModel):
    """Parameters for a parameter sweep over `beta` or `gamma`.

    The fixed SIR fields (population, beta, gamma, initial_infected, days)
    supply the baseline values; whichever of `beta` or `gamma` is named in
    `sweep_parameter` is overridden by each sweep value at run time.
    """

    sweep_parameter: Literal["beta", "gamma"]
    sweep_from: float = Field(gt=0.0, lt=1.0)
    sweep_to: float = Field(gt=0.0, lt=1.0)
    step: float = Field(gt=0.0, le=0.5)

    population: int = Field(default=DEFAULT_POPULATION, ge=2, le=MAX_POPULATION)
    beta: float = Field(default=DEFAULT_BETA, gt=0.0, lt=1.0)
    gamma: float = Field(default=DEFAULT_GAMMA, gt=0.0, lt=1.0)
    initial_infected: int = Field(default=DEFAULT_INITIAL_INFECTED, ge=1)
    days: int = Field(default=DEFAULT_TIME_DAYS, ge=1, le=MAX_DAYS)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sweep_parameter": "beta",
                "sweep_from": 0.10,
                "sweep_to": 0.40,
                "step": 0.05,
                "population": 100000,
                "beta": 0.3,
                "gamma": 0.1,
                "initial_infected": 10,
                "days": 160,
            }
        }
    )

    @model_validator(mode="after")
    def _validate_range(self) -> "SensitivityRequest":
        if self.sweep_to <= self.sweep_from:
            raise ValueError("sweep_to must be greater than sweep_from")
        return self
