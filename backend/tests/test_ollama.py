import json

import pytest
from pydantic import ValidationError

from app.providers.triage import ollama
from app.providers.triage.factory import create_provider


def test_ollama_requests_schema_and_validates_output(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:1b")

    def fake_post(url, payload, headers=None):
        assert url == "http://ollama:11434/api/chat"
        assert payload["model"] == "llama3.2:1b"
        assert payload["stream"] is False
        assert "properties" in payload["format"]
        assert payload["messages"][0]["role"] == "system"
        return {"message": {"content": json.dumps({
            "category": "water", "priority": "high",
            "summary": "Burst water pipe flooding the street.",
            "confidence": 0.9,
        })}}

    monkeypatch.setattr(ollama, "post_json", fake_post)
    result = ollama.OllamaTriage().triage(
        "Burst water pipe flooding the street.", "Synthetic Street"
    )
    assert result.category.value == "water"
    assert result.priority.value == "high"


def test_ollama_rejects_invalid_output(monkeypatch):
    monkeypatch.setattr(
        ollama, "post_json",
        lambda *args, **kwargs: {
            "message": {"content": '{"category":"unicorn"}'}
        },
    )
    with pytest.raises(ValidationError):
        ollama.OllamaTriage().triage("Water pipe leaking outside.", "Synthetic Street")


@pytest.mark.parametrize("selected,expected_name", [
    ("llm", "llm:groq"),
    ("ollama", "llm:ollama"),
    ("rules", "rules"),
    ("simulated", "simulated"),
])
def test_factory_selects_each_provider(monkeypatch, selected, expected_name):
    monkeypatch.setenv("TRIAGE_PROVIDER", selected)
    assert create_provider().name == expected_name


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("TRIAGE_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="Unsupported TRIAGE_PROVIDER"):
        create_provider()
