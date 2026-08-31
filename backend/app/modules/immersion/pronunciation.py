from dataclasses import dataclass


@dataclass(frozen=True)
class PronunciationSignals:
    word_accuracy: float
    phoneme_accuracy: float
    rhythm: float
    intonation: float


@dataclass(frozen=True)
class PronunciationResult:
    score: int
    band: str
    coaching: str


def score_pronunciation(signals: PronunciationSignals) -> PronunciationResult:
    values = [signals.word_accuracy, signals.phoneme_accuracy, signals.rhythm, signals.intonation]
    if any(value < 0 or value > 100 for value in values):
        raise ValueError("发音分项必须在 0 到 100 之间")
    score = round(
        signals.word_accuracy * 0.35
        + signals.phoneme_accuracy * 0.35
        + signals.rhythm * 0.2
        + signals.intonation * 0.1
    )
    if score >= 90:
        return PronunciationResult(score, "自然", "保持句子重音，尝试更快语速。")
    if score >= 75:
        return PronunciationResult(score, "清晰", "优先复听连读和重读词，再录一次。")
    return PronunciationResult(score, "练习中", "放慢语速，先稳定每个重读音节。")
