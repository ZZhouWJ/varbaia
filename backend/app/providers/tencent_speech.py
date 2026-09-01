"""Tencent Cloud English STT/TTS boundary for voice role play."""

import asyncio
import base64
import json
from dataclasses import dataclass
from uuid import uuid4

from tencentcloud.asr.v20190614 import asr_client
from tencentcloud.asr.v20190614 import models as asr_models
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.tts.v20190823 import models as tts_models
from tencentcloud.tts.v20190823 import tts_client

from app.core.config import Settings
from app.providers.pronunciation import PronunciationProviderError


@dataclass(frozen=True)
class SynthesizedSpeech:
    wav_bytes: bytes
    session_id: str


class TencentEnglishSpeechProvider:
    """Keeps Tencent SDK request details outside Role Play business code."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.tencentcloud_secret_id or not settings.tencentcloud_secret_key:
            raise PronunciationProviderError("authentication_error", "未配置腾讯云语音凭据。")

    async def transcribe_pcm16(self, pcm_bytes: bytes) -> str:
        if not pcm_bytes:
            raise PronunciationProviderError("invalid_audio", "不能识别空录音。")
        return await asyncio.to_thread(self._transcribe_pcm16, pcm_bytes)

    async def synthesize_english(self, text: str) -> SynthesizedSpeech:
        if not text.strip():
            raise PronunciationProviderError("provider_business_error", "不能合成空文本。")
        return await asyncio.to_thread(self._synthesize_english, text)

    def _profile(self, endpoint: str) -> ClientProfile:
        profile = ClientProfile()
        profile.httpProfile.endpoint = endpoint
        return profile

    def _credentials(self) -> credential.Credential:
        return credential.Credential(
            self.settings.tencentcloud_secret_id, self.settings.tencentcloud_secret_key
        )

    def _transcribe_pcm16(self, pcm_bytes: bytes) -> str:
        request = asr_models.SentenceRecognitionRequest()
        request.from_json_string(
            json.dumps(
                {
                    "EngSerViceType": self.settings.tencentcloud_asr_engine_model_type or "16k_en",
                    "SourceType": 1,
                    "VoiceFormat": "pcm",
                    "Data": base64.b64encode(pcm_bytes).decode(),
                    "DataLen": len(pcm_bytes),
                }
            )
        )
        client = asr_client.AsrClient(
            self._credentials(), "", self._profile("asr.tencentcloudapi.com")
        )
        response = client.SentenceRecognition(request)
        transcript = str(response.Result).strip()
        if not transcript:
            raise PronunciationProviderError(
                "provider_business_error", "腾讯云未返回英语转写文本。"
            )
        return transcript

    def _synthesize_english(self, text: str) -> SynthesizedSpeech:
        try:
            voice_type = int(self.settings.tencentcloud_tts_voice_type)
        except ValueError as exc:
            raise PronunciationProviderError(
                "invalid_audio", "TENCENTCLOUD_TTS_VOICE_TYPE 必须是数字。"
            ) from exc
        session_id = str(uuid4())
        request = tts_models.TextToVoiceRequest()
        request.from_json_string(
            json.dumps(
                {
                    "Text": text,
                    "SessionId": session_id,
                    "ModelType": 1,
                    "VoiceType": voice_type,
                    "PrimaryLanguage": 2,
                    "SampleRate": 16000,
                    "Codec": "wav",
                }
            )
        )
        client = tts_client.TtsClient(
            self._credentials(),
            self.settings.tencentcloud_region or "ap-beijing",
            self._profile("tts.tencentcloudapi.com"),
        )
        response = client.TextToVoice(request)
        try:
            wav_bytes = base64.b64decode(response.Audio, validate=True)
        except Exception as exc:
            raise PronunciationProviderError(
                "provider_business_error", "腾讯云返回的 TTS 音频无效。"
            ) from exc
        if not wav_bytes:
            raise PronunciationProviderError("provider_business_error", "腾讯云返回了空 TTS 音频。")
        return SynthesizedSpeech(wav_bytes=wav_bytes, session_id=session_id)
