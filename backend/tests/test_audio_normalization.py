import wave
from pathlib import Path

import pytest

from app.providers.audio_normalization import normalize_audio, validate_reference_text
from app.providers.pronunciation import PronunciationProviderError


def write_wav(path: Path, *, sample_rate: int = 16000, channels: int = 1, width: int = 2) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(width)
        output.setframerate(sample_rate)
        output.writeframes(b"\x00" * (sample_rate * channels * width // 10))


@pytest.mark.asyncio
async def test_accepts_pcm16_mono_16khz_wav(tmp_path: Path) -> None:
    path = tmp_path / "recording.wav"
    write_wav(path)
    normalized = await normalize_audio(path, "audio/wav")
    assert normalized.source_container == "wav"
    assert normalized.duration_seconds == 0.1


@pytest.mark.asyncio
async def test_rejects_wav_with_unsupported_sample_rate(tmp_path: Path) -> None:
    path = tmp_path / "recording.wav"
    write_wav(path, sample_rate=44100)
    with pytest.raises(PronunciationProviderError) as raised:
        await normalize_audio(path, "audio/wav")
    assert raised.value.category == "invalid_audio"


def test_reference_text_is_english_and_nonempty() -> None:
    assert validate_reference_text("  hello\nworld  ") == "hello world"
    with pytest.raises(PronunciationProviderError) as raised:
        validate_reference_text("你好")
    assert raised.value.category == "invalid_reference_text"
