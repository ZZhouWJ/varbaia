from app.modules.immersion.subtitles import parse_subtitles


def test_parses_srt_segments_in_order() -> None:
    segments = parse_subtitles(
        "1\n00:00:01,000 --> 00:00:02,500\nHello there.\n\n"
        "2\n00:00:02,500 --> 00:00:04,000\nWelcome back.\n"
    )
    assert segments == [(1000, 2500, "Hello there."), (2500, 4000, "Welcome back.")]


def test_parses_vtt_segments() -> None:
    segments = parse_subtitles("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nPractise English.\n")
    assert segments == [(0, 1000, "Practise English.")]
