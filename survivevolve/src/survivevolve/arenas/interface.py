"""Protocol implemented by interchangeable trusted arenas/referees."""

from typing import Mapping, Protocol

from survivevolve.models import Genome, MatchResult


class Arena(Protocol):
    """Score N entrants against a seeded environment.

    An implementation supplies an *isolated* executor for each untrusted genome.
    It cannot delegate rule changes, scoring, or resource accounting to them.
    """

    def evaluate(self, entrants: Mapping[str, Genome], *, seed: int) -> MatchResult:
        """Return one score per entrant; the meaning is defined by the arena."""
        ...
