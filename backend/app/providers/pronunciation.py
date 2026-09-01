"""Provider-neutral pronunciation assessment contracts."""

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class NormalizedPcmAudio:
    """16 kHz, mono, signed 16-bit little-endian PCM accepted by SOE-N."""

    pcm_bytes: bytes
    duration_seconds: float
    source_container: str


@dataclass(frozen=True)
class WordResult:
    text: str | None
    start_time_ms: int | None
    end_time_ms: int | None
    pronunciation_accuracy: float | None
    pronunciation_fluency: float | None
    match_tag: int | None


@dataclass(frozen=True)
class PhoneResult:
    text: str | None
    start_time_ms: int | None
    end_time_ms: int | None
    pronunciation_accuracy: float | None
    match_tag: int | None


@dataclass(frozen=True)
class PronunciationAssessment:
    overall_score: float | None
    pronunciation_accuracy: float | None
    pronunciation_fluency: float | None
    pronunciation_completion: float | None
    word_results: tuple[WordResult, ...]
    phone_results: tuple[PhoneResult, ...]
    raw_provider_result: dict[str, object]

    def public_dict(self) -> dict[str, object]:
        """Return the stable domain response without provider diagnostic data."""
        data = asdict(self)
        data.pop("raw_provider_result")
        return data


class PronunciationProviderError(RuntimeError):
    def __init__(self, category: str, message: str, *, provider_code: int | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.provider_code = provider_code


class PronunciationAssessmentProvider(Protocol):
    async def assess(
        self, reference_text: str, audio: NormalizedPcmAudio
    ) -> PronunciationAssessment: ...
