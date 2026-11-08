"""Errors raised by the Namu client.

Every error is a `NamuError`. Errors the API answered carry its stable `type` (branch on it), the HTTP `status`, a
`message` written for developers, and the `request_id` to send Namu when asking about a request.

    NamuError
    ├── APIConnectionError        the request did not reach the API, or no answer came back
    │   └── APITimeoutError       no answer within the client's timeout
    └── APIStatusError            the API answered with an error status
        ├── BadRequestError           400  invalid_request, missing_text, unknown_voice, unsupported_language, ...
        ├── AuthenticationError       401  missing_api_key, invalid_api_key, key_revoked
        ├── PermissionDeniedError     403  insufficient_scope, account_paused
        ├── NotFoundError             404
        ├── PayloadTooLargeError      413  payload_too_large, audio_too_long, text_too_long
        ├── UnsupportedAudioError     415  unsupported_audio
        ├── NothingHeardError         422  nothing_heard
        ├── RateLimitError            429  rate_limited
        │   └── QuotaExceededError    429  quota_exceeded (the month's allowance is used; not retried)
        └── InternalServerError       5xx  internal_error, upstream_error, upstream_timeout, ...
"""
from __future__ import annotations

from typing import Optional

__all__ = [
    "NamuError", "APIConnectionError", "APITimeoutError", "APIStatusError", "BadRequestError", "AuthenticationError",
    "PermissionDeniedError", "NotFoundError", "PayloadTooLargeError", "UnsupportedAudioError", "NothingHeardError",
    "RateLimitError", "QuotaExceededError", "InternalServerError",
]


class NamuError(Exception):
    """Base class for every error this package raises."""

    def __init__(self, message: str, *, status: Optional[int] = None, type: Optional[str] = None,
                 request_id: Optional[str] = None) -> None:
        self.message = message
        self.status = status
        self.type = type
        self.request_id = request_id
        prefix = " ".join(str(x) for x in (status, type) if x is not None)
        super().__init__(f"{prefix}: {message}" + (f" (request {request_id})" if request_id else "") if prefix else message)


class APIConnectionError(NamuError):
    """The request did not reach the API, or the connection broke before an answer came back."""


class APITimeoutError(APIConnectionError):
    """No answer within the client's timeout."""


class APIStatusError(NamuError):
    """The API answered with an error status. `type` is the stable code from the error body."""

    status: int
    type: str


class BadRequestError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class PermissionDeniedError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class PayloadTooLargeError(APIStatusError):
    pass


class UnsupportedAudioError(APIStatusError):
    pass


class NothingHeardError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    pass


class QuotaExceededError(RateLimitError):
    pass


class InternalServerError(APIStatusError):
    pass


_BY_STATUS = {400: BadRequestError, 401: AuthenticationError, 403: PermissionDeniedError, 404: NotFoundError,
              413: PayloadTooLargeError, 415: UnsupportedAudioError, 422: NothingHeardError, 429: RateLimitError}


def error_for(status: int, type: str, message: str, request_id: Optional[str]) -> APIStatusError:
    """The most specific error class for an API answer."""
    if status == 429 and type == "quota_exceeded":
        cls: type[APIStatusError] = QuotaExceededError
    elif status >= 500:
        cls = InternalServerError
    else:
        cls = _BY_STATUS.get(status, APIStatusError)
    return cls(message, status=status, type=type, request_id=request_id)
