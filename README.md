# Survivevolve

**Code is the genome. Survival is the test.**

Survivevolve is an open-source experiment in artificial life: autonomous software organisms compete for survival while evolving their **own code, prompts, and eventually the mechanisms they use to improve themselves**.

The aim is not to build a realistic simulated world. The world is a source of pressure and feedback. **The experiment is the evolution of the organisms.**

> **Status: early-stage research project.** Survivevolve is being built on top of [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve). The mechanisms described below are the project's goals, not claims that persistent, self-modifying organisms are already working. OpenEvolve's existing code evolution, prompt optimization, archives, and coevolution are the starting point.

## The idea

Imagine several software organisms entering the same arena. Each begins with a strategy, a prompt, a limited budget, and the ability to act.

One organism learns to avoid unnecessary fights. Another experiments with cooperation. A third spends scarce resources asking an LLM to rewrite part of its own strategy. Some changes help; others fail. Organisms that exhaust their resources die. Successful implementations can persist and be inherited.

Eventually, an organism might improve not only **what it does**, but **how it decides what to change**.

The interesting question is not whether an optimizer can find a better game-playing function. It is:

**Can software organisms become better at surviving by choosing, testing, and inheriting changes to their own cognition?**

## Core principles

- **Reuse before reinvention.** Keep OpenEvolve's mature evolutionary machinery. Integrate existing agent frameworks, arenas, sandboxes, and viewers where useful.
- **Code and prompts are evolvable.** Mutations must change actual executable behavior or reasoning instructions, not merely cosmetic parameters.
- **Survival provides selection pressure.** Organisms compete or cooperate in existing environments; elaborate world simulation is not the product.
- **Evolution has a cost.** LLM calls, experiments, time, and computation consume limited budgets. Improving yourself must compete with staying alive.
- **The organism gains agency.** A long-term goal is for organisms to decide whether, when, and how to attempt improvements, rather than relying entirely on an external optimizer.
- **Inheritance matters.** Descendants carry forward versioned code, prompts, and relevant state, with a traceable lineage.
- **Experiments must be honest.** Compare against frozen baselines, evaluate on unseen opponents and environments, and record the cost of failed mutations.
- **Unsafe code stays isolated.** Generated programs never receive unrestricted access to the host, secrets, or the trusted arena referee.

## How an organism should work

An organism has a versioned **genome**—initially a Python strategy and an editable prompt—and an evolving history of encounters.

Its intended life cycle:

1. **Observe:** receive an observation from the arena.
2. **Act:** use its current strategy and, when affordable, reasoning tools.
3. **Pay:** account for actions, computation, and consultations.
4. **Adapt:** decide whether a code or prompt mutation is worth the risk.
5. **Test:** run candidates in isolation and measure them against independent challenges.
6. **Select:** accept useful changes; reject failed experiments without refunding their costs.
7. **Survive, reproduce, or die:** allow the environment and available resources to determine continuation and inheritance.

These are **design targets**. The first experiment will establish the simpler loop—evolving real Python policies against existing opponents—before attempting the complete autonomous life cycle.

## Built on existing projects

| Component | Starting point | Role |
| --- | --- | --- |
| Evolution | [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) | Program mutations, selection, archives, prompt optimization, evolutionary populations, coevolution |
| Arenas | [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) and [MAgent2](https://github.com/Farama-Foundation/MAgent2) | Standard multi-agent interfaces and an initial competitive environment |
| Richer environments, later | [Neural MMO](https://github.com/NeuralMMO/environment) | An optional more complex survival world |
| Recursive self-modification research | [Darwin Gödel Machine](https://github.com/jennyzzt/dgm) | A possible route toward evolving the agent's improvement machinery |
| Live observation research | [OpenEvo](https://github.com/ShumpZeke/OpenEvo) | Candidate source for reusable telemetry and a browser control center |

**One evolutionary authority:** we do not intend to maintain several conflicting mutation, selection, or archive engines. Additional projects are candidates for selective integration, not automatic dependencies.

## Initial experiment

We will start with an existing battle arena and a small population of Python policies.

**The first meaningful success** is not a beautiful simulation or a passing unit test. It is a reproducible run where:

- Multiple policies compete in an existing environment.
- OpenEvolve produces at least one genuine, model-generated code or prompt modification.
- The modification changes subsequent behavior and persists in a versioned descendant.
- The candidate is tested against held-out opponents or seeds.
- Its improvement is measured against frozen strategies **after accounting for evolution costs**.

A working adapter is not proof of evolutionary progress. We will report failures, regressions, and uncertain results as such.

## Planned research directions

1. **Competitive code evolution:** connect OpenEvolve to a reusable arena, compare evolved policies with non-evolving baselines.
2. **Costly cognition:** introduce budgets for LLM calls, testing, computation, and survival.
3. **Organism-controlled adaptation:** let each organism choose when to attempt modifications.
4. **Persistence and inheritance:** track individuals, death, offspring, and the genealogy of code and prompts.
5. **Interchangeable minds and worlds:** test different agent architectures and arenas through stable interfaces.
6. **Live laboratory:** observe the arena, inspect source changes and lineages, alter environmental conditions, and replay experiments alongside fast headless research runs.
7. **Deeper self-improvement:** investigate evolving the processes that generate, evaluate, and select an organism's own changes, while keeping the trusted referee outside organism control.

The order and scope will change according to experimental evidence.

## What Survivevolve is not

- Not a new evolutionary framework invented from scratch.
- Not a detailed virtual civilization simulator.
- Not a claim that language models are conscious or literally alive.
- Not a benchmark leaderboard where an external optimizer gets unlimited free attempts.
- Not a system that grants model-generated code uncontrolled access to the host.

## Security and reproducibility

LLM-generated Python is untrusted input. Candidate execution requires an independently controlled isolation boundary, strict filesystem and network restrictions, no provider credentials, resource limits, and a trusted external evaluator. Containerization alone is not a security guarantee; these controls must be tested.

We intend to save source revisions, prompts, model/provider settings, seeds, opponent versions, resource expenditure, failures, and results. Randomized comparisons should use repeated runs and held-out conditions rather than relying on a single impressive trajectory.

## Getting started

The Survivevolve arena integration is **not yet a verified, end-to-end runnable system**. Until it is, start with the upstream [OpenEvolve installation and examples](https://github.com/algorithmicsuperintelligence/openevolve#-quick-start), including its existing competitive resource-allocation and prompt-optimization examples.

This repository will document a reproducible arena command once the integration passes real execution tests. We will not present planned commands as implemented functionality.

## License and attribution

Survivevolve builds on OpenEvolve, licensed under **Apache License 2.0**, and credits its original authors. Additional components retain their respective licenses. The repository's own license and any third-party notices should be included and verified when the fork is published.

---

**Survive. Adapt. Rewrite yourself.**
