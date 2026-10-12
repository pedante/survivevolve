"""A lightweight, offline boundary check; not an evolution adapter yet.

Keep OpenEvolve imports here rather than importing it throughout Survivevolve.
This module validates the *installed* upstream API; M1 will implement an actual
adapter behind `EvolutionEngine`.
"""

from importlib import import_module


REQUIRED_API = ("run_evolution", "run_coevolution", "Population", "Opponent", "Config")


def verify_public_api() -> None:
    """Fail loudly when an OpenEvolve update removes an API M1 plans to use."""
    try:
        upstream = import_module("openevolve")
    except ImportError as exc:
        raise RuntimeError(
            "OpenEvolve is not installed. Install the root checkout with `pip install -e .`"
        ) from exc
    missing = [name for name in REQUIRED_API if not hasattr(upstream, name)]
    if missing:
        raise RuntimeError("Incompatible OpenEvolve public API; missing: " + ", ".join(missing))
