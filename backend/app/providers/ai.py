from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class WritingEvaluation:
    clarity_score: int
    corrected_draft: str
    suggestions: list[str]
    grammar_score: int | None = None
    vocabulary_score: int | None = None
    coherence_score: int | None = None
    task_completion_score: int | None = None
    key_errors: list[str] | None = None
    better_expressions: list[str] | None = None


@dataclass(frozen=True)
class RolePlayReply:
    reply: str
    coaching_tip: str


@dataclass(frozen=True)
class RolePlayFeedback:
    task_completion: int
    grammar: int
    vocabulary: int
    fluency: int | None
    pronunciation: int | None
    naturalness: int
    key_corrections: list[str]
    better_expressions: list[str]


class EnglishLearningProvider(Protocol):
    async def evaluate_writing(self, prompt: str, draft: str) -> WritingEvaluation: ...

    async def transcribe_english(self, audio_url: str) -> list[dict[str, object]]: ...

    async def reply_to_role_play(
        self, scenario: str, conversation: list[dict[str, str]]
    ) -> RolePlayReply: ...

    async def evaluate_role_play(
        self, scenario: str, conversation: list[dict[str, str]]
    ) -> RolePlayFeedback: ...


class ExternalHttpProvider:
    """Minimal OpenAI-compatible adapter; deployments select the actual provider by config."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.ai_api_base_url.rstrip("/")
        self.api_key = settings.ai_api_key

    async def evaluate_writing(self, prompt: str, draft: str) -> WritingEvaluation:
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置外部 AI Provider，无法执行写作评价。")
        payload = {
            "model": self.settings.ai_model or "configured-by-provider",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return ONLY a JSON object with integer 0-100 fields clarity_score, "
                        "grammar_score, vocabulary_score, coherence_score, task_completion_score; "
                        "corrected_draft (string); suggestions, key_errors, and better_expressions "
                        "(arrays of concise strings). Assess English writing only."
                    ),
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
            grammar_score=_optional_score(data.get("grammar_score")),
            vocabulary_score=_optional_score(data.get("vocabulary_score")),
            coherence_score=_optional_score(data.get("coherence_score")),
            task_completion_score=_optional_score(data.get("task_completion_score")),
            key_errors=[str(item) for item in data.get("key_errors", [])],
            better_expressions=[str(item) for item in data.get("better_expressions", [])],
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

    async def reply_to_role_play(
        self, scenario: str, conversation: list[dict[str, str]]
    ) -> RolePlayReply:
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置外部 AI Provider，无法执行角色扮演。")
        payload = {
            "model": self.settings.ai_model or "configured-by-provider",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an English conversation partner. Reply naturally in English, "
                        "then return JSON with reply and one concise coaching_tip."
                    ),
                },
                {"role": "user", "content": f"Scenario: {scenario}\nConversation: {conversation}"},
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
        import json

        data = json.loads(response.json()["choices"][0]["message"]["content"])
        return RolePlayReply(reply=str(data["reply"]), coaching_tip=str(data["coaching_tip"]))

    async def evaluate_role_play(
        self, scenario: str, conversation: list[dict[str, str]]
    ) -> RolePlayFeedback:
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置外部 AI Provider，无法评价角色扮演。")
        payload = {
            "model": self.settings.ai_model or "configured-by-provider",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return ONLY JSON with integer 0-100 task_completion, grammar, vocabulary, "
                        "naturalness; optional integer fluency/pronunciation only when supported; "
                        "key_corrections and better_expressions arrays. "
                        "Assess English role play only."
                    ),
                },
                {"role": "user", "content": f"Scenario: {scenario}\nConversation: {conversation}"},
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
        import json

        data = json.loads(response.json()["choices"][0]["message"]["content"])
        return RolePlayFeedback(
            task_completion=max(0, min(100, int(data["task_completion"]))),
            grammar=max(0, min(100, int(data["grammar"]))),
            vocabulary=max(0, min(100, int(data["vocabulary"]))),
            fluency=_optional_score(data.get("fluency")),
            pronunciation=_optional_score(data.get("pronunciation")),
            naturalness=max(0, min(100, int(data["naturalness"]))),
            key_corrections=[str(item) for item in data.get("key_corrections", [])],
            better_expressions=[str(item) for item in data.get("better_expressions", [])],
        )


def _optional_score(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    return max(0, min(100, int(value)))
