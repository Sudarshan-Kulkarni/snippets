"""FastAPI Server-Sent Events (SSE) server that streams song lyrics line-by-line."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional, Union

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from db import get_song_with_lines, init_db

INDEX_HTML = Path(__file__).resolve().parent / "index.html"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="SSE Song Lyrics Streamer", lifespan=lifespan)


def format_sse(
    data: dict,
    event: Optional[str] = None,
    event_id: Optional[Union[int, str]] = None,
    retry_ms: Optional[int] = None,
) -> str:
    """Format a dictionary into the standard W3C Server-Sent Events text wire format."""
    lines: list[str] = []
    if retry_ms is not None:
        lines.append(f"retry: {retry_ms}")
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if event is not None:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data)}")
    return "\n".join(lines) + "\n\n"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.get("/stream")
async def stream_lyrics(
    request: Request,
    song: str = Query(default="Venom", description="Song title to stream"),
    interval: float = Query(default=5.0, ge=0.5, le=60.0, description="Seconds between lyric lines"),
    last_id: Optional[int] = Query(default=None, description="Optional manual resume line number"),
    last_event_id: Optional[str] = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    song_data = get_song_with_lines(song)
    if song_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Song '{song}' not found in SQLite.",
        )

    # Determine starting point if reconnecting via standard Last-Event-ID header or query param
    resume_after = 0
    if last_event_id and last_event_id.isdigit():
        resume_after = int(last_event_id)
    elif last_id is not None:
        resume_after = last_id

    async def event_generator() -> AsyncGenerator[str, None]:
        # Tell client to auto-reconnect after 3s if the connection drops
        yield format_sse(
            data={
                "song": song_data["title"],
                "artist": song_data["artist"],
                "total_lines": song_data["total_lines"],
                "resumed_after_line": resume_after,
                "interval_seconds": interval,
            },
            event="connected",
            retry_ms=3000,
        )

        remaining_lines = [
            line for line in song_data["lines"] if line["line_number"] > resume_after
        ]

        for idx, line in enumerate(remaining_lines):
            if await request.is_disconnected():
                break

            # Send the first line right away, then wait `interval` seconds between subsequent lines
            if idx > 0:
                await asyncio.sleep(interval)
                if await request.is_disconnected():
                    break

            payload = {
                "song": song_data["title"],
                "artist": song_data["artist"],
                "line_number": line["line_number"],
                "total_lines": song_data["total_lines"],
                "text": line["text"],
            }
            yield format_sse(
                data=payload,
                event="lyric",
                event_id=line["line_number"],
            )

        if not await request.is_disconnected():
            yield format_sse(
                data={
                    "song": song_data["title"],
                    "artist": song_data["artist"],
                    "message": "Song finished!",
                },
                event="complete",
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
