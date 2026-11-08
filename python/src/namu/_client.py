from __future__ import annotations

import os
import random
import time
from typing import Any, BinaryIO, Dict, List, Optional, Union, cast

import requests

from ._errors import APIConnectionError, APITimeoutError, AuthenticationError, error_for
from ._version import __version__
from .types import ConverseTurn, Language, Model, SpeechFormat, Transcription, Translation, Usage, Voice, VoiceInfo

__all__ = ["Namu", "AudioInput", "DEFAULT_BASE_URL"]

DEFAULT_BASE_URL = "https://api.namuai-lab.com"
AudioInput = Union[str, "os.PathLike[str]", bytes, bytearray, BinaryIO]
"""A path to an audio file, its bytes, or an open binary file. Any of WAV, MP3, M4A/AAC, OGG/Opus, WebM or FLAC."""

_RETRY_STATUSES = frozenset({429, 502, 503, 504})


class Namu:
    """A client for the Namu API: speech recognition, speech synthesis, translation and a voice agent for Hausa,
    Zarma and French.

        from namu import Namu

        client = Namu()                 # reads NAMU_API_KEY
        audio = client.speech("Sannu da zuwa!", voice="nadia", format="mp3")

    Keep it on your server: the key must never reach a phone or a browser.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 300.0,
        max_retries: int = 3,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        :param api_key: your secret key (`namu_sk_...`). Defaults to the `NAMU_API_KEY` environment variable.
        :param base_url: defaults to `NAMU_BASE_URL`, then https://api.namuai-lab.com.
        :param timeout: seconds to wait for an answer. Generous by default: a model waking up after a quiet spell can
            take a minute or more.
        :param max_retries: how many times to retry network errors, `429 rate_limited` and `502`/`503`/`504`, with a
            growing pause (or the `Retry-After` the API sends). `quota_exceeded` and other 4xx are never retried.
        :param session: a `requests.Session` to reuse (proxies, adapters, connection pooling).
        """
        self.api_key = api_key if api_key is not None else os.environ.get("NAMU_API_KEY")
        self.base_url = (base_url or os.environ.get("NAMU_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self._session = session or requests.Session()
        self._owns_session = session is None

    # ---- text to speech -------------------------------------------------------------------------------------------
    def speech(self, text: str, *, voice: Union[Voice, str] = "nadia", language: Optional[Union[Language, str]] = None,
               format: Union[SpeechFormat, str] = "wav") -> bytes:
        """Speak `text` (up to 2,000 characters). Returns the audio: WAV (24 kHz mono, default), MP3 or Ogg Opus.

        `language` defaults to the voice's first language and must be one the voice speaks.
        """
        body: Dict[str, Any] = {"text": text, "voice": voice, "format": format}
        if language:
            body["language"] = language
        return self._request("POST", "/v1/speech", json=body).content

    # ---- speech to text -------------------------------------------------------------------------------------------
    def transcribe(self, audio: AudioInput, *, language: Union[Language, str] = "ha") -> Transcription:
        """Write down what was said in `audio` (up to 25 MB and 5 minutes). `language` is not detected: send the
        language you expect."""
        response = self._request("POST", "/v1/transcribe", files=_file(audio), data={"language": language})
        return cast(Transcription, response.json())

    # ---- translation ----------------------------------------------------------------------------------------------
    def translate(self, text: Optional[str] = None, *, audio: Optional[AudioInput] = None, target: str = "fr",
                  source: Optional[str] = None, include_audio: bool = False) -> Translation:
        """Translate Hausa ⇄ French, from `text` (up to 2,000 characters) or from `audio`.

        `source` defaults to the other language from `target`. With `include_audio`, the answer's `audio` field holds
        the translation spoken, as base64 WAV.
        """
        if (text is None) == (audio is None):
            raise ValueError("Give either text or audio.")
        fields: Dict[str, Any] = {"target": target}
        if source:
            fields["source"] = source
        if text is not None:
            response = self._request("POST", "/v1/translate", json={"text": text, "include_audio": include_audio, **fields})
        else:
            if include_audio:
                fields["include_audio"] = "true"
            response = self._request("POST", "/v1/translate", files=_file(cast(AudioInput, audio)), data=fields)
        return cast(Translation, response.json())

    # ---- voice agent (research preview) ---------------------------------------------------------------------------
    def converse(self, audio: AudioInput, *, session_id: Optional[str] = None, persona: str = "nadia") -> ConverseTurn:
        """One turn with the voice agent, in Hausa. The key needs the `converse` scope. The answer's `audio` is the
        reply spoken, base64 WAV. Each turn stands alone: the API keeps no conversation."""
        fields: Dict[str, Any] = {"persona": persona}
        if session_id:
            fields["session_id"] = session_id
        return cast(ConverseTurn, self._request("POST", "/v1/converse", files=_file(audio), data=fields).json())

    # ---- account and catalogue ------------------------------------------------------------------------------------
    def usage(self) -> Usage:
        """Audio seconds used this calendar month (UTC) and the allowance. Free: counts nothing."""
        return cast(Usage, self._request("GET", "/v1/usage").json())

    def voices(self) -> List[VoiceInfo]:
        """The voices `speech` can use. No key needed."""
        return cast(List[VoiceInfo], self._request("GET", "/v1/voices", auth=False).json()["data"])

    def models(self) -> List[Model]:
        """The models, their endpoints, languages and status. No key needed."""
        return cast(List[Model], self._request("GET", "/v1/models", auth=False).json()["data"])

    # ---- lifecycle ------------------------------------------------------------------------------------------------
    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> "Namu":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Namu(base_url={self.base_url!r})"

    # ---- plumbing -------------------------------------------------------------------------------------------------
    def _request(self, method: str, path: str, *, auth: bool = True, **kwargs: Any) -> requests.Response:
        headers = {"User-Agent": f"namu-python/{__version__}", "Accept": "application/json"}
        if auth:
            if not self.api_key:
                raise AuthenticationError("Set NAMU_API_KEY or pass api_key=.", status=401, type="missing_api_key")
            headers["Authorization"] = f"Bearer {self.api_key}"
        attempt = 0
        while True:
            try:
                response = self._session.request(method, self.base_url + path, headers=headers, timeout=self.timeout,
                                                 **kwargs)
            except requests.Timeout as e:
                error: Exception = APITimeoutError(f"No answer within {self.timeout:g} s.")
                cause: Exception = e
            except requests.RequestException as e:
                error, cause = APIConnectionError(f"Could not reach the Namu API: {e.__class__.__name__}."), e
            else:
                if response.ok:
                    return response
                error = _api_error(response)
                cause = None  # type: ignore[assignment]
                retryable = response.status_code in _RETRY_STATUSES and getattr(error, "type", "") != "quota_exceeded"
                if not retryable or attempt >= self.max_retries:
                    raise error
                time.sleep(_delay(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue
            if attempt >= self.max_retries:
                raise error from cause
            time.sleep(_delay(attempt, None))
            attempt += 1


def _file(audio: AudioInput) -> Dict[str, Any]:
    if isinstance(audio, (str, os.PathLike)):
        with open(audio, "rb") as f:
            return {"file": (os.path.basename(os.fspath(audio)), f.read())}
    if isinstance(audio, (bytes, bytearray)):
        return {"file": ("audio", bytes(audio))}
    return {"file": (os.path.basename(str(getattr(audio, "name", "audio"))), audio.read())}


def _delay(attempt: int, retry_after: Optional[str]) -> float:
    if retry_after:
        try:
            return max(0.0, min(float(retry_after), 60.0))
        except ValueError:
            pass
    return min(2.0 ** attempt, 16.0) * (0.75 + random.random() / 2)  # 1, 2, 4 … seconds, with jitter


def _api_error(response: requests.Response) -> Exception:
    request_id = response.headers.get("X-Request-Id")
    try:
        body = response.json()["error"]
        return error_for(response.status_code, str(body.get("type") or "http_error"), str(body.get("message") or ""),
                         body.get("request_id") or request_id)
    except (ValueError, KeyError, TypeError, AttributeError):
        return error_for(response.status_code, "http_error", response.text[:200], request_id)
