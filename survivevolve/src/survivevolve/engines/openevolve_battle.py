"""OpenEvolve coevolution over MAgent2 Battle. Two team policies, not living agents."""
import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path
from urllib.parse import urlsplit

from survivevolve.arenas.magent2_battle import duel_fitness, run_episode
from survivevolve.execution.docker_policy import DockerPolicy, PolicyFailure

POLICIES = Path(__file__).resolve().parents[1] / "policies"


def docker_preflight(image: str) -> None:
    if not shutil.which("docker"):
        raise RuntimeError("Docker CLI is required: refusing unsafe fallback")
    for args in (("info", "--format", "{{.ServerVersion}}"), ("image", "inspect", image)):
        result = subprocess.run(["docker", *args], capture_output=True,
                                text=True, timeout=15, check=False)
        if result.returncode:
            raise RuntimeError("Docker daemon or policy image unavailable; build the M1 policy image")


def make_evaluator(seeds: tuple[int, ...], *, cycles: int = 24,
                   image: str = "survivevolve-policy:m1"):
    """Cloudpickle-compatible evaluator for OpenEvolve; generated code stays outside host."""
    if not seeds:
        raise ValueError("one or more matched seeds required")

    def evaluate(path, population_name, opponents):
        if population_name not in ("red", "blue") or not opponents:
            raise ValueError("invalid population/opponent set")
        try:
            with tempfile.TemporaryDirectory(prefix="sv-opponents-") as temp:
                outcomes = []
                for index, opponent in enumerate(opponents):
                    if opponent.language.lower() != "python":
                        return {"combined_score": -10000.0, "invalid": 1.0}
                    opponent_file = Path(temp) / f"opponent-{index}.py"
                    opponent_file.write_text(opponent.code)
                    score = duel_fitness(
                        Path(path), opponent_file, seeds,
                        match=lambda a, b, seed: run_episode(
                            a, b, seed, cycles=cycles,
                            policy_factory=partial(DockerPolicy, image=image)),
                    )
                    outcomes.append(score)
            return {"combined_score": min(outcomes), "invalid": 0.0,
                    "matches": float(len(opponents) * len(seeds) * 2)}
        except PolicyFailure as exc:
            logging.getLogger(__name__).warning("sandboxed policy invalid: %s", exc)
            return {"combined_score": -10000.0, "invalid": 1.0}
        # Unexpected environment errors must abort rather than mark valid code invalid.
    return evaluate


def engine_config(seed: int, *, model: str, key: str, endpoint: str):
    from openevolve.config import Config, LLMModelConfig
    config = Config()
    config.language = "python"
    config.random_seed = seed
    config.diff_based_evolution = False
    config.database.num_islands = 1
    config.database.population_size = 16
    config.database.archive_size = 8
    config.evaluator.parallel_evaluations = 1
    config.evaluator.max_retries = 0
    config.evaluator.timeout = 600
    config.evaluator.cascade_evaluation = False
    config.evaluator.use_llm_feedback = False
    config.llm.models = [LLMModelConfig(name=model, api_key=key, api_base=endpoint,
                                        max_tokens=1024, retries=0)]
    config.llm.evaluator_models = []
    config.llm.max_tokens = 1024
    config.llm.retries = 0
    config.max_code_length = 64000
    config.prompt.system_message = (
        "Improve a Python TEAM policy for MAgent2 Battle. Return a complete Python "
        "file defining act(observation, agent_id, num_actions) -> int. "
        "Observations are nested 13x13x5 numeric lists; actions 0=wait, "
        "1..12=move, 13..20=attack. Python standard library only. "
        "Return integer 0 <= action < num_actions. Evaluated inside Docker "
        "from both colors on matched seeds. Do not change the function signature."
    )
    return config


def main(argv=None):
    parser = argparse.ArgumentParser(description="Survivevolve M1: OpenEvolve + MAgent2")
    parser.add_argument("--smoke", action="store_true", help="offline Docker+MAgent2 match")
    parser.add_argument("--confirm-live", action="store_true", help="allow potentially billed LLM coevolution")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--cycles", type=int, default=24)
    parser.add_argument("--output", default="out/survivevolve-m1")
    parser.add_argument("--image", default="survivevolve-policy:m1")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if min(args.rounds, args.iterations, args.cycles) < 1:
        parser.error("rounds, iterations and cycles must be positive")
    if args.resume and args.smoke:
        parser.error("cannot resume a smoke match")
    try:
        docker_preflight(args.image)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.error(str(exc))
    if args.smoke:
        scores = run_episode(POLICIES / "red.py", POLICIES / "blue.py",
                             args.seed, cycles=args.cycles,
                             policy_factory=partial(DockerPolicy, image=args.image))
        print(json.dumps({"kind": "real_magent2_docker_smoke", "seed": args.seed,
                          "scores": scores}, indent=2))
        return
    if not args.confirm_live:
        parser.error("live LLM evolution requires --confirm-live; run --smoke first")
    model = os.getenv("SV_MODEL", "").strip()
    key = os.getenv("SV_API_KEY", "").strip()
    endpoint = os.getenv("SV_API_BASE", "https://api.openai.com/v1").strip()
    if not (model and key and endpoint):
        parser.error("explicit SV_MODEL and SV_API_KEY are required")
    from openevolve import Population, run_coevolution
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    evaluation_id = f"magent2-battle-v4-map12-cycles{args.cycles}-matched-v1"
    manifest = {
        "format": "survivevolve.m1.v1", "arena": "magent2.battle_v4",
        "generation": "llm_live", "model": model,
        "endpoint_origin": urlsplit(endpoint).hostname or "",
        "seed": args.seed, "rounds": args.rounds,
        "iterations_per_phase": args.iterations, "cycles": args.cycles,
        "opponent_count": 2, "seeds": [args.seed, args.seed + 12],
        "image": args.image, "evaluation_id": evaluation_id,
        "genomes_sha256": {
            name: hashlib.sha256((POLICIES / f"{name}.py").read_bytes()).hexdigest()
            for name in ("red", "blue")
        },
    }
    path = output / "survivevolve-manifest.json"
    if args.resume:
        if not path.exists() or json.loads(path.read_text()) != manifest:
            parser.error("resume manifest differs or missing")
    elif path.exists():
        parser.error("existing manifest in output; use --resume or a fresh directory")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    result = run_coevolution(
        {name: Population(POLICIES / f"{name}.py",
                          engine_config(args.seed + salt, model=model,
                                        key=key, endpoint=endpoint))
         for name, salt in (("red", 0), ("blue", 100))},
        make_evaluator((args.seed, args.seed + 12), cycles=args.cycles, image=args.image),
        output_dir=str(output), evaluation_id=evaluation_id, rounds=args.rounds,
        iterations_per_phase=args.iterations, opponent_count=2, resume=args.resume,
    )
    print(json.dumps({"completed_phases": result.completed_phases,
                      "checkpoint": result.checkpoint_path,
                      "champions": {
                          k: {"id": v.id, "sha256": hashlib.sha256(v.code.encode()).hexdigest(),
                              "score": v.metrics.get("combined_score")}
                          for k, v in result.champions.items()
                      }}, indent=2))


if __name__ == "__main__":
    main()
