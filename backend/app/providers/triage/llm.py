import os

from app.providers.triage.base import TriageResult
from app.providers.triage.prompt import build_messages
from app.providers.triage.transport import post_json


class LLMTriage:
    name = "llm:groq"

    def triage(self, text: str, location: str) -> TriageResult:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        response = post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            payload={
                "model": os.environ.get(
                    "GROQ_MODEL", "openai/gpt-oss-20b"
                ),
                "messages": build_messages(text),
                "temperature": 0,
                "reasoning_effort": "low",
                "max_completion_tokens": 2048,
                "response_format": {"type": "json_object"},
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )

        content = response["choices"][0]["message"]["content"]
        return TriageResult.model_validate_json(content)

