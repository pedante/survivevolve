"""Trusted MAgent2 Battle referee. Candidate source is NEVER imported here.

Each color is controlled by one evolving *team policy*, not a persistent
individual organism. Future arenas need not share that restriction.
"""
from contextlib import ExitStack
from pathlib import Path
from typing import Mapping

from survivevolve.execution.docker_policy import DockerPolicy
from survivevolve.models import Genome, MatchResult


def team_of(agent_id: str) -> str:
    if agent_id.startswith("red_"):
        return "red"
    if agent_id.startswith("blue_"):
        return "blue"
    raise ValueError("unexpected arena agent ID")


def run_episode(red: Path, blue: Path, seed: int, *, cycles: int = 24,
                env_factory=None, policy_factory=DockerPolicy) -> dict[str, float]:
    """Run real MAgent2 by default; injectable factories are for offline tests."""
    if env_factory is None:
        from magent2.environments import battle_v4
        env_factory = battle_v4.parallel_env
    env = env_factory(map_size=12, max_cycles=cycles, render_mode=None)
    scores = {"red": 0.0, "blue": 0.0}
    try:
        observations, _ = env.reset(seed=seed)
        with ExitStack() as stack:
            policies = {
                "red": stack.enter_context(policy_factory(red, seed)),
                "blue": stack.enter_context(policy_factory(blue, seed + 100000)),
            }
            for _ in range(cycles):
                if not env.agents:
                    break
                buckets = {"red": [], "blue": []}
                for agent in env.agents:
                    obs = observations[agent]
                    buckets[team_of(agent)].append({
                        "agent_id": agent,
                        "observation": obs.tolist() if hasattr(obs, "tolist") else obs,
                        "num_actions": env.action_space(agent).n,
                    })
                actions = {}
                for side, batch in buckets.items():
                    if batch:
                        reply = policies[side].actions(batch)
                        actions.update({item["agent_id"]: action
                                        for item, action in zip(batch, reply)})
                observations, rewards, _, _, _ = env.step(actions)
                for agent, reward in rewards.items():
                    scores[team_of(agent)] += float(reward)
        return scores
    finally:
        env.close()


def duel_fitness(candidate: Path, opponent: Path, seeds=(17, 29), *,
                 match=run_episode) -> float:
    """Candidate advantage against an opponent with map-color bias cancelled."""
    if not seeds:
        raise ValueError("at least one seed required")
    advantages = []
    for seed in seeds:
        first = match(candidate, opponent, seed)
        second = match(opponent, candidate, seed)
        advantages.extend((first["red"] - first["blue"],
                           second["blue"] - second["red"]))
    return sum(advantages) / len(advantages)


class MAgent2BattleArena:
    """Arena contract implementation, with exactly two team-controlled sides."""

    def __init__(self, *, cycles: int = 24):
        self.cycles = cycles

    def evaluate(self, entrants: Mapping[str, Genome], *, seed: int) -> MatchResult:
        if set(entrants) != {"red", "blue"}:
            raise ValueError("MAgent2 Battle adapter expects red and blue genomes")
        # The temporary directory stores *data*, not executable host modules.
        import tempfile
        with tempfile.TemporaryDirectory(prefix="survivevolve-battle-") as temp:
            root = Path(temp)
            red, blue = root / "red.py", root / "blue.py"
            red.write_text(entrants["red"].code)
            blue.write_text(entrants["blue"].code)
            scores = run_episode(red, blue, seed, cycles=self.cycles)
        return MatchResult(scores=scores, metadata={"arena": "magent2.battle_v4"})
