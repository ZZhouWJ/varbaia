import pytest
from fastapi import HTTPException

from app.modules.immersion.media import validate_media_signature


def test_accepts_matching_iso_bmff_header(tmp_path) -> None:
    media = tmp_path / "lesson.mp4"
    media.write_bytes(b"\x00\x00\x00\x18ftypisom")
    validate_media_signature(media, ".mp4")


def test_rejects_mismatched_media_header(tmp_path) -> None:
    media = tmp_path / "lesson.mp4"
    media.write_bytes(b"not-a-video")
    with pytest.raises(HTTPException, match="媒体内容"):
        validate_media_signature(media, ".mp4")
