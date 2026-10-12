# Survivevolve core package (M0)

This is the **independently installable** Survivevolve Python package. It deliberately
contains no copy of OpenEvolve's evolution algorithm, no arena simulation, and no
candidate-code executor. At M0 it defines only engine-neutral data structures and
extension interfaces. The protocols are **not yet an implemented evolution loop**.

From the GitHub repository root:

```bash
python -m pip install -e './survivevolve[dev]'
python -m pytest -q survivevolve/tests
```

To check the actual fork's OpenEvolve API too, first install the upstream package
from the **same checkout** (not a second, unrelated PyPI version):

```bash
python -m pip install -e .
python -m pytest -q survivevolve/tests
```

The separate directory may eventually move to a different repository with its
history intact, or depend on an upgraded/different evolutionary backend. The
source under the root `openevolve/` stays owned by upstream.

See [`../docs/survivevolve/ARCHITECTURE.md`](../docs/survivevolve/ARCHITECTURE.md)
for the boundaries and [`../docs/survivevolve/UPSTREAM.md`](../docs/survivevolve/UPSTREAM.md)
for the update process.
