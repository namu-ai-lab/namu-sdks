"""Against the real API, only the endpoints and errors that cost nothing: run with NAMU_LIVE=1 pytest -m live."""
import os

import pytest

from namu import AuthenticationError, Namu

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.environ.get("NAMU_LIVE") != "1", reason="set NAMU_LIVE=1")]


def test_voices_and_models():
    c = Namu(api_key="")
    assert {"nadia", "mouhamad", "fr"} <= {v["id"] for v in c.voices()}
    models = {m["id"]: m for m in c.models()}
    assert set(models) == {"speech-recognition", "speech-synthesis", "translation", "voice-agent"}
    assert set(models["speech-recognition"]["languages"]) == {"ha", "dje", "fr"}


def test_unknown_key_is_refused_with_a_request_id():
    with pytest.raises(AuthenticationError) as e:
        Namu(api_key="namu_sk_" + "0" * 43, max_retries=0).speech("Sannu")
    assert e.value.type == "invalid_api_key" and e.value.request_id
