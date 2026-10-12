# Keeping Survivevolve up to date with OpenEvolve

The repository is a GitHub fork of
[`algorithmicsuperintelligence/openevolve`](https://github.com/algorithmicsuperintelligence/openevolve).
**The goal is to take upstream fixes frequently without losing Survivevolve code.**

## Ownership rule

New Survivevolve development lives under `survivevolve/` and
`docs/survivevolve/`. Keep upstream-owned files unchanged: `openevolve/`,
`tests/`, `examples/`, `configs/`, `scripts/`, the root `pyproject.toml`,
`setup.py`, and OpenEvolve's original tools. Add new CI workflows rather than
rewriting the original workflows. The **root README.md** is our intentional
exception and may need manual conflict resolution when upstream edits theirs.

## Regular contributor pull requests

CI runs `survivevolve/tools/check_upstream_changes.py` on the diff against the pull
request's base commit. Any change to protected paths fails, by default.
The check is deliberately about **the proposed diff**, not whether the fork's
files equal whatever was most recently published upstream.

## Updating upstream deliberately

In a clean local checkout:

```bash
git remote add upstream https://github.com/algorithmicsuperintelligence/openevolve.git
# If already set, just run `git fetch upstream`.
git fetch upstream main
git switch main
git pull --ff-only origin main
git switch -c sync/upstream-YYYY-MM-DD
git merge --no-edit upstream/main
```

Replace `YYYY-MM-DD` with the actual sync date. Resolve README or other
conflicts carefully; do **not** choose `-X theirs` over the entire tree.
Run upstream's existing tests and our package tests:

```bash
python -m pip install -e '.[dev]'
python -m pip install -e './survivevolve[dev]'
python -m pytest -q survivevolve/tests
python -m pytest -q tests/test_coevolution.py
# Then run a full upstream suite where compute/resources allow:
python -m pytest -q tests/ -m 'not slow'
```

Open a PR against `main` with the `sync/upstream-` branch prefix. Such PRs
explicitly allow changes to upstream paths **only in the guard**, not in tests
or review. Inspect all upstream changes (including dependency/security updates),
verify the original examples still work, and document the upstream SHA in the PR.
Merge only after tests and human inspection. Never force-push `main` and never
use automatic upstream merges without checks.

**Important:** a successful smoke test is not security verification. OpenEvolve
may execute generated candidate Python with host privileges unless the evaluator
is externally sandboxed; M0 does not solve that issue.
