import asyncio
from typing import Any

import httpx

CALL_TIMEOUT_SECONDS = 10.0


async def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> dict[str, Any]:
    async with asyncio.timeout(CALL_TIMEOUT_SECONDS):
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(CALL_TIMEOUT_SECONDS),
            follow_redirects=False,
        ) as client:
            response = await client.post(
                url, json=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()


def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    # Called from synchronous routes running in FastAPI's worker threads.
    return asyncio.run(_post_json(url, payload, headers or {}))
