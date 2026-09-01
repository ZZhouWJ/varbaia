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
    )
    assert "server_engine_type=16k_en" in target.url
    assert "secretid=secret-id" in target.url
    assert "private-key" not in target.url
    assert "signature=" in target.url
