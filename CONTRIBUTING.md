# Contributing

Thank you for helping improve IronGate Lab.

## Ground rules

- Keep all network behavior restricted to loopback addresses.
- Do not add scanning, exploitation, persistence, evasion, credential capture, or
  real industrial-device targeting.
- New register writes must remain explicit, bounded, documented, and covered by
  cleanup tests.
- Never include real operational addresses, credentials, packet captures, or vendor
  configurations in fixtures or documentation.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Before opening a pull request, run:

```bash
ruff check .
mypy
pytest
python -m build
```

## Pull requests

Keep changes focused and explain their safety impact. Add regression tests for bug
fixes and document any user-visible behavior in `CHANGELOG.md`. A pull request must
pass the full Python 3.10–3.13 CI matrix before merge.
