"""The upstream protection guard must fail closed on accidental upstream edits."""

import importlib.util
from pathlib import Path


def _guard():
    # Load as a regular module without adding tools/ to package paths.
    path = Path(__file__).resolve().parents[1] / "tools" / "check_upstream_changes.py"
    spec = importlib.util.spec_from_file_location("survivevolve_source_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protected_paths():
    check = _guard().find_protected
    changed = [
        "openevolve/api.py", "tests/test_api.py", "examples/demo.py", "scripts/run.py",
        "configs/default_config.yaml", "pyproject.toml", "setup.py",
        "survivevolve/src/survivevolve/models.py", "survivevolve/tests/test_contracts.py",
        "docs/survivevolve/UPSTREAM.md", ".github/workflows/survivevolve.yml", "README.md",
    ]
    assert check(changed) == changed[:7]


def test_guard_does_not_exempt_renamed_upstream_files():
    check = _guard().find_protected
    assert check(["openevolve/renamed.py", "tests/renamed.py"])


def test_real_git_diff_detects_renamed_upstream_source(tmp_path):
    """Treat moved upstream code as delete+add, not an allowed new feature."""
    import subprocess

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            check=True, text=True, capture_output=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.email", "survivevolve-test@example.invalid")
    git("config", "user.name", "Survivevolve Test")
    (tmp_path / "openevolve").mkdir()
    (tmp_path / "openevolve" / "engine.py").write_text("UPSTREAM = True\n")
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    (tmp_path / "survivevolve").mkdir()
    (tmp_path / "openevolve" / "engine.py").rename(tmp_path / "survivevolve" / "stolen.py")
    git("add", "-A")
    git("commit", "-qm", "move upstream engine")
    from unittest.mock import patch

    guard = _guard()
    with patch.object(guard.subprocess, "run", wraps=guard.subprocess.run) as wrapped:
        # changed_files uses cwd of the calling process, so temporarily run there.
        import os
        current = Path.cwd()
        try:
            os.chdir(tmp_path)
            changed = guard.changed_files(base)
        finally:
            os.chdir(current)
        assert wrapped.called
    assert "openevolve/engine.py" in changed
    assert "survivevolve/stolen.py" in changed
    assert guard.find_protected(changed) == ["openevolve/engine.py"]
