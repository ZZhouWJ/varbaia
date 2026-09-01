import base64
import hashlib
import hmac
from urllib.parse import parse_qs, quote, urlencode, urlparse

from app.core.config import Settings
from app.providers.tencent_soe_n import signed_soe_n_handshake_target, soe_n_handshake_target


def test_soe_n_uses_account_app_id_and_english_engine() -> None:
    target = soe_n_handshake_target(Settings(tencentcloud_app_id="123456"))
    assert target.url == "wss://soe.cloud.tencent.com/soe/api/123456"
    assert target.server_engine_type == "16k_en"


def test_soe_n_requires_account_app_id() -> None:
    try:
        soe_n_handshake_target(Settings(_env_file=None))
    except RuntimeError as exc:
        assert "TENCENTCLOUD_APP_ID" in str(exc)
    else:
        raise AssertionError("expected account AppID validation")


def test_soe_n_signing_keeps_english_engine_and_hides_secret_key() -> None:
    target = signed_soe_n_handshake_target(
        Settings(
            _env_file=None,
            tencentcloud_app_id="123456",
            tencentcloud_secret_id="secret-id",
            tencentcloud_secret_key="private-key",
        ),
        timestamp=100,
        nonce=9,
        voice_id="voice-123",
    )
    assert "server_engine_type=16k_en" in target.url
    assert "secretid=secret-id" in target.url
    assert "private-key" not in target.url
    assert "signature=" in target.url
    assert "voice_id=voice-123" in target.url
    assert target.voice_id == "voice-123"
    params = dict(target.signature_params)
    assert params["eval_mode"] == "1"
    assert params["ref_text"] == "hello world"
    assert params["score_coeff"] == "1.0"
    assert params["voice_format"] == "0"
    assert params["rec_mode"] == "0"
    assert params["sentence_info_enabled"] == "0"
    assert params["text_mode"] == "0"
    url_params = parse_qs(urlparse(target.url).query, keep_blank_values=True)
    assert {key: value for key, value in url_params.items() if key != "signature"} == {
        key: [value] for key, value in target.signature_params
    }
    assert not target.signing_text.startswith("wss://")
    assert not target.signing_text.startswith("GET")
    assert "ref_text=hello world" in target.signing_text
    assert "ref_text=hello%20world" not in target.signing_text
    assert "appid=" not in target.url
    assert "/soe/api/123456?" in target.url


def test_soe_n_creates_unique_nonempty_voice_id_for_each_connection() -> None:
    settings = Settings(
        _env_file=None,
        tencentcloud_app_id="123456",
        tencentcloud_secret_id="secret-id",
        tencentcloud_secret_key="private-key",
    )
    first = signed_soe_n_handshake_target(settings, timestamp=100)
    second = signed_soe_n_handshake_target(settings, timestamp=100)
    assert first.voice_id and second.voice_id
    assert first.voice_id != second.voice_id
    assert len(first.voice_id) <= 128
    assert f"voice_id={first.voice_id}" in first.url


def test_soe_n_rejects_overlong_voice_id() -> None:
    settings = Settings(
        _env_file=None,
        tencentcloud_app_id="123456",
        tencentcloud_secret_id="secret-id",
        tencentcloud_secret_key="private-key",
    )
    try:
        signed_soe_n_handshake_target(settings, voice_id="x" * 129)
    except ValueError as exc:
        assert "128" in str(exc)
    else:
        raise AssertionError("expected voice_id length validation")


def test_soe_n_matches_independent_official_sdk_reference() -> None:
    settings = Settings(
        _env_file=None,
        tencentcloud_app_id="fake-app",
        tencentcloud_secret_id="fake-secret-id",
        tencentcloud_secret_key="fake-secret-key",
    )
    target = signed_soe_n_handshake_target(
        settings, timestamp=100, nonce=9, voice_id="fixed-voice-id"
    )
    # Independent line-by-line reproduction of Tencent's published SDK algorithm.
    params = dict(target.signature_params)
    ordered = tuple(sorted(params.items()))
    raw_query = "&".join(f"{key}={value}" for key, value in ordered)
    reference_signing_text = f"soe.cloud.tencent.com/soe/api/fake-app?{raw_query}"
    reference_signature = base64.b64encode(
        hmac.new(b"fake-secret-key", reference_signing_text.encode(), hashlib.sha1).digest()
    ).decode()
    reference_url = (
        "wss://soe.cloud.tencent.com/soe/api/fake-app?"
        f"{urlencode(ordered)}&signature={quote(reference_signature, safe='')}"
    )
    assert target.signing_text == reference_signing_text
    assert target.signature == reference_signature
    assert target.url == reference_url
