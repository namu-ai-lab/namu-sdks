"""The Namu API for Python: speech recognition, speech synthesis, translation and a voice agent for Hausa, Zarma and
French. https://www.namuai-lab.com

    from namu import Namu

    client = Namu()  # reads NAMU_API_KEY
    audio = client.speech("Sannu da zuwa!", voice="nadia", format="mp3")
"""
from ._client import DEFAULT_BASE_URL, AudioInput, Namu
from ._errors import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NamuError,
    NotFoundError,
    NothingHeardError,
    PayloadTooLargeError,
    PermissionDeniedError,
    QuotaExceededError,
    RateLimitError,
    UnsupportedAudioError,
)
from ._version import __version__

__all__ = [
    "Namu", "AudioInput", "DEFAULT_BASE_URL", "__version__",
    "NamuError", "APIConnectionError", "APITimeoutError", "APIStatusError", "BadRequestError", "AuthenticationError",
    "PermissionDeniedError", "NotFoundError", "PayloadTooLargeError", "UnsupportedAudioError", "NothingHeardError",
    "RateLimitError", "QuotaExceededError", "InternalServerError",
]
