"""Portable *data* passed across engine and arena boundaries.

These objects do not execute generated code. Genome source and prompts are data,
not trusted Python to be loaded inside the referee or orchestrator process.
"""

from dataclasses import dataclass, field
from typing import Mapping, Optional


@dataclass(frozen=True)
class Genome:
    """One immutable version of an organism's editable artifacts.

    `parent_id` is an optional pointer to the predecessor's artifact identifier,
    not a complete lineage database. Organism identity and resources are separate
    future concerns; neither should be stored in mutable engine internals.
    """

    artifact_id: str
    code: str
    prompt: str = ""
    parent_id: Optional[str] = None
    language: str = "python"


@dataclass(frozen=True)
class Evaluation:
    """Trusted evaluator's metric report; higher combined_score is better.

    Metrics have engine-independent names. A trusted component must validate
    values and sandbox code *before* producing this report.
    """

    metrics: Mapping[str, float]


@dataclass(frozen=True)
class EvolutionRequest:
    """A bounded batch request. The organism-owned mutation decision comes later."""

    initial: Genome
    iterations: int
    seed: int


@dataclass(frozen=True)
class EvolutionResult:
    """Outcome of one optimization run, retaining the best exact genome."""

    best: Genome
    evaluation: Evaluation
    candidates_evaluated: int


@dataclass(frozen=True)
class MatchResult:
    """Per-entrant results for one match, independent of population count.

    Live observations and event streams will be a separate, later interface.
    """

    scores: Mapping[str, float]
    metadata: Mapping[str, str] = field(default_factory=dict)
