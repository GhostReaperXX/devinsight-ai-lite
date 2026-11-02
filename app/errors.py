"""Business errors. They describe what went wrong and know nothing about HTTP."""


class AppError(Exception):
    """Parent of every error the application raises on purpose."""


class NotFoundError(AppError):
    """The thing named in the request does not exist."""


class ConflictError(AppError):
    """The request clashes with the current state, such as a repeated e-mail."""


class RuleViolationError(AppError):
    """The request is well formed but breaks a business rule."""


class PermissionDeniedError(AppError):
    """The user is known, but is not allowed to do this."""


class AuthenticationError(AppError):
    """The user could not be identified."""
