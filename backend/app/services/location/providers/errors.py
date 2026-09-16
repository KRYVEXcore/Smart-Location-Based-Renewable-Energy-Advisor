"""Provider error hierarchy.

LocationService catches these and turns them into a ResourceError in the
response instead of letting them fail the whole request or leak as a 500.
"""


class ProviderError(Exception):
    """Base class for all provider failures. `code` maps to schemas.ResourceError.code."""

    code = "unavailable"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProviderNotConfiguredError(ProviderError):
    code = "not_configured"


class ProviderTimeoutError(ProviderError):
    code = "timeout"


class ProviderRateLimitedError(ProviderError):
    code = "rate_limited"


class ProviderAuthenticationError(ProviderError):
    code = "auth_failed"


class ProviderInvalidResponseError(ProviderError):
    code = "invalid_response"
