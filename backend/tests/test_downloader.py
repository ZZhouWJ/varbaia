from pathlib import Path

import pytest

from app.modules.immersion.downloader import download_remote_video


class FakeProcess:
    returncode = 0

    def __init__(self, output: bytes) -> None:
        self.output = output

    async def communicate(self) -> tuple[bytes, bytes]:
        return self.output, b""


@pytest.mark.asyncio
async def test_remote_download_accepts_only_media_root_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("app.modules.immersion.downloader.shutil.which", lambda _name: "yt-dlp")

    async def fake_spawn(*args: object, **_kwargs: object) -> FakeProcess:
        template = Path(str(args[args.index("--output") + 1]))
        downloaded = Path(str(template).replace(".%(ext)s", ".mp4"))
        downloaded.write_bytes(b"\x00\x00\x00\x18ftypisomfixture")
        return FakeProcess(f"{downloaded}\n".encode())

    name, size = await download_remote_video(
        source_url="https://www.youtube.com/watch?v=fixture",
        media_root=tmp_path,
        stored_stem="safe-name",
        max_bytes=1024,
        spawn=fake_spawn,
    )
    assert name == "safe-name.mp4"
    assert size == len(b"\x00\x00\x00\x18ftypisomfixture")
