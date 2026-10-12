"""Offline referee tests; deliberately never import candidate code on the host."""
from contextlib import AbstractContextManager
from pathlib import Path
from types import SimpleNamespace

import pytest

from survivevolve.arenas.magent2_battle import MAgent2BattleArena, duel_fitness, run_episode, team_of
from survivevolve.engines.openevolve_battle import make_evaluator
from survivevolve.execution.docker_policy import PolicyFailure
from survivevolve.models import Genome


class FakePolicy(AbstractContextManager):
    def __init__(self, source, seed):
        self.source = Path(source)
    def actions(self, batch):
        return [0] * len(batch)
    def __exit__(self, *args):
        return False


class FakeArena:
    def __init__(self, **kwargs):
        self.agents = ["red_0", "blue_0"]
    def reset(self, seed):
        assert seed >= 0
        return {"red_0": [], "blue_0": []}, {}
    def action_space(self, agent):
        return SimpleNamespace(n=21)
    def step(self, actions):
        assert actions == {"red_0": 0, "blue_0": 0}
        self.agents = []
        return {}, {"red_0": 2.0, "blue_0": 0.5}, {}, {}, {}
    def close(self):
        pass


def test_referee_does_not_execute_python_on_host(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    marker = tmp_path / "executed.txt"
    for policy in (a, b):
        policy.write_text(f"from pathlib import Path; Path({str(marker)!r}).touch()")
    assert run_episode(a, b, 17, env_factory=FakeArena, policy_factory=FakePolicy) == {
        "red": 2.0, "blue": 0.5}
    assert not marker.exists()


def test_side_swap_removes_constant_color_advantage(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    def match(red, blue, seed):
        return {"red": 2.0, "blue": 0.5}
    assert duel_fitness(a, b, (17, 29), match=match) == pytest.approx(0)


def test_bad_team_is_rejected():
    with pytest.raises(ValueError):
        team_of("unexpected_0")
    with pytest.raises(ValueError):
        MAgent2BattleArena().evaluate({"a": Genome("g", "pass")}, seed=17)


def test_evaluator_penalizes_invalid_policy_without_host_executing(tmp_path, monkeypatch):
    import survivevolve.engines.openevolve_battle as module
    program = tmp_path / "policy.py"
    program.write_text("raise RuntimeError('NEVER EXECUTE ON HOST')")
    def failure(*args, **kwargs):
        raise PolicyFailure()
    monkeypatch.setattr(module, "duel_fitness", failure)
    result = make_evaluator((17,))(str(program), "red", (
        SimpleNamespace(language="python", code="pass"),))
    assert result == {"combined_score": -10000.0, "invalid": 1.0}


def test_evaluator_uses_opponent_cohort_worst_case(tmp_path, monkeypatch):
    import survivevolve.engines.openevolve_battle as module
    program = tmp_path / "policy.py"
    program.write_text("pass")
    values = iter([3.0, -2.0])
    monkeypatch.setattr(module, "duel_fitness", lambda *args, **kwargs: next(values))
    result = make_evaluator((17, 29))(str(program), "blue", (
        SimpleNamespace(language="python", code="pass"),
        SimpleNamespace(language="python", code="pass"),
    ))
    assert result == {"combined_score": -2.0, "invalid": 0.0, "matches": 8.0}
