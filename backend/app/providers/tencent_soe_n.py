"""Tencent SOE-N WebSocket adapter boundary.

SOE-N uses the account-level ``TENCENTCLOUD_APP_ID`` and never uses the
legacy HTTP assessment service. The adapter is isolated so the WebSocket
signing procedure can be verified before live traffic is sent.
"""

import asyncio
import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from urllib.parse import quote
from uuid import uuid4

import websockets

from app.core.config import Settings

SOE_N_HOST = "soe.cloud.tencent.com"


@dataclass(frozen=True)
class SoeNHandshakeTarget:
    url: str
    server_engine_type: str
    voice_id: str | None = None
    signature_params: tuple[tuple[str, str], ...] = ()
    signing_text: str = ""
    signature: str = ""


def soe_n_handshake_target(settings: Settings) -> SoeNHandshakeTarget:
    """Create the unsigned SOE-N endpoint; signing is never delegated to SOE-B."""
    if not settings.tencentcloud_app_id:
        raise RuntimeError("未配置 TENCENTCLOUD_APP_ID，无法连接 SOE-N。")
    app_id = quote(settings.tencentcloud_app_id, safe="")
    return SoeNHandshakeTarget(
        url=f"wss://{SOE_N_HOST}/soe/api/{app_id}", server_engine_type="16k_en"
    )


def signed_soe_n_handshake_target(
    settings: Settings,
    *,
    timestamp: int | None = None,
    nonce: int | None = None,
    voice_id: str | None = None,
) -> SoeNHandshakeTarget:
    """Build the SOE-N HMAC-SHA1 signed WebSocket handshake URL."""
    target = soe_n_handshake_target(settings)
    if not settings.tencentcloud_secret_id or not settings.tencentcloud_secret_key:
        raise RuntimeError("未配置腾讯云密钥，无法签名 SOE-N WebSocket 请求。")
    now = int(time.time()) if timestamp is None else timestamp
    current_nonce = now if nonce is None else nonce
    if current_nonce <= 0 or len(str(current_nonce)) > 10:
        raise ValueError("SOE-N nonce 必须是最长 10 位的正整数。")
    current_voice_id = voice_id or str(uuid4())
    if not current_voice_id or len(current_voice_id) > 128:
        raise ValueError("SOE-N voice_id 必须为 1 到 128 个字符。")
    params = {
        "eval_mode": "1",
        "expired": str(now + 3600),
        "keyword": "",
        "nonce": str(current_nonce),
        "rec_mode": "0",
        "ref_text": "hello world",
        "score_coeff": "1.0",
        "secretid": settings.tencentcloud_secret_id,
        "server_engine_type": target.server_engine_type,
        "sentence_info_enabled": "0",
        "text_mode": "0",
        "timestamp": str(now),
        "voice_format": "0",
        "voice_id": current_voice_id,
    }
    signature_params = tuple(sorted(params.items()))
    raw_query = "&".join(f"{key}={value}" for key, value in signature_params)
    query = "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in signature_params
    )
    path = target.url.removeprefix(f"wss://{SOE_N_HOST}")
    signing_text = f"{SOE_N_HOST}{path}?{raw_query}"
    signature = base64.b64encode(
        hmac.new(
            settings.tencentcloud_secret_key.encode(), signing_text.encode(), hashlib.sha1
        ).digest()
    ).decode()
    return SoeNHandshakeTarget(
        url=f"{target.url}?{query}&signature={quote(signature, safe='')}",
        server_engine_type=target.server_engine_type,
        voice_id=current_voice_id,
        signature_params=signature_params,
        signing_text=signing_text,
        signature=signature,
    )


def signed_soe_n_assessment_target(
    settings: Settings,
    reference_text: str,
    *,
    timestamp: int | None = None,
    nonce: int | None = None,
    voice_id: str | None = None,
) -> SoeNHandshakeTarget:
    """Create a signed SOE-N English sentence-assessment target.

    This intentionally follows the already verified handshake signer byte for
    byte.  It only substitutes the per-assessment reference text and voice id;
    ``signed_soe_n_handshake_target`` remains the stable health-check builder.
    """
    target = soe_n_handshake_target(settings)
    if not settings.tencentcloud_secret_id or not settings.tencentcloud_secret_key:
        raise RuntimeError("未配置腾讯云密钥，无法签名 SOE-N WebSocket 请求。")
    cleaned_text = reference_text.strip()
    if not cleaned_text:
        raise ValueError("SOE-N 句子评测需要非空英文参考文本。")
    now = int(time.time()) if timestamp is None else timestamp
    current_nonce = now if nonce is None else nonce
    if current_nonce <= 0 or len(str(current_nonce)) > 10:
        raise ValueError("SOE-N nonce 必须是最长 10 位的正整数。")
    current_voice_id = voice_id or str(uuid4())
    if not current_voice_id or len(current_voice_id) > 128:
        raise ValueError("SOE-N voice_id 必须为 1 到 128 个字符。")
    params = {
        "eval_mode": "1",
        "expired": str(now + 3600),
        "keyword": "",
        "nonce": str(current_nonce),
        "rec_mode": "0",
        "ref_text": cleaned_text,
        "score_coeff": "1.0",
        "secretid": settings.tencentcloud_secret_id,
        "server_engine_type": target.server_engine_type,
        "sentence_info_enabled": "0",
        "text_mode": "0",
        "timestamp": str(now),
        "voice_format": "0",
        "voice_id": current_voice_id,
    }
    signature_params = tuple(sorted(params.items()))
    raw_query = "&".join(f"{key}={value}" for key, value in signature_params)
    query = "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in signature_params
    )
    path = target.url.removeprefix(f"wss://{SOE_N_HOST}")
    signing_text = f"{SOE_N_HOST}{path}?{raw_query}"
    signature = base64.b64encode(
        hmac.new(
            settings.tencentcloud_secret_key.encode(), signing_text.encode(), hashlib.sha1
        ).digest()
    ).decode()
    return SoeNHandshakeTarget(
        url=f"{target.url}?{query}&signature={quote(signature, safe='')}",
        server_engine_type=target.server_engine_type,
        voice_id=current_voice_id,
        signature_params=signature_params,
        signing_text=signing_text,
        signature=signature,
    )


async def verify_soe_n_handshake(settings: Settings) -> None:
    """Open a real SOE-N signed WebSocket connection; no audio is submitted."""
    target = signed_soe_n_handshake_target(settings)
    async with websockets.connect(target.url, open_timeout=15, close_timeout=5):
        await asyncio.sleep(0)
