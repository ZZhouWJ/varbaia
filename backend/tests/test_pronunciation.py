import pytest

from app.modules.immersion.pronunciation import PronunciationSignals, score_pronunciation
from app.modules.pronunciation_tasks import _public_evaluation_error


def test_pronunciation_weights_word_and_phoneme_accuracy() -> None:
    result = score_pronunciation(PronunciationSignals(90, 80, 70, 60))
    assert result.score == 80
    assert result.band == "清晰"


def test_pronunciation_rejects_invalid_provider_scores() -> None:
    with pytest.raises(ValueError):
        score_pronunciation(PronunciationSignals(101, 80, 70, 60))


def test_public_pronunciation_error_never_echoes_provider_message() -> None:
    assert _public_evaluation_error("authentication_error") == (
        "发音评测鉴权不可用，请联系 Owner 检查服务配置。"
    )
    assert _public_evaluation_error("unknown") == "发音评测服务发生未预期错误。"
