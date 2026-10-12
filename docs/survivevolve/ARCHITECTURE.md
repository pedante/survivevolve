# Survivevolve architecture — M0

**Status:** contracts only. No organism runtime, no trained agent, no arena
adapter, no execution sandbox, no self-modification loop yet.

## Core ownership

- **Upstream OpenEvolve** (`openevolve/`, root `examples/`, `tests/`,
  `configs/`, `scripts/`): owns its selection, islands, mutation prompting,
  evaluation coordination, and storage. Do not patch it for Survivevolve.
- **Survivevolve** (`survivevolve/src/survivevolve/`): owns portable contracts,
  future persistent organisms, resource budgets and reproduction rules.
- **Engine adapters**: translate portable genomes/evaluation results to a
  chosen search backend. OpenEvolve is the first candidate. Other evolution
  engines need new adapters, not alterations to organism history.
- **Arena adapters**: map one or more versioned genomes into existing multi-agent
  environments; arena rules and scoring are always outside candidate control.
- **Trusted execution boundary** (M1 prerequisite): untrusted Python must run
  in a constrained external sandbox, not in the referee/evolution/LLM host.
- **Experiment record** (later): engine-neutral event history and exact prompt,
  code, seed, opponent and budget versions, independent of engine checkpoints.

## Current extension contracts

| Contract | File | What it expresses |
| --- | --- | --- |
| `Genome` | `models.py` | Exact code/prompt artifact, optional parent reference |
| `EvolutionEngine.run` | `engines/interface.py` | Bounded batch search, trusted fitness callback |
| `Arena.evaluate` | `arenas/interface.py` | Seeded N-entrant matchup without engine-specific objects |
| `verify_public_api` | `engines/openevolve_compat.py` | Checks installed OpenEvolve offers the expected public API |

M0 protocols are intentionally minimal. They do **not** imply an implemented
adapter. An OpenEvolve `Population` is a search population, not an organism.
OpenEvolve `run_coevolution` currently handles **exactly two evolving
populations in alternating phases**, not N independent persistent organisms.

## Next milestone — M1 acceptance gates

1. Build an OpenEvolve adapter using **public APIs**, not private database hacks.
2. Use an existing arena through a separate trusted evaluator, first with
   frozen baselines; permit N simultaneous entrants independently of the
   two-population evolution scheduler.
3. Execute *all* generated candidate code in an isolated environment with no
   provider credentials, no network, and restricted filesystem/CPU/memory.
4. Prove at least one **model-generated** code edit changes behavior; distinguish
   such runs from OpenEvolve's offline scripted-proposal demo.
5. Report held-out performance, candidate counts, match counts, model usage,
   costs and failure categories. No unmeasured success claims.

## Repository longevity

`survivevolve/` is a separate Python distribution (`pip install -e
./survivevolve`), with no runtime import from OpenEvolve in its contracts.
The upstream-check module is the only M0 place using OpenEvolve imports.
When upstream changes, run both its own suite and our compatibility suite;
when a better backend appears, implement its adapter against these contracts.
If Survivevolve leaves the fork later, extract the separate directory and use
`git filter-repo --subdirectory-filter survivevolve` in a new repository to
preserve the package's commit history (on a clone).

See [UPSTREAM.md](UPSTREAM.md) for the protected-source update process.
