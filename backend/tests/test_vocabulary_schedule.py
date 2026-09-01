from app.models import VocabularyItem
from app.modules.vocabulary_api import schedule_review


def make_item(interval_days: int, ease: int, repetitions: int) -> VocabularyItem:
    return VocabularyItem(
        term="curious",
        definition="wanting to know more",
        interval_days=interval_days,
        ease=ease,
        repetitions=repetitions,
    )


def test_again_resets_interval_and_reduces_ease() -> None:
    item = make_item(interval_days=8, ease=250, repetitions=3)
    schedule_review(item, "again")
    assert (item.interval_days, item.ease, item.repetitions) == (1, 230, 0)


def test_successful_reviews_match_frontend_schedule() -> None:
    item = make_item(interval_days=0, ease=250, repetitions=0)
    schedule_review(item, "good")
    assert (item.interval_days, item.ease, item.repetitions) == (1, 250, 1)
    schedule_review(item, "easy")
    assert (item.interval_days, item.ease, item.repetitions) == (4, 265, 2)
