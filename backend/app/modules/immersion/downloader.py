"""Safe yt-dlp boundary for approved remote immersion media."""

import asyncio
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path

from app.modules.immersion.media import safe_media_path, validate_media_signature

SpawnProcess = Callable[..., Awaitable[asyncio.subprocess.Process]]


async def download_remote_video(
    *,
    source_url: str,
    media_root: Path,
    stored_stem: str,
    max_bytes: int,
    spawn: SpawnProcess = asyncio.create_subprocess_exec,
) -> tuple[str, int]:
    """Download one remote video without trusting provider-controlled filenames."""
    executable = shutil.which("yt-dlp")
    if executable is None:
        raise RuntimeError("服务器未安装 yt-dlp，无法导入远程视频。")
    media_root.mkdir(parents=True, exist_ok=True)
    output_template = safe_media_path(media_root, f"{stored_stem}.%(ext)s")
    process = await spawn(
        executable,
        "--no-playlist",
        "--no-progress",
        "--restrict-filenames",
        "--max-filesize",
        str(max_bytes),
        "--merge-output-format",
        "mp4",
        "--print",
        "after_move:filepath",
        "--output",
        str(output_template),
        source_url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError("远程视频下载失败，请检查来源是否可访问或改为上传文件。")
    lines = [line.strip() for line in stdout.decode(errors="replace").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("yt-dlp 未返回下载文件路径。")
    candidate = Path(lines[-1]).resolve()
    try:
        candidate.relative_to(media_root.resolve())
    except ValueError as exc:
        raise RuntimeError("yt-dlp 返回了媒体目录外的文件。") from exc
    suffix = candidate.suffix.lower()
    if suffix not in {".mp4", ".webm", ".mov", ".m4v"} or not candidate.is_file():
        raise RuntimeError("远程视频格式不受支持或文件不存在。")
    size = candidate.stat().st_size
    if size <= 0 or size > max_bytes:
        candidate.unlink(missing_ok=True)
        raise RuntimeError("远程视频超过大小限制。")
    validate_media_signature(candidate, suffix)
    return candidate.name, size
