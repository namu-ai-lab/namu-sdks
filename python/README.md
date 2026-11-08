# Namu API for Python

Speech recognition, speech synthesis, translation and a voice agent for **Hausa, Zarma and French**, from Python.

```bash
pip install namu-ai
```

```python
from namu import Namu

client = Namu()  # reads NAMU_API_KEY

audio = client.speech("Sannu da zuwa! Muna farin cikin jin muryarku.", voice="nadia", format="mp3")
open("welcome.mp3", "wb").write(audio)

print(client.transcribe("welcome.mp3", language="ha")["text"])
```

Get a key at [namuai-lab.com/account/keys](https://www.namuai-lab.com/account/keys) and keep it on your server: never in
a mobile app or a web page. During the beta every account gets 30 minutes of audio a month, free.

## Usage

```python
# Text to speech: Hausa (nadia), Zarma and Hausa (mouhamad), French (fr); wav, mp3 or opus
audio = client.speech("Fofo! Mate ni go?", voice="mouhamad", language="dje", format="opus")

# Speech to text: a path, bytes or an open file; ha, dje or fr (not detected: say which)
result = client.transcribe("voice-note.ogg", language="ha")

# Translation, Hausa ⇄ French, from text or speech, optionally spoken back (base64 WAV)
fr = client.translate("Ina kwana? Yau za a yi zafi sosai.", source="ha", target="fr")
spoken = client.translate(audio="question.ogg", source="ha", target="fr", include_audio=True)

# Voice agent (research preview; the key needs the converse scope)
turn = client.converse("hello.ogg", session_id="demo-42")

# Account and catalogue
client.usage()    # {'month_audio_seconds_used': 312.4, 'month_audio_seconds_limit': 1800.0}
client.voices()   # no key needed
client.models()
```

Responses are plain dictionaries, typed with `TypedDict` (`namu.types`) for your editor.

## Errors

Every error is a `NamuError`. Errors the API answered carry its stable `type`, the HTTP `status`, a `message` and the
`request_id` to send Namu.

```python
from namu import Namu, NamuError, QuotaExceededError, BadRequestError

try:
    audio = client.speech(text)
except QuotaExceededError:
    ...                      # this month's allowance is used
except BadRequestError as e:
    print(e.type, e.message) # unknown_voice, unsupported_language, missing_text, ...
except NamuError as e:
    print(e.status, e.type, e.request_id)
```

| Class | Status | `type` |
| --- | --- | --- |
| `BadRequestError` | 400 | `invalid_request`, `invalid_json`, `missing_text`, `missing_file`, `empty_audio`, `unknown_voice`, `unsupported_language`, `unsupported_pair`, `unknown_persona` |
| `AuthenticationError` | 401 | `missing_api_key`, `invalid_api_key`, `key_revoked` |
| `PermissionDeniedError` | 403 | `insufficient_scope`, `account_paused` |
| `PayloadTooLargeError` | 413 | `payload_too_large`, `audio_too_long`, `text_too_long` |
| `UnsupportedAudioError` | 415 | `unsupported_audio` |
| `NothingHeardError` | 422 | `nothing_heard` |
| `RateLimitError` / `QuotaExceededError` | 429 | `rate_limited` / `quota_exceeded` |
| `InternalServerError` | 5xx | `internal_error`, `upstream_error`, `upstream_timeout`, ... |
| `APIConnectionError` / `APITimeoutError` | none | the API could not be reached, or did not answer in time |

## Retries and timeouts

Network errors, `429 rate_limited` and `502`/`503`/`504` are retried up to 3 times, after `Retry-After` or 1, 2, 4
seconds (with jitter). `quota_exceeded` and other 4xx never are. The default timeout is 300 seconds: the first request
after a quiet spell can take a minute while a model wakes up.

```python
client = Namu(timeout=120, max_retries=5)
```

## Configuration

| Argument | Environment | Default |
| --- | --- | --- |
| `api_key` | `NAMU_API_KEY` | none |
| `base_url` | `NAMU_BASE_URL` | `https://api.namuai-lab.com` |
| `timeout` | | 300 seconds |
| `max_retries` | | 3 |
| `session` | | a new `requests.Session` |

## Data

Speech to text and text to speech run on Namu's own models. Translation and the voice agent's replies are written by
Google Gemini through OpenRouter, which receives the text they work on. Namu keeps usage records, not your audio or
text.

## Development

```bash
pip install -e ".[dev]"
pytest                        # mocked, no network
NAMU_LIVE=1 pytest -m live    # the free endpoints of the real API
```

Requires Python 3.9+. Licensed under Apache 2.0.
