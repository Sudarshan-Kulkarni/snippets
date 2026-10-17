# Server-Sent Events (SSE) → macOS Notifications

## How It Works

1. **SQLite Seed (`db.py`):** On startup, creates `db.sqlite3` (`songs` and `lyric_lines` tables) and seeds the 121 lines of *Eminem — Venom*.
2. **SSE Stream (`server.py`):** `GET /stream?song=Venom&interval=5` returns a FastAPI `StreamingResponse` (`media_type="text/event-stream"`). Every `interval` seconds, the async generator yields an SSE frame:
   ```text
   id: 1
   event: lyric
   data: {"song": "Venom", "artist": "Eminem", "line_number": 1, "total_lines": 121, "text": "..."}

   ```
3. **Disconnect & Resume (`Last-Event-ID`):** If the connection drops, reconnecting with `Last-Event-ID` (or `?last_id=<line_number>`) resumes the stream from the exact next lyric line.
4. **macOS Notification Banner (`index.html`):** The browser listens with `new EventSource(...)` and calls `new Notification(...)` on each `lyric` event.

## Quickstart

```bash
cd push-notifications/sse
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn server:app --host 127.0.0.1 --port 8765
```

Then open **http://localhost:8765** in your browser and click **Start Streaming**, or watch the raw SSE wire stream in your terminal:

```bash
curl -N "http://127.0.0.1:8765/stream?song=Venom&interval=5"
```
