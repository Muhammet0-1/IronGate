"""Backward-compatible entry point for a bounded IronGate Lab scenario."""

from __future__ import annotations

import sys

from irongate_lab.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["scenario", *sys.argv[1:]]))
