# Survivevolve — instructions for coding agents

Project goal: evolve persistent software organisms' editable code and prompts
under survival constraints, without simulating an elaborate fake world.

## First read

- [`README.md`](README.md) — project purpose and claims vs planned milestones
- [`docs/survivevolve/ARCHITECTURE.md`](docs/survivevolve/ARCHITECTURE.md)
- [`docs/survivevolve/UPSTREAM.md`](docs/survivevolve/UPSTREAM.md)

## Ownership: reuse before rebuilding

This repository is a fork of `algorithmicsuperintelligence/openevolve`.
**Ordinary development MUST NOT edit** upstream-owned `openevolve/`, `tests/`,
`examples/`, `configs/`, `scripts/`, root packaging or existing workflows.
Put all new Survivevolve runtime and tests inside `survivevolve/` and design
notes under `docs/survivevolve/`. Upstream syncs are special reviewed PRs.
Do not implement another evolutionary search/selection/archive engine; use the
public OpenEvolve API behind an adapter. Do not confuse OpenEvolve's two
alternating *populations* with independent living organisms.

## Scientific and safety rules

- No claims of real learning/evolution without reproducible real runs.
- Distinguish scripted proposals from actual LLM-generated source mutations.
- Treat **all generated code as untrusted**. Never execute it in-process with
  provider keys or the referee's permissions. A proper isolation layer is a
  prerequisite before M1 executes such code.
- Persist exact source, prompts, seeds, environment versions, failure cases and
  resource costs once experiment storage is implemented.
- Keep `survivevolve` package importable without OpenEvolve or MAgent2 installed;
  dependencies belong in adapters.

## Validate changes

```bash
python -m pip install -e '.[dev]'
python -m pip install -e './survivevolve[dev]'
python -m pytest -q survivevolve/tests
python -m pytest -q tests/test_coevolution.py
```

For upstream ownership checks, see `survivevolve/tools/check_upstream_changes.py`.
Open a PR rather than automatically merging feature work into main.
