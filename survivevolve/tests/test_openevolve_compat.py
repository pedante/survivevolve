"""Offline compatibility against the checked-out upstream, when installed."""

from unittest.mock import patch

import pytest

from survivevolve.engines.openevolve_compat import verify_public_api


def test_compatibility_probe_reports_missing_symbols():
    class FakeUpstream:
        run_evolution = staticmethod(lambda: None)

    with patch("survivevolve.engines.openevolve_compat.import_module", return_value=FakeUpstream()):
        with pytest.raises(RuntimeError, match="run_coevolution"):
            verify_public_api()


def test_live_openevolve_contract():
    upstream = pytest.importorskip("openevolve")
    verify_public_api()
    # Exact public API names are critical for M1; don't bind to private internals.
    assert callable(upstream.run_evolution)
    assert callable(upstream.run_coevolution)
