import pytest

from app.modules.immersion.pronunciation import PronunciationSignals, score_pronunciation


def test_pronunciation_weights_word_and_phoneme_accuracy() -> None:
    result = score_pronunciation(PronunciationSignals(90, 80, 70, 60))
    assert result.score == 80
    assert result.band == "清晰"


def test_pronunciation_rejects_invalid_provider_scores() -> None:
    with pytest.raises(ValueError):
        score_pronunciation(PronunciationSignals(101, 80, 70, 60))
