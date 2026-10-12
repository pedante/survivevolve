#!/usr/bin/env python3
"""Reject edits to upstream-owned files in ordinary Survivevolve pull requests.

Inspect only a PR's changes relative to its base commit (not a moving upstream
branch). Intentional upstream-sync PRs must opt in explicitly.
"""

import argparse
import subprocess
import sys

PROTECTED_PREFIXES = (
    "openevolve/",
    "tests/",
    "examples/",
    "configs/",
    "scripts/",
)
PROTECTED_FILES = (
    "pyproject.toml", "setup.py", "openevolve-run.py", "Makefile",
    "LICENSE", "Dockerfile", "MANIFEST.in", "CLAUDE.md",
    ".github/workflows/claude.yml", ".github/workflows/python-test.yml",
    ".github/workflows/release.yml", ".github/workflows/security-scan.yml",
)
# An intentional new root-level file can be added freely. The protection does
# not apply to *our* docs or package, and intentionally excludes README.md.


def find_protected(paths):
    return [
        path
        for path in paths
        if path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES)
    ]


def changed_files(base):
    result = subprocess.run(
        ["git", "diff", "--no-renames", "--name-only", "--diff-filter=ACDMRT", base, "HEAD", "--"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Commit SHA of PR base")
    parser.add_argument(
        "--allow-upstream-sync",
        action="store_true",
        help="Only for reviewed sync/upstream-* branches; still run tests",
    )
    args = parser.parse_args(argv)
    try:
        protected = find_protected(changed_files(args.base))
    except subprocess.CalledProcessError as error:
        print("Cannot compute protected diff; failing closed:", error.stderr, file=sys.stderr)
        return 2
    if protected and not args.allow_upstream_sync:
        print("Unexpected changes to OpenEvolve-owned paths:", file=sys.stderr)
        for path in protected:
            print(f"  {path}", file=sys.stderr)
        print("Keep fork features in survivevolve/; use a reviewed sync/upstream-* PR to update upstream.", file=sys.stderr)
        return 1
    if protected:
        print("Upstream sync exception used; human review and full compatibility checks required.")
        for path in protected:
            print(f"  {path}")
    else:
        print("Upstream source protection passed: no protected files modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
