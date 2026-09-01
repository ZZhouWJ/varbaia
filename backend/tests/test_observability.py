from app.core.observability import request_id_from


def test_request_id_accepts_safe_client_identifier() -> None:
    assert request_id_from("trace_1.2-abc") == "trace_1.2-abc"


def test_request_id_replaces_unsafe_or_oversized_input() -> None:
    assert request_id_from("bad\nlog") != "bad\nlog"
    assert request_id_from("x" * 101) != "x" * 101
