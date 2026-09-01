"""Tencent SOE-N implementation of the pronunciation provider contract.

Only this module knows Tencent's WebSocket event shape.  Business modules use
``PronunciationAssessmentProvider`` and never receive signed URLs or Tencent
credentials.
"""

import asyncio
import json
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol, cast

import websockets

from app.core.config import Settings
from app.providers.audio_normalization import validate_reference_text
from app.providers.pronunciation import (
    NormalizedPcmAudio,
    PhoneResult,
    PronunciationAssessment,
    PronunciationProviderError,
    WordResult,
)
from app.providers.tencent_soe_n import signed_soe_n_assessment_target

Connect = Callable[[str], AbstractAsyncContextManager["SoeNWebSocket"]]


class SoeNWebSocket(Protocol):
    async def send(self, message: bytes | str) -> None: ...

    async def recv(self) -> str | bytes: ...


class TencentSOENAdapter:
    """Assess an English sentence through the SOE-N WebSocket protocol."""

    def __init__(
        self,
        settings: Settings,
        *,
        connect: Connect | None = None,
        timeout_seconds: float = 30,
    ) -> None:
        self.settings = settings
        self.connect = connect or cast(Connect, websockets.connect)
        self.timeout_seconds = timeout_seconds

    async def assess(
        self, reference_text: str, audio: NormalizedPcmAudio
    ) -> PronunciationAssessment:
        cleaned_text = validate_reference_text(reference_text)
        if not audio.pcm_bytes:
            raise PronunciationProviderError("invalid_audio", "不能提交空的 PCM 音频。")
        target = signed_soe_n_assessment_target(self.settings, cleaned_text)
        try:
            async with self.connect(target.url) as socket:
                handshake = await self._receive_event(socket)
                self._ensure_success(handshake)
                await socket.send(audio.pcm_bytes)
                await socket.send(json.dumps({"type": "end"}))
                return await self._receive_final_result(socket)
        except PronunciationProviderError:
            raise
        except TimeoutError as exc:
            raise PronunciationProviderError("provider_timeout", "SOE-N 评测响应超时。") from exc
        except websockets.WebSocketException as exc:
            raise PronunciationProviderError(
                "websocket_error", "SOE-N WebSocket 连接失败。"
            ) from exc
        except OSError as exc:
            raise PronunciationProviderError("websocket_error", "SOE-N 网络连接失败。") from exc

    async def _receive_event(self, socket: SoeNWebSocket) -> dict[str, object]:
        try:
            message = await asyncio.wait_for(socket.recv(), timeout=self.timeout_seconds)
        except TimeoutError as exc:
            raise PronunciationProviderError("provider_timeout", "SOE-N 评测响应超时。") from exc
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        try:
            value = json.loads(message)
        except json.JSONDecodeError as exc:
            raise PronunciationProviderError(
                "provider_business_error", "SOE-N 返回了无效 JSON。"
            ) from exc
        if not isinstance(value, dict):
            raise PronunciationProviderError("provider_business_error", "SOE-N 返回格式不正确。")
        return cast(dict[str, object], value)

    async def _receive_final_result(self, socket: SoeNWebSocket) -> PronunciationAssessment:
        while True:
            event = await self._receive_event(socket)
            self._ensure_success(event)
            if event.get("final") in (1, "1", True):
                result = event.get("result")
                if not isinstance(result, dict):
                    raise PronunciationProviderError(
                        "provider_business_error", "SOE-N 最终响应缺少 result。"
                    )
                return parse_soe_n_result(cast(dict[str, object], result))

    @staticmethod
    def _ensure_success(event: dict[str, object]) -> None:
        code = event.get("code", 0)
        try:
            numeric_code = int(cast(int | str, code))
        except (TypeError, ValueError):
            raise PronunciationProviderError(
                "provider_business_error", "SOE-N 返回了无效 code。"
            ) from None
        if numeric_code == 0:
            return
        message = str(event.get("message", "SOE-N 业务错误"))
        category = {
            4002: "authentication_error",
            4003: "service_unavailable",
            4004: "provider_rate_limit",
            4005: "service_unavailable",
        }.get(numeric_code, "provider_business_error")
        raise PronunciationProviderError(category, message, provider_code=numeric_code)


def parse_soe_n_result(result: dict[str, object]) -> PronunciationAssessment:
    """Map only documented SOE-N response keys; keep all other data internally.

    Tencent's sentence-mode response uses ``SuggestedScore``, ``PronAccuracy``,
    ``PronFluency``, ``PronCompletion``, ``Words`` and each word's
    ``PhoneInfos``. Missing fields deliberately remain ``None`` rather than
    being inferred from similarly named provider values.
    """
    words_source = result.get("Words")
    words = _parse_words(words_source)
    phones = _parse_phones(words_source)
    return PronunciationAssessment(
        overall_score=_number(result.get("SuggestedScore")),
        pronunciation_accuracy=_number(result.get("PronAccuracy")),
        pronunciation_fluency=_number(result.get("PronFluency")),
        pronunciation_completion=_number(result.get("PronCompletion")),
        word_results=tuple(words),
        phone_results=tuple(phones),
        raw_provider_result=result,
    )


def _parse_words(value: object) -> list[WordResult]:
    if not isinstance(value, list):
        return []
    results: list[WordResult] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        results.append(
            WordResult(
                text=_string(item.get("Word")),
                start_time_ms=_integer(item.get("MemBeginTime")),
                end_time_ms=_integer(item.get("MemEndTime")),
                pronunciation_accuracy=_number(item.get("PronAccuracy")),
                pronunciation_fluency=_number(item.get("PronFluency")),
                match_tag=_integer(item.get("MatchTag")),
            )
        )
    return results


def _parse_phones(value: object) -> list[PhoneResult]:
    if not isinstance(value, list):
        return []
    results: list[PhoneResult] = []
    for word in value:
        if not isinstance(word, dict):
            continue
        phone_infos = word.get("PhoneInfos")
        if not isinstance(phone_infos, list):
            continue
        for item in phone_infos:
            if not isinstance(item, dict):
                continue
            results.append(
                PhoneResult(
                    text=_string(item.get("Phone")),
                    start_time_ms=_integer(item.get("MemBeginTime")),
                    end_time_ms=_integer(item.get("MemEndTime")),
                    pronunciation_accuracy=_number(item.get("PronAccuracy")),
                    match_tag=_integer(item.get("MatchTag")),
                )
            )
    return results


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _string(value: object) -> str | None:
    return value if isinstance(value, str) else None

