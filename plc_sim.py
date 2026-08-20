"""Backward-compatible entry point for the localhost PLC simulator."""

from __future__ import annotations

import sys

from irongate_lab.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["simulate", *sys.argv[1:]]))
