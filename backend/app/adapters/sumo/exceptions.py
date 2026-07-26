"""SUMO adapter exception hierarchy."""


class SumoAdapterError(RuntimeError):
    """Base class for expected SUMO adapter failures."""


class SumoConfigurationError(SumoAdapterError, ValueError):
    """Raised when an experiment cannot be represented safely in SUMO."""


class SumoUnavailableError(SumoAdapterError):
    """Raised when the supported SUMO runtime cannot be located."""


class SumoExecutionError(SumoAdapterError):
    """Raised when a SUMO or TraCI operation fails."""
