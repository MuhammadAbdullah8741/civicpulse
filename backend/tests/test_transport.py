import asyncio

import httpx
import pytest

from app.providers.triage import transport


def test_transport_uses_ten_second_deadline_and_parses_json(monkeypatch):
    real_client = httpx.AsyncClient
    real_timeout = asyncio.timeout
    deadlines = []

    def deadline(seconds):
        deadlines.append(seconds)
        return real_timeout(seconds)

    def reply(request):
        assert request.method == "POST"
        return httpx.Response(200, json={"result": "ok"})

    def client(**kwargs):
        assert kwargs["timeout"].read == 10.0
        assert kwargs["follow_redirects"] is False
        return real_client(transport=httpx.MockTransport(reply), **kwargs)

    monkeypatch.setattr(transport.asyncio, "timeout", deadline)
    monkeypatch.setattr(transport.httpx, "AsyncClient", client)
    assert transport.post_json("https://example.invalid", {"test": True}) == {"result": "ok"}
    assert deadlines == [10.0]


def test_transport_deadline_cancels_pending_request(monkeypatch):
    real_timeout = asyncio.timeout

    def immediate_deadline(seconds):
        assert seconds == 10.0
        # Exercise cancellation deterministically without a ten-second sleep.
        return real_timeout(0)

    class PendingClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def post(self, *args, **kwargs):
            await asyncio.Event().wait()

    monkeypatch.setattr(transport.asyncio, "timeout", immediate_deadline)
    monkeypatch.setattr(transport.httpx, "AsyncClient", lambda **kwargs: PendingClient())
    with pytest.raises(TimeoutError):
        transport.post_json("https://example.invalid", {})
