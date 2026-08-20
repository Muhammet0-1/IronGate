"""Project-specific exception hierarchy."""


class IronGateError(Exception):
    """Base class for expected IronGate Lab failures."""


class ConfigurationError(IronGateError):
    """Raised when a requested lab configuration is unsafe or invalid."""


class TransportError(IronGateError):
    """Raised when the local Modbus transport cannot complete an operation."""


class ScenarioError(IronGateError):
    """Raised when a bounded lab scenario cannot finish safely."""
