from collections.abc import Iterator
from pathlib import Path

from fastapi import HTTPException, status


def safe_media_path(root: Path, stored_name: str) -> Path:
    path = (root / stored_name).resolve()
    if root.resolve() not in path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到媒体")
    return path


def validate_media_signature(path: Path, suffix: str) -> None:
    """Reject files whose container header conflicts with the claimed video extension."""
    header = path.read_bytes()[:32]
    is_iso_bmff = len(header) >= 8 and header[4:8] == b"ftyp"
    is_webm = header.startswith(b"\x1a\x45\xdf\xa3")
    valid = (suffix in {".mp4", ".mov", ".m4v"} and is_iso_bmff) or (
        suffix == ".webm" and is_webm
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="媒体内容与文件类型不匹配",
        )


def parse_range(value: str | None, size: int) -> tuple[int, int] | None:
    if not value:
        return None
    if not value.startswith("bytes="):
        raise HTTPException(status_code=416, detail="无效的媒体 Range")
    start_text, _, end_text = value[6:].partition("-")
    if not start_text:
        length = int(end_text)
        return max(0, size - length), size - 1
    start = int(start_text)
    end = int(end_text) if end_text else size - 1
    if start < 0 or start >= size or end < start:
        raise HTTPException(status_code=416, detail="无效的媒体 Range")
    return start, min(end, size - 1)


def iter_bytes(path: Path, start: int, end: int, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    with path.open("rb") as source:
        source.seek(start)
        remaining = end - start + 1
        while remaining:
            chunk = source.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
