from app.modules.immersion.tasks import STEPS


def test_import_state_sequence_is_monotonic_and_finishes_ready() -> None:
    statuses = [step[0] for step in STEPS]
    progress = [step[1] for step in STEPS]
    assert statuses[0] == "validating"
    assert statuses[-1] == "ready"
    assert progress == sorted(progress)
    assert progress[-1] == 100
