"""Domain-level exceptions, translated to HTTP status codes in the API layer."""


class ServiceError(Exception):
    """Base class for expected business-rule failures."""


class NotFoundError(ServiceError):
    """A referenced entity does not exist."""


class ConflictError(ServiceError):
    """The operation violates a uniqueness or business invariant."""


class RateUnavailableError(ServiceError):
    """No NBU exchange rate could be resolved within the lookback window."""
