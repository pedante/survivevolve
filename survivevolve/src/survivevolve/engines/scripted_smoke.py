"""Offline OpenEvolve integration: scripted proposals, NOT an LLM experiment.

Exercises run_coevolution with actual OpenEvolve, MAgent2 and Docker to expose
API/configuration/integration errors before paid real-model testing.
"""
import argparse
import json
import threading
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from survivevolve.engines.openevolve_battle import (
    POLICIES, docker_preflight, engine_config, make_evaluator,
)

SCRIPTED_CODE = '''import random

def act(observation, agent_id, num_actions):
    # Deliberately simple scripted source rewrite; not produced by an LLM.
    return random.randrange(num_actions)
'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1_000_000:
                self.send_error(413)
                return
            request = json.loads(self.rfile.read(size))
            model = request["model"]
        except (ValueError, KeyError):
            self.send_error(400)
            return
        fence = chr(96) * 3
        data = json.dumps({
            "id": "survivevolve-scripted-m1", "object": "chat.completion", "created": 0,
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant",
                                         "content": f"{fence}python\n{SCRIPTED_CODE}{fence}"},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="output directory; defaults to temporary")
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--image", default="survivevolve-policy:m1")
    args = parser.parse_args(argv)
    if args.cycles < 1:
        parser.error("cycles must be positive")
    docker_preflight(args.image)
    from openevolve import Population, run_coevolution
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix="sv-m1-scripted-") as temporary:
                output = args.output or str(Path(temporary) / "experiment")
                populations = {
                    team: Population(POLICIES / f"{team}.py", engine_config(
                        17 + i, model=team, key="scripted-no-secret",
                        endpoint=f"http://127.0.0.1:{server.server_port}/v1"))
                    for i, team in enumerate(("red", "blue"))
                }
                result = run_coevolution(
                    populations, make_evaluator((17,), cycles=args.cycles, image=args.image),
                    output_dir=output, evaluation_id=f"m1-scripted-cycles{args.cycles}",
                    rounds=1, iterations_per_phase=1, opponent_count=1,
                )
                checkpoint = json.loads(Path(result.checkpoint_path).read_text())
                assert result.completed_phases == 2
                assert len(checkpoint["history"]) == 2
                # A connected controller alone is insufficient: score real,
                # valid sandboxed game play and retain an actual source mutation.
                for team, population in checkpoint["populations"].items():
                    seed = next(p for p in population["programs"]
                                if p["id"] == f"{team}-seed")
                    assert seed["metrics"].get("invalid") == 0.0, (
                        f"{team} seed was not evaluated successfully by MAgent2/Docker"
                    )
                    assert any(p["code"] != seed["code"] for p in population["programs"]), (
                        f"{team} had no stored scripted source mutation"
                    )
                print(json.dumps({
                    "kind": "scripted_not_llm", "completed_phases": 2,
                    "population_sizes": {
                        name: len(p["programs"])
                        for name, p in checkpoint["populations"].items()
                    },
                }, indent=2))
        finally:
            server.shutdown()
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
