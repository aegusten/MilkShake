"""Server-Sent Events plumbing shared by the stream endpoints."""

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from fastapi.responses import StreamingResponse

from app.realtime import get_broadcaster

HEARTBEAT_SECONDS = 15.0
RETRY_MS = 3000
PING = "event: ping\ndata: {}\n\n"


def frame(event_id: int, event: dict[str, Any]) -> str:
    data = json.dumps(event, default=str, separators=(",", ":"))
    return f"id: {event_id}\nevent: {event['type']}\ndata: {data}\n\n"


async def open_stream(
    channel: str,
    snapshot: Callable[[], Awaitable[list[dict[str, Any]]]],
    is_disconnected: Callable[[], Awaitable[bool]],
    heartbeat: float = HEARTBEAT_SECONDS,
) -> AsyncIterator[str]:
    """Subscribe first, then send the snapshot, then live events.

    Subscribing before reading the snapshot means an event that lands while
    the snapshot query runs is still delivered; at worst the client sees a
    change twice, which the UI handles by replacing by id. A browser that
    reconnects gets a fresh snapshot, so nothing needs replaying by
    Last-Event-ID.
    """
    subscription = get_broadcaster().subscribe(channel)
    queue: asyncio.Queue = await subscription.__aenter__()
    try:
        yield f"retry: {RETRY_MS}\n\n"
        event_id = 0
        for event in await snapshot():
            event_id += 1
            yield frame(event_id, event)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat)
            except TimeoutError:
                if await is_disconnected():
                    return
                # A named event rather than an SSE comment, because browsers
                # never surface comments to page code. Clients treat a
                # silence much longer than this as a dead connection: a proxy
                # can keep the browser's socket open after the backend is
                # gone, and then nothing else would ever tell them.
                yield PING
                continue
            if event is None:
                return
            event_id += 1
            yield frame(event_id, event)
    finally:
        await subscription.__aexit__(None, None, None)


def sse_response(stream: AsyncIterator[str]) -> StreamingResponse:
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Tells nginx-style proxies not to buffer the stream.
            "X-Accel-Buffering": "no",
        },
    )
