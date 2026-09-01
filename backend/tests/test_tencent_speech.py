import base64
import json

import pytest

from app.core.config import Settings
from app.providers.tencent_speech import TencentEnglishSpeechProvider


class FakeAsrResponse:
    Result = "hello there"


class FakeAsrClient:
    request: object | None = None

    def __init__(self, *_args: object) -> None:
        pass

    def SentenceRecognition(self, request: object) -> FakeAsrResponse:
        type(self).request = request
        return FakeAsrResponse()


class FakeTtsResponse:
    Audio = base64.b64encode(b"RIFFfake-wav").decode()


class FakeTtsClient:
    request: object | None = None

    def __init__(self, *_args: object) -> None:
        pass

    def TextToVoice(self, request: object) -> FakeTtsResponse:
        type(self).request = request
        return FakeTtsResponse()


def settings() -> Settings:
    return Settings(
        _env_file=None,
        tencentcloud_secret_id="secret-id",
        tencentcloud_secret_key="secret-key",
        tencentcloud_tts_voice_type="101001",
    )


@pytest.mark.asyncio
async def test_transcription_uses_pcm_english_sentence_recognition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.providers.tencent_speech.asr_client.AsrClient", FakeAsrClient)
    transcript = await TencentEnglishSpeechProvider(settings()).transcribe_pcm16(b"\x00\x00" * 1600)
    payload = json.loads(FakeAsrClient.request.to_json_string())  # type: ignore[union-attr]
    assert transcript == "hello there"
    assert payload["EngSerViceType"] == "16k_en"
    assert payload["VoiceFormat"] == "pcm"
    assert payload["DataLen"] == 3200


@pytest.mark.asyncio
async def test_synthesis_uses_english_wav_and_decodes_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.providers.tencent_speech.tts_client.TtsClient", FakeTtsClient)
    speech = await TencentEnglishSpeechProvider(settings()).synthesize_english("Hello there")
    payload = json.loads(FakeTtsClient.request.to_json_string())  # type: ignore[union-attr]
    assert payload["PrimaryLanguage"] == 2
    assert payload["Codec"] == "wav"
    assert payload["VoiceType"] == 101001
    assert speech.wav_bytes == b"RIFFfake-wav"
