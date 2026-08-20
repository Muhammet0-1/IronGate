# Security Policy

## Supported version

Security fixes are provided for the latest release on the `main` branch.

## Reporting a vulnerability

Please use GitHub's **private vulnerability reporting** or a private security
advisory for this repository. Do not include secrets, sensitive industrial data, or
details from systems you are not authorized to test.

Include:

- the affected version or commit;
- a minimal localhost-only reproduction;
- expected and actual behavior;
- the security impact; and
- a suggested remediation, if available.

Please do not open a public issue until a fix or coordinated disclosure plan exists.

## Scope

In scope are flaws in this repository, including bypasses of its loopback boundary,
confirmation checks, iteration limits, or read-only register policy.

Real ICS/SCADA systems, internet hosts, third-party Modbus devices, and findings that
require testing infrastructure without explicit authorization are out of scope. This
project is a simulator, not a production security control.
