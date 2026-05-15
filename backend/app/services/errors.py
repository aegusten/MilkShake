"""Service-layer exceptions.

Services are HTTP-agnostic. They raise these domain errors; a FastAPI
exception handler in ``app.main`` translates each one to the correct HTTP
status. This keeps services usable from CLI scripts, background workers, and
tests without dragging in FastAPI.
"""


class ServiceError(Exception):
    """Base class for all service-layer errors."""


class NotFoundError(ServiceError):
    """A requested entity does not exist. Maps to HTTP 404."""


class ConflictError(ServiceError):
    """The operation violates a uniqueness or state constraint. Maps to 409."""


class InvalidInputError(ServiceError):
    """Input fails a business rule (beyond Pydantic schema). Maps to 400."""


class UnauthorizedError(ServiceError):
    """Authentication failed (bad creds, bad/missing token). Maps to 401."""


class ForbiddenError(ServiceError):
    """Authenticated but not allowed (disabled account, etc). Maps to 403."""
