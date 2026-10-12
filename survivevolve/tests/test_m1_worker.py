"""Worker pure-protocol tests (the actual worker runs only in Docker)."""
import pytest
from survivevolve.execution.worker import handle


def test_policy_actions_are_constrained():
    req = {"batch": [{"observation": [], "agent_id": "red_0", "num_actions": 21}]}
    assert handle(req, lambda obs, agent, n: 13) == {"actions": [13]}
    for action in (True, -1, 21, 3.5, "13"):
        with pytest.raises(ValueError):
            handle(req, lambda *args: action)
    with pytest.raises(ValueError):
        handle({"batch": [{}]}, lambda *args: 0)
    with pytest.raises(ValueError):
        handle({"batch": [{}] * 129}, lambda *args: 0)


def test_no_action_policy_must_fail():
    with pytest.raises(ValueError):
        handle({"batch": [{"num_actions": 0}]}, lambda *args: 0)
