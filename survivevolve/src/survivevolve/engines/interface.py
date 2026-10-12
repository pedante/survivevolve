"""Protocol implemented by interchangeable evolutionary search engines."""

from typing import Callable, Protocol

from survivevolve.models import Evaluation, EvolutionRequest, EvolutionResult, Genome


# Scoring stays outside the engine. Implementations must never run untrusted
# Genome.code in-process; evaluations belong to trusted, sandboxed adapters.
FitnessFunction = Callable[[Genome], Evaluation]


class EvolutionEngine(Protocol):
    """A batch search API, not a mandate to use any particular search algorithm.

    M0 deliberately does not encode OpenEvolve's two-population restriction.
    Per-organism/on-demand mutation will be a separately versioned capability.
    """

    def run(self, request: EvolutionRequest, evaluate: FitnessFunction) -> EvolutionResult:
        """Run bounded evolution and return actual source code and metrics."""
        ...
