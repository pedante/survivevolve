"""M0 contracts can be used without importing or running OpenEvolve/MAgent2."""

from dataclasses import FrozenInstanceError

import pytest

from survivevolve.arenas.interface import Arena
from survivevolve.engines.interface import EvolutionEngine
from survivevolve.models import Evaluation, EvolutionRequest, EvolutionResult, Genome, MatchResult


class FixedEngine:
    """Test double, emphatically not an evolutionary organism implementation."""

    def run(self, request, evaluate):
        assert request.iterations > 0
        measured = evaluate(request.initial)
        return EvolutionResult(request.initial, measured, 1)


class FixedArena:
    def evaluate(self, entrants, *, seed):
        return MatchResult(
            scores={name: float(seed + len(genome.code)) for name, genome in entrants.items()}
        )


def test_genome_is_immutable_and_keeps_prompt_lineage():
    genome = Genome("g1", "def act(obs): return 0", "Avoid fights", "g0")
    assert genome.prompt == "Avoid fights"
    assert genome.parent_id == "g0"
    with pytest.raises(FrozenInstanceError):
        genome.code = "print('modified')"


def test_engine_is_replaceable_and_uses_trusted_evaluation():
    genome = Genome("g1", "def act(obs): return 0")
    engine: EvolutionEngine = FixedEngine()
    seen = []

    def evaluate(candidate):
        seen.append(candidate.artifact_id)
        return Evaluation({"combined_score": 0.7})

    result = engine.run(EvolutionRequest(genome, iterations=5, seed=42), evaluate)
    assert result.best == genome
    assert result.evaluation.metrics["combined_score"] == 0.7
    assert result.candidates_evaluated == 1
    assert seen == ["g1"]


def test_arena_accepts_more_than_two_independent_entrants():
    arena: Arena = FixedArena()
    entrants = {f"organism-{i}": Genome(f"v{i}", "x" * (i + 1)) for i in range(4)}
    before = dict(entrants)
    result = arena.evaluate(entrants, seed=17)
    assert result.scores == {f"organism-{i}": float(18 + i) for i in range(4)}
    assert entrants == before


def test_importing_contracts_does_not_execute_candidate_code(tmp_path):
    marker = tmp_path / "candidate-executed.txt"
    source = f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')"
    genome = Genome("untrusted", source)
    assert genome.code == source
    assert not marker.exists()
