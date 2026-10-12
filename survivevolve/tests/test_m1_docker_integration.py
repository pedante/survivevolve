"""Real Docker boundary tests: require explicit SV_DOCKER_TEST=1."""
import os
import pytest
from survivevolve.execution.docker_policy import DockerPolicy, PolicyFailure

pytestmark = pytest.mark.skipif(
    os.environ.get("SV_DOCKER_TEST") != "1",
    reason="Real Docker checks require explicit opt-in",
)


def _run(tmp_path, code, *, timeout=5):
    policy = tmp_path / "generated.py"
    policy.write_text(code)
    with DockerPolicy(policy, 17, timeout=timeout) as runner:
        return runner.actions([{"agent_id": "red_0", "observation": [],
                                "num_actions": 21}])


def test_docker_does_not_inherit_provider_key(tmp_path, monkeypatch):
    monkeypatch.setenv("SV_API_KEY", "TOP_SECRET_NOT_FOR_WORKERS")
    assert _run(tmp_path, "import os\ndef act(o,a,n): return 1 if 'SV_API_KEY' in os.environ else 0") == [0]


def test_readonly_candidate_mount(tmp_path):
    source = (
        "def act(o,a,n):\n"
        "    try:\n"
        "        open('/code/policy.py','w').write('changed')\n"
        "    except OSError:\n"
        "        return 0\n"
        "    return 1\n"
    )
    assert _run(tmp_path, source) == [0]


def test_no_network(tmp_path):
    source = (
        "import socket\n"
        "def act(o,a,n):\n"
        "    s=socket.socket()\n"
        "    s.settimeout(1)\n"
        "    try:\n"
        "        s.connect(('1.1.1.1', 53))\n"
        "    except OSError:\n"
        "        return 0\n"
        "    finally:\n"
        "        s.close()\n"
        "    return 1\n"
    )
    assert _run(tmp_path, source) == [0]


def test_looping_policy_times_out(tmp_path):
    with pytest.raises(PolicyFailure):
        _run(tmp_path, "def act(o,a,n):\n    while True: pass\n", timeout=1.5)


def test_invalid_action_is_penalized(tmp_path):
    with pytest.raises(PolicyFailure):
        _run(tmp_path, "def act(o,a,n): return True")
