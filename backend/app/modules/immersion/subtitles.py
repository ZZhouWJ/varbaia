import re

from fastapi import HTTPException

TIME_PATTERN = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})[,.](?P<ms>\d{3})\s*-->\s*"
    r"(?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2})[,.](?P<ems>\d{3})"
)


def _to_ms(hours: str, minutes: str, seconds: str, milliseconds: str) -> int:
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(milliseconds)


def parse_subtitles(content: str) -> list[tuple[int, int, str]]:
    segments: list[tuple[int, int, str]] = []
    blocks = re.split(r"\r?\n\s*\r?\n", content.lstrip("\ufeff").replace("WEBVTT", "", 1))
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        time_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue
        match = TIME_PATTERN.search(lines[time_index])
        if match is None:
            raise HTTPException(status_code=422, detail="字幕时间格式无效")
        text = " ".join(lines[time_index + 1 :]).strip()
        if not text:
            continue
        start = _to_ms(match["h"], match["m"], match["s"], match["ms"])
        end = _to_ms(match["eh"], match["em"], match["es"], match["ems"])
        if end <= start:
            raise HTTPException(status_code=422, detail="字幕时间范围无效")
        segments.append((start, end, text))
    if not segments:
        raise HTTPException(status_code=422, detail="未识别到有效字幕片段")
    return segments
