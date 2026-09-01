import pytest

from app.core.config import Settings
from app.providers.ai import ExternalHttpProvider


@pytest.mark.asyncio
async def test_external_provider_fails_closed_without_credentials() -> None:
    provider = ExternalHttpProvider(Settings(ai_api_base_url="", ai_api_key=""))
    with pytest.raises(RuntimeError, match="未配置外部 AI Provider"):
        await provider.transcribe_english("https://media.example.com/audio.mp3")
    with pytest.raises(RuntimeError, match="未配置外部 AI Provider"):
        await provider.reply_to_role_play("Ordering coffee", [])
