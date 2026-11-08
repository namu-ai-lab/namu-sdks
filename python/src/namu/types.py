"""The shapes of the API's JSON answers, as typed dictionaries. Responses are plain dicts: index them as usual."""
from __future__ import annotations

import sys
from typing import List, Optional

if sys.version_info >= (3, 11):
    from typing import Literal, NotRequired, TypedDict
else:  # pragma: no cover
    from typing_extensions import Literal, NotRequired, TypedDict

__all__ = ["Language", "Voice", "SpeechFormat", "Transcription", "Translation", "ConverseTurn", "Usage", "Model",
           "VoiceInfo"]

Language = Literal["ha", "dje", "fr"]
"""`ha` Hausa, `dje` Zarma, `fr` French."""

Voice = Literal["nadia", "warm", "mouhamad", "fr"]
"""`nadia` (Hausa; `warm` is the same voice), `mouhamad` (Zarma and Hausa), `fr` (French)."""

SpeechFormat = Literal["wav", "mp3", "opus"]


class Transcription(TypedDict):
    model: str
    text: str
    """What was said, in lower case, without punctuation."""
    language: str
    audio_seconds: float
    """The length of the audio sent: what was counted."""


class Translation(TypedDict):
    model: str
    source: str
    target: str
    source_text: str
    """The text sent, or what was heard in the audio."""
    text: str
    """The translation."""
    characters: NotRequired[int]
    """Text requests: the characters translated."""
    audio_seconds: NotRequired[float]
    """Audio requests: the length of the audio sent."""
    audio: NotRequired[Optional[str]]
    """With include_audio: the translation spoken, base64 WAV."""


class ConverseTurn(TypedDict):
    model: str
    persona: str
    session_id: Optional[str]
    heard: str
    """What the person said, as text."""
    reply: str
    """The answer, as text."""
    audio: str
    """The answer spoken, base64 WAV."""
    sample_rate: int
    audio_seconds: float
    """Audio sent plus the reply: what was counted."""


class Usage(TypedDict):
    month_audio_seconds_used: float
    month_audio_seconds_limit: float


class Model(TypedDict):
    id: str
    task: str
    endpoint: str
    scope: str
    languages: List[str]
    status: str
    """`beta` or `research`."""


class VoiceInfo(TypedDict):
    id: str
    languages: List[str]
    language: str
    """The voice's first language."""
    description: str
