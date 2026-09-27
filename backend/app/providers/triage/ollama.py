import os

from app.providers.triage.base import TriageResult
from app.providers.triage.prompt import build_messages
from app.providers.triage.transport import post_json


class OllamaTriage:
    name = "llm:ollama"

    def triage(self, text: str, location: str) -> TriageResult:
        base_url = os.environ.get(
            "OLLAMA_BASE_URL", "http://ollama:11434"
        ).rstrip("/")
        response = post_json(
            base_url + "/api/chat",
            payload={
                "model": os.environ.get("OLLAMA_MODEL", "llama3.2:1b"),
                "messages": build_messages(text),
                "stream": False,
                "format": TriageResult.model_json_schema(),
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "num_ctx": 2048,
                    "num_predict": 180,
                },
            },
        )
        return TriageResult.model_validate_json(response["message"]["content"])
