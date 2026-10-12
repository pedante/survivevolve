"""Verify Docker command restrictions before real Docker execution in CI."""
from types import SimpleNamespace
import pytest
from survivevolve.execution.docker_policy import DockerPolicy, PolicyFailure


class FakeProcess:
    def __init__(self, argv, **kwargs):
        self.argv = argv
        self.stdin = SimpleNamespace(fileno=lambda: -1)
        self.stdout = SimpleNamespace(fileno=lambda: -1)
    def poll(self):
        return 0
    def wait(self, **kwargs):
        return 0


def test_docker_flags_prevent_credentials_and_network(tmp_path, monkeypatch):
    import survivevolve.execution.docker_policy as module
    policy = tmp_path / "candidate.py"
    policy.write_text("def act(o, a, n): return 0")
    policy.chmod(0o600)  # Like upstream evaluator NamedTemporaryFile.
    recorded = []
    def fake_popen(args, **kwargs):
        recorded.extend(args)
        return FakeProcess(args)
    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    runner = DockerPolicy(policy, 17)
    assert runner.staged_source.stat().st_mode & 0o004  # readable by uid 65534
    assert runner.staged_source.read_text() == policy.read_text()
    runner.close()
    for required in ("--network", "none", "--read-only", "--cap-drop", "ALL",
                     "--security-opt", "no-new-privileges", "--user", "65534:65534"):
        assert required in recorded
    assert not any("SV_API_KEY" in arg or "OPENAI_API_KEY" in arg for arg in recorded)
    assert "survivevolve-policy:m1" in recorded
    assert any("readonly" in arg and "candidate.py" in arg for arg in recorded)


def test_reject_large_source(tmp_path):
    file = tmp_path / "oversized.py"
    file.write_text("a" * 64001)
    with pytest.raises(PolicyFailure):
        DockerPolicy(file, 0)
