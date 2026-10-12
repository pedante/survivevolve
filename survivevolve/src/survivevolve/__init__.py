"""Survivevolve's upstream-independent extension contracts.

M0 includes no arena, evolutionary implementation, or unsafe code runner.
"""

from .models import Evaluation, EvolutionRequest, EvolutionResult, Genome, MatchResult

__all__ = ["Evaluation", "EvolutionRequest", "EvolutionResult", "Genome", "MatchResult"]
