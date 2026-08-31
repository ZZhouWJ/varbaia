from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class WritingEvaluation:
    clarity_score: int
    corrected_draft: str
    suggestions: list[str]


class EnglishLearningProvider(Protocol):
    async def evaluate_writing(self, prompt: str, draft: str) -> WritingEvaluation: ...

    async def transcribe_english(self, audio_url: str) -> list[dict[str, object]]: ...


class ExternalHttpProvider:
    """Minimal OpenAI-compatible adapter; deployments select the actual provider by config."""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ai_api_base_url.rstrip("/")
        self.api_key = settings.ai_api_key

    async def evaluate_writing(self, prompt: str, draft: str) -> WritingEvaluation:
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置外部 AI Provider，无法执行写作评价。")
        payload = {
            "model": "configured-by-provider",
            "messages": [
                {
                    "role": "system",
                    "content": "Return concise English-learning writing feedback as JSON.",
                },
                {"role": "user", "content": f"Prompt: {prompt}\nDraft: {draft}"},
            ],
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        import json

        data = json.loads(content)
        return WritingEvaluation(
            clarity_score=int(data["clarity_score"]),
            corrected_draft=str(data["corrected_draft"]),
            suggestions=[str(item) for item in data["suggestions"]],
        )

    async def transcribe_english(self, audio_url: str) -> list[dict[str, object]]:
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置外部 AI Provider，无法执行英语转写。")
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"audio_url": audio_url, "language": "en", "response_format": "verbose_json"},
            )
            response.raise_for_status()
        segments = response.json().get("segments", [])
        return [
            {"start": float(item["start"]), "end": float(item["end"]), "text": str(item["text"])}
            for item in segments
        ]
