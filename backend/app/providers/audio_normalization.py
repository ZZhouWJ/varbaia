"""Explicit media boundary for pronunciation providers."""

import asyncio
import shutil
import wave
from pathlib import Path

from app.providers.pronunciation import NormalizedPcmAudio, PronunciationProviderError

MAX_AUDIO_BYTES = 20 * 1024 * 1024
MIN_DURATION_SECONDS = 0.1
MAX_DURATION_SECONDS = 60.0
PCM_SAMPLE_RATE = 16_000
PCM_CHANNELS = 1
PCM_SAMPLE_WIDTH = 2


def validate_reference_text(reference_text: str) -> str:
    cleaned = " ".join(reference_text.split())
    if not cleaned:
        raise PronunciationProviderError("invalid_reference_text", "参考文本不能为空。")
    if len(cleaned.split()) > 30:
        raise PronunciationProviderError(
            "invalid_reference_text", "句子评测最多支持 30 个英文单词。"
        )
    if not cleaned.isascii():
        raise PronunciationProviderError(
            "invalid_reference_text", "第一版仅支持英文 ASCII 参考文本。"
        )
    return cleaned


async def normalize_audio(path: Path, mime_type: str) -> NormalizedPcmAudio:
    """Validate then convert supported browser recordings to SOE-N PCM.

    WAV is accepted directly only when it is already 16 kHz mono PCM16.  The
    browser's WebM/Opus recordings, OGG, and MP4/AAC are explicitly converted
    with FFmpeg; if FFmpeg is unavailable we fail rather than uploading an
    incompatible file.
    """
    if not path.is_file() or path.stat().st_size == 0:
        raise PronunciationProviderError("invalid_audio", "录音文件为空或不存在。")
    if path.stat().st_size > MAX_AUDIO_BYTES:
        raise PronunciationProviderError("invalid_audio", "录音文件超过 20MB。")
    suffix = path.suffix.lower()
    if suffix == ".wav":
        return _read_pcm_wav(path)
    if suffix not in {".webm", ".ogg", ".mp4"}:
        raise PronunciationProviderError("invalid_audio", "不支持的音频容器格式。")
    if not mime_type.startswith("audio/"):
        raise PronunciationProviderError("invalid_audio", "上传文件不是音频 MIME 类型。")
    return await _transcode_with_ffmpeg(path, suffix.removeprefix("."))


def _read_pcm_wav(path: Path) -> NormalizedPcmAudio:
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            sample_rate = source.getframerate()
            sample_width = source.getsampwidth()
            compression = source.getcomptype()
            frames = source.getnframes()
            pcm_bytes = source.readframes(frames)
    except wave.Error as exc:
        raise PronunciationProviderError("invalid_audio", "WAV 文件无法解析。") from exc
    if (channels, sample_rate, sample_width, compression) != (
        PCM_CHANNELS,
        PCM_SAMPLE_RATE,
        PCM_SAMPLE_WIDTH,
        "NONE",
    ):
        raise PronunciationProviderError(
            "invalid_audio", "WAV 必须为 16kHz、单声道、16-bit PCM；请重新录音。"
        )
    return _normalized_pcm(pcm_bytes, "wav")


async def _transcode_with_ffmpeg(path: Path, source_container: str) -> NormalizedPcmAudio:
    executable = shutil.which("ffmpeg")
    if executable is None:
        raise PronunciationProviderError(
            "invalid_audio", "服务器未安装 FFmpeg，无法转换浏览器 WebM/OGG/MP4 录音。"
        )
    process = await asyncio.create_subprocess_exec(
        executable,
        "-v",
        "error",
        "-i",
        str(path),
        "-ac",
        str(PCM_CHANNELS),
        "-ar",
        str(PCM_SAMPLE_RATE),
        "-f",
        "s16le",
        "-acodec",
        "pcm_s16le",
        "pipe:1",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    pcm_bytes, stderr = await process.communicate()
    if process.returncode != 0:
        detail = RuntimeError(stderr.decode(errors="replace")[:200])
        raise PronunciationProviderError(
            "invalid_audio", "音频转换失败，无法用于发音评测。"
        ) from detail
    return _normalized_pcm(pcm_bytes, source_container)


def _normalized_pcm(pcm_bytes: bytes, source_container: str) -> NormalizedPcmAudio:
    if len(pcm_bytes) % (PCM_CHANNELS * PCM_SAMPLE_WIDTH) != 0:
        raise PronunciationProviderError("invalid_audio", "PCM 数据的位深或声道数不合法。")
    duration = len(pcm_bytes) / (PCM_SAMPLE_RATE * PCM_CHANNELS * PCM_SAMPLE_WIDTH)
    if not MIN_DURATION_SECONDS <= duration <= MAX_DURATION_SECONDS:
        raise PronunciationProviderError("invalid_audio", "句子评测录音时长须在 0.1 至 60 秒之间。")
    return NormalizedPcmAudio(
        pcm_bytes=pcm_bytes, duration_seconds=duration, source_container=source_container
    )
