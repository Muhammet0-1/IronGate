# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses semantic versioning for its own public interface.

## [Unreleased]

## [0.2.0] - 2026-08-19

### Added

- Installable `irongate_lab` package and `irongate-lab` command.
- Separate simulator, gateway, process, scenario, model, and validation layers.
- Deterministic, socket-free unit tests and a Python 3.10–3.13 CI matrix.
- Project security policy, contribution guide, MIT license, and packaging metadata.
- JSON Lines output for bounded observation runs.

### Changed

- Reframed the proof of concept as a defensive localhost training environment.
- Restricted all endpoints to loopback addresses and unprivileged ports.
- Replaced the autonomous infinite write loop with finite observation by default.
- Required `--apply` plus exact endpoint confirmation before synthetic valve writes.
- Limited the simulated register map and made pressure/alarm registers read-only.
- Pinned PyModbus to the tested 3.11 API line.

### Removed

- Anti-VM checks, attack-oriented messaging, fake telemetry claims, and unused imports.
- Binding the simulator to every network interface.

[Unreleased]: https://github.com/Muhammet0-1/IronGate/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Muhammet0-1/IronGate/releases/tag/v0.2.0
