"""Untrusted policy execution endpoint. Run ONLY inside a restricted container."""
import contextlib
import json
import random
import runpy
import sys


def handle(message, act):
    if not isinstance(message, dict) or not isinstance(message.get("batch"), list):
        raise ValueError("expected batch")
    batch = message["batch"]
    if len(batch) > 128:
        raise ValueError("batch too large")
    answers = []
    for item in batch:
        n = item.get("num_actions")
        if type(n) is not int or not (1 <= n <= 128):
            raise ValueError("invalid action count")
        with contextlib.redirect_stdout(sys.stderr):
            action = act(item.get("observation"), item.get("agent_id"), n)
        if type(action) is not int or not (0 <= action < n):
            raise ValueError("invalid policy action")
        answers.append(action)
    return {"actions": answers}


def main():
    random.seed(int(sys.argv[1]))
    # Module execution is intentional and must NEVER happen on the host.
    with contextlib.redirect_stdout(sys.stderr):
        namespace = runpy.run_path("/code/policy.py")
    act = namespace.get("act")
    if not callable(act):
        raise RuntimeError("policy must define act(observation, agent_id, num_actions)")
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if message == {"stop": True}:
                break
            response = handle(message, act)
        except Exception as exc:
            response = {"error": f"policy_error:{type(exc).__name__}"}
        sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
