"""Fan-out of live events to Server-Sent Event streams.

Two interchangeable broadcasters:

- ``InMemoryBroadcaster`` keeps subscribers in this process. Enough for one
  backend worker, and what the tests use.
- ``RedisBroadcaster`` goes through Redis pub/sub, so several workers (or
  several containers) see each other's events. Used when ``REDIS_URL`` is set.

Events are plain dicts. The SSE layer turns them into ``event:``/``data:``
frames; nothing here knows about HTTP.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Protocol

from app.config import get_settings

ADMIN_CHANNEL = "orders:admin"
DISPLAY_CHANNEL = "orders:display"

# A subscriber that falls this far behind is dropped rather than letting its
# queue grow without bound. Its stream ends and the browser reconnects,
# which re-sends the full snapshot.
MAX_QUEUE = 100


def guest_channel(order_id: str) -> str:
    return f"orders:guest:{order_id}"


class Broadcaster(Protocol):
    async def publish(self, channel: str, event: dict[str, Any]) -> None: ...

    def subscribe(self, channel: str) -> Any:
        """Async context manager yielding an ``asyncio.Queue`` of events.
        ``None`` on the queue means the subscription was dropped."""


class InMemoryBroadcaster:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(channel, ())):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                self._subscribers[channel].discard(queue)
                queue.get_nowait()
                queue.put_nowait(None)

    @asynccontextmanager
    async def subscribe(self, channel: str) -> AsyncIterator[asyncio.Queue]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=MAX_QUEUE)
        self._subscribers.setdefault(channel, set()).add(queue)
        try:
            yield queue
        finally:
            self._subscribers.get(channel, set()).discard(queue)

    def subscriber_count(self, channel: str) -> int:
        return len(self._subscribers.get(channel, ()))


class RedisBroadcaster:
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis

        self._redis = redis.from_url(url, decode_responses=True)

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        await self._redis.publish(channel, json.dumps(event, default=str))

    @asynccontextmanager
    async def subscribe(self, channel: str) -> AsyncIterator[asyncio.Queue]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=MAX_QUEUE)
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)

        async def pump() -> None:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    queue.put_nowait(json.loads(message["data"]))
                except asyncio.QueueFull:
                    queue.get_nowait()
                    queue.put_nowait(None)
                    return

        task = asyncio.create_task(pump())
        try:
            yield queue
        finally:
            task.cancel()
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()


_broadcaster: Broadcaster | None = None


def get_broadcaster() -> Broadcaster:
    global _broadcaster
    if _broadcaster is None:
        url = get_settings().REDIS_URL
        _broadcaster = RedisBroadcaster(url) if url else InMemoryBroadcaster()
    return _broadcaster


def set_broadcaster(broadcaster: Broadcaster | None) -> None:
    """Swap the broadcaster. Tests use this to force the in-memory one."""
    global _broadcaster
    _broadcaster = broadcaster
