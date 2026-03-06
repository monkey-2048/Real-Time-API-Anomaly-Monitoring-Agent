from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()


class RedisQueue:
    def __init__(self) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self.queue_name = settings.redis_queue_name

    async def enqueue(self, payload: dict[str, Any]) -> None:
        await self._redis.lpush(self.queue_name, json.dumps(payload))

    async def dequeue(self, timeout_seconds: int = 5) -> dict[str, Any] | None:
        item = await self._redis.brpop(self.queue_name, timeout=timeout_seconds)
        if not item:
            return None
        _, raw = item
        return json.loads(raw)

    async def length(self) -> int:
        return int(await self._redis.llen(self.queue_name))

    async def close(self) -> None:
        await self._redis.aclose()
