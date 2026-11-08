"""The client against a mocked API (responses). Nothing here touches the network."""
import base64
import json

import pytest
import requests
import responses

import namu
from namu import (
    APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, InternalServerError, Namu, NamuError,
    NothingHeardError, PayloadTooLargeError, PermissionDeniedError, QuotaExceededError, RateLimitError,
    UnsupportedAudioError,
)

BASE = "https://api.namuai-lab.com"
KEY = "namu_sk_" + "a" * 43


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(namu._client.time, "sleep", lambda s: None)


@pytest.fixture
def client():
    return Namu(api_key=KEY)


def err(status, type, message="m", request_id="rid"):
    return responses.Response("POST", "", status=status, json={"error": {"type": type, "message": message, "request_id": request_id}})


@responses.activate
def test_speech_sends_json_and_returns_bytes(client):
    responses.post(f"{BASE}/v1/speech", body=b"OggS...", headers={"X-Audio-Seconds": "2.4"}, content_type="audio/ogg")
    audio = client.speech("Fofo! Mate ni go?", voice="mouhamad", language="dje", format="opus")
    assert audio == b"OggS..."
    call = responses.calls[0].request
    assert json.loads(call.body) == {"text": "Fofo! Mate ni go?", "voice": "mouhamad", "format": "opus", "language": "dje"}
    assert call.headers["Authorization"] == f"Bearer {KEY}"
    assert call.headers["User-Agent"] == f"namu-python/{namu.__version__}"


@responses.activate
def test_speech_defaults(client):
    responses.post(f"{BASE}/v1/speech", body=b"RIFF")
    client.speech("Sannu")
    assert json.loads(responses.calls[0].request.body) == {"text": "Sannu", "voice": "nadia", "format": "wav"}


@responses.activate
@pytest.mark.parametrize("make", [lambda p: str(p), lambda p: p, lambda p: p.read_bytes(), lambda p: open(p, "rb")])
def test_transcribe_accepts_paths_bytes_and_files(client, tmp_path, make):
    note = tmp_path / "note.ogg"
    note.write_bytes(b"OggS\x00voice")
    responses.post(f"{BASE}/v1/transcribe", json={"model": "speech-recognition", "text": "sannu", "language": "ha", "audio_seconds": 2.0})
    result = client.transcribe(make(note), language="ha")
    assert result["text"] == "sannu"
    body = responses.calls[0].request.body
    assert b'name="file"' in body and b"OggS\x00voice" in body and b'name="language"' in body


@responses.activate
def test_translate_text_and_audio(client, tmp_path):
    responses.post(f"{BASE}/v1/translate", json={"model": "translation", "source": "ha", "target": "fr", "source_text": "x", "text": "y", "characters": 1})
    out = client.translate("Ina kwana?", source="ha", target="fr")
    assert out["text"] == "y"
    assert json.loads(responses.calls[0].request.body) == {"text": "Ina kwana?", "include_audio": False, "target": "fr", "source": "ha"}

    clip = tmp_path / "q.wav"
    clip.write_bytes(b"RIFF")
    client.translate(audio=clip, target="ha", include_audio=True)
    body = responses.calls[1].request.body
    assert b'name="include_audio"' in body and b"true" in body and b'name="target"' in body


def test_translate_needs_text_or_audio(client):
    with pytest.raises(ValueError):
        client.translate()
    with pytest.raises(ValueError):
        client.translate("x", audio=b"y")


@responses.activate
def test_converse(client):
    wav = base64.b64encode(b"RIFF").decode()
    responses.post(f"{BASE}/v1/converse", json={"model": "voice-agent", "persona": "nadia", "session_id": "s1", "heard": "sannu",
                                                "reply": "Lafiya lau", "audio": wav, "sample_rate": 24000, "audio_seconds": 3.0})
    turn = client.converse(b"RIFF", session_id="s1")
    assert turn["reply"] == "Lafiya lau" and base64.b64decode(turn["audio"]) == b"RIFF"
    assert b'name="session_id"' in responses.calls[0].request.body


@responses.activate
def test_catalogue_needs_no_key():
    responses.get(f"{BASE}/v1/voices", json={"data": [{"id": "nadia", "languages": ["ha"], "language": "ha", "description": "d"}]})
    responses.get(f"{BASE}/v1/models", json={"data": [{"id": "speech-synthesis", "task": "speech", "endpoint": "/v1/speech", "scope": "speech", "languages": ["ha"], "status": "beta"}]})
    keyless = Namu(api_key="")
    assert [v["id"] for v in keyless.voices()] == ["nadia"]
    assert keyless.models()[0]["status"] == "beta"
    assert "Authorization" not in responses.calls[0].request.headers


@responses.activate
def test_usage(client):
    responses.get(f"{BASE}/v1/usage", json={"month_audio_seconds_used": 312.4, "month_audio_seconds_limit": 1800.0})
    assert client.usage()["month_audio_seconds_limit"] == 1800.0


def test_missing_key_raises_before_any_request(monkeypatch):
    monkeypatch.delenv("NAMU_API_KEY", raising=False)
    with pytest.raises(AuthenticationError) as e:
        Namu().speech("x")
    assert e.value.type == "missing_api_key" and e.value.status == 401


def test_environment(monkeypatch):
    monkeypatch.setenv("NAMU_API_KEY", KEY)
    monkeypatch.setenv("NAMU_BASE_URL", "https://example.test/")
    c = Namu()
    assert c.api_key == KEY and c.base_url == "https://example.test"


@responses.activate
@pytest.mark.parametrize("status,type,cls", [
    (400, "unknown_voice", BadRequestError), (401, "invalid_api_key", AuthenticationError),
    (403, "insufficient_scope", PermissionDeniedError), (413, "text_too_long", PayloadTooLargeError),
    (415, "unsupported_audio", UnsupportedAudioError), (422, "nothing_heard", NothingHeardError),
    (429, "quota_exceeded", QuotaExceededError), (500, "internal_error", InternalServerError),
])
def test_errors_map_to_classes_and_are_not_retried(client, status, type, cls):
    responses.post(f"{BASE}/v1/speech", status=status, json={"error": {"type": type, "message": "why", "request_id": "r1"}})
    with pytest.raises(cls) as e:
        client.speech("x")
    assert isinstance(e.value, NamuError)
    assert (e.value.status, e.value.type, e.value.message, e.value.request_id) == (status, type, "why", "r1")
    assert len(responses.calls) == 1  # 4xx and 500 are not retried; quota_exceeded never


@responses.activate
def test_rate_limited_is_retried_after_retry_after(client, monkeypatch):
    slept = []
    monkeypatch.setattr(namu._client.time, "sleep", slept.append)
    responses.post(f"{BASE}/v1/speech", status=429, headers={"Retry-After": "3"}, json={"error": {"type": "rate_limited", "message": "m", "request_id": "r"}})
    responses.post(f"{BASE}/v1/speech", body=b"RIFF")
    assert client.speech("x") == b"RIFF"
    assert slept == [3.0] and len(responses.calls) == 2


@responses.activate
def test_upstream_errors_retry_then_give_up(client):
    for _ in range(4):
        responses.post(f"{BASE}/v1/speech", status=502, json={"error": {"type": "upstream_error", "message": "m", "request_id": "r"}})
    with pytest.raises(InternalServerError):
        client.speech("x")
    assert len(responses.calls) == 4  # first try + 3 retries


@responses.activate
def test_rate_limit_class_hierarchy(client):
    responses.post(f"{BASE}/v1/speech", status=429, json={"error": {"type": "rate_limited", "message": "m", "request_id": "r"}})
    with pytest.raises(RateLimitError) as e:
        Namu(api_key=KEY, max_retries=0).speech("x")
    assert not isinstance(e.value, QuotaExceededError)


@responses.activate
def test_non_json_error_still_has_request_id(client):
    responses.post(f"{BASE}/v1/speech", status=503, body="Service Unavailable", headers={"X-Request-Id": "gw-1"})
    with pytest.raises(InternalServerError) as e:
        Namu(api_key=KEY, max_retries=0).speech("x")
    assert e.value.type == "http_error" and e.value.request_id == "gw-1"


@responses.activate
def test_network_errors(client):
    responses.post(f"{BASE}/v1/speech", body=requests.ConnectionError("down"))
    with pytest.raises(APIConnectionError):
        Namu(api_key=KEY, max_retries=1).speech("x")
    assert len(responses.calls) == 2
    responses.reset()
    responses.post(f"{BASE}/v1/speech", body=requests.Timeout("slow"))
    with pytest.raises(APITimeoutError):
        Namu(api_key=KEY, max_retries=0).speech("x")


def test_context_manager_closes_its_session():
    with Namu(api_key=KEY) as c:
        assert repr(c) == "Namu(base_url='https://api.namuai-lab.com')"
