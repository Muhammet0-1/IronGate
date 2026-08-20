# IronGate Lab

[![CI](https://github.com/Muhammet0-1/IronGate/actions/workflows/ci.yml/badge.svg)](https://github.com/Muhammet0-1/IronGate/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

IronGate Lab is a **localhost-only** Modbus/TCP training environment for studying
basic ICS/SCADA process monitoring, control-state changes, and fail-safe software
design. It contains a synthetic water-pressure process, a small PLC simulator, and
a bounded scenario runner.

The project is intentionally a laboratory tool. It does not discover devices,
target real industrial systems, conceal activity, capture credentials, or implement
malware behavior.

## Project story

The original proof of concept used the IronGate name as a reference to public
research about a 2016 industrial-control malware sample. That early version mixed a
simulator with an autonomous register-writing script and described the demonstration
in attack-oriented terms.

Version 0.2.0 rebuilds the idea as a defensive engineering lab. Connections are
restricted in code to loopback addresses, observation is the default, write mode is
finite and requires an exact endpoint confirmation, and only the synthetic valve
register is writable. Anti-analysis and evasion behavior are deliberately absent.

## Safety boundaries

- Both client and server accept only `localhost`, `127.0.0.0/8`, or `::1`.
- There is no flag that disables the loopback restriction.
- The simulator uses an unprivileged port (`5020` by default).
- `observe` never writes registers.
- `scenario` is observation-only unless `--apply` is supplied.
- Write mode also requires `--confirm-lab-target` to match the exact endpoint.
- Every run has a bounded iteration count (maximum 1,000).
- Only register `1`, the synthetic valve command, accepts writes.
- A valve opened by the runner is closed during cleanup when possible.
- No real network scan, persistence, process injection, anti-VM, or stealth feature
  is included.

These controls reduce accidental misuse; they do not turn Modbus/TCP into a secure
industrial protocol. Never point similar tooling at equipment you do not own and
have explicit permission to test.

## Architecture

```text
irongate-lab scenario/observe
            |
            v
   validated loopback endpoint
            |
            v
   PyModbus gateway ----> localhost Modbus/TCP server
                                    |
                                    v
                           thread-safe register bank
                                    |
                                    v
                         synthetic pressure process
```

The domain model and scenario policy are independent from PyModbus, so almost all
tests run without opening a socket.

## Requirements

- Python 3.10 or newer
- PyModbus 3.11.x (pinned to one minor API line)

## Installation

```bash
git clone https://github.com/Muhammet0-1/IronGate.git
cd IronGate

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

For development tools:

```bash
python -m pip install -e '.[dev]'
```

## Quick start

Start the synthetic PLC in one terminal:

```bash
irongate-lab simulate
```

Read five snapshots from another terminal (no writes):

```bash
irongate-lab observe --iterations 5
```

Run a bounded local write demonstration:

```bash
irongate-lab scenario \
  --iterations 15 \
  --open-below 55 \
  --close-at 65 \
  --apply \
  --confirm-lab-target 127.0.0.1:5020
```

Machine-readable output is available with `--json`:

```bash
irongate-lab observe --iterations 3 --json
```

The legacy filenames remain as safe compatibility shims:

```bash
python plc_sim.py
python irongate.py --iterations 5
```

## Register map

| Address | Name | Access | Values |
| ---: | --- | --- | --- |
| `0` | Pressure | Read only | Synthetic value from `0` to `150` |
| `1` | Valve command | Read/write | `0` closed, `1` open |
| `2` | Alarm | Read only | `0` normal, `1` high pressure |

The map is deliberately small and is not intended to represent any vendor device.

## CLI reference

```bash
irongate-lab --help
irongate-lab simulate --help
irongate-lab observe --help
irongate-lab scenario --help
```

Invalid hosts, privileged ports, non-finite timing values, invalid device IDs, and
unconfirmed writes fail with a clear configuration error.

## Development and verification

```bash
ruff check .
mypy
pytest
python -m build
```

The GitHub Actions matrix runs those checks on Python 3.10, 3.11, 3.12, and 3.13.
Tests use fake transports and deterministic disturbances; they do not connect to
external systems.

## Responsible use

Use this project only as a local educational simulator or as a code-review exercise.
For security concerns about the project itself, see [SECURITY.md](SECURITY.md). For
contribution guidance, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Released under the [MIT License](LICENSE).
