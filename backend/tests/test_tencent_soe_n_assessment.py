import json
from contextlib import AbstractAsyncContextManager

import pytest

from app.core.config import Settings
from app.providers.pronunciation import NormalizedPcmAudio, PronunciationProviderError
from app.providers.tencent_soe_n_assessment import TencentSOENAdapter, parse_soe_n_result


class MockSocket:
    def __init__(self, events: list[dict[str, object]]) -> None:
        self.events = [json.dumps(event) for event in events]
        self.sent: list[bytes | str] = []

    async def send(self, message: bytes | str) -> None:
        self.sent.append(message)

    async def recv(self) -> str:
        return self.events.pop(0)


class MockConnection(AbstractAsyncContextManager[MockSocket]):
    def __init__(self, socket: MockSocket) -> None:
        self.socket = socket

    async def __aenter__(self) -> MockSocket:
        return self.socket

    async def __aexit__(self, *args: object) -> None:
        return None


def adapter_for(socket: MockSocket) -> TencentSOENAdapter:
    settings = Settings(
        _env_file=None,
        tencentcloud_app_id="fake-app",
        tencentcloud_secret_id="fake-secret-id",
        tencentcloud_secret_key="fake-secret-key",
    )
    return TencentSOENAdapter(settings, connect=lambda _url: MockConnection(socket))


@pytest.mark.asyncio
async def test_adapter_uploads_pcm_then_end_and_returns_final_domain_result() -> None:
    socket = MockSocket(
        [
            {"code": 0, "message": "success"},
            {
                "code": 0,
                "final": 1,
                "result": {
                    "SuggestedScore": 91.5,
                    "PronAccuracy": 90,
                    "PronFluency": 0.88,
                    "PronCompletion": 1,
                    "Words": [
                        {
                            "Word": "hello",
                            "MemBeginTime": 0,
                            "MemEndTime": 410,
                            "PronAccuracy": 90,
                            "PronFluency": 0.88,
                            "MatchTag": 0,
                            "PhoneInfos": [
                                {
                                    "Phone": "hh",
                                    "MemBeginTime": 0,
                                    "MemEndTime": 80,
                                    "PronAccuracy": 92,
                                    "MatchTag": 0,
                                }
                            ],
                        }
                    ],
                },
            },
        ]
    )
    result = await adapter_for(socket).assess(
        "hello world", NormalizedPcmAudio(b"\x00\x00" * 1600, 0.1, "webm")
    )
    assert socket.sent[0] == b"\x00\x00" * 1600
    assert socket.sent[1] == '{"type": "end"}'
    assert result.overall_score == 91.5
    assert result.pronunciation_accuracy == 90
    assert result.word_results[0].text == "hello"
    assert result.phone_results[0].text == "hh"
    assert "raw_provider_result" not in result.public_dict()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("code", "category"),
    [(4002, "authentication_error"), (4003, "service_unavailable"), (4004, "provider_rate_limit")],
)
async def test_adapter_maps_tencent_business_errors(code: int, category: str) -> None:
    with pytest.raises(PronunciationProviderError) as raised:
        await adapter_for(MockSocket([{"code": code, "message": "provider failure"}])).assess(
            "hello", NormalizedPcmAudio(b"\x00\x00" * 1600, 0.1, "wav")
        )
    assert raised.value.category == category
    assert raised.value.provider_code == code


def test_response_parser_does_not_guess_missing_score_fields() -> None:
    assessment = parse_soe_n_result({"Words": [{"Word": "hello", "MatchTag": 0}]})
    assert assessment.overall_score is None
    assert assessment.pronunciation_accuracy is None
    assert assessment.word_results[0].match_tag == 0
    assert assessment.phone_results == ()
