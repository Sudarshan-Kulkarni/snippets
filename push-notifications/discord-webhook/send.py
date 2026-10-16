"""Send a push notification to Discord (and mirrored iPhone / Apple Watch) via Incoming Webhook."""
import argparse
from datetime import datetime, timezone
from typing import Optional

import requests

from config import get_settings


def send_notification(
    webhook_url: str,
    message: str,
    title: Optional[str] = None,
    user_id: Optional[str] = None,
    username: str = "Snippets Bot",
) -> None:
    """POST a message (and optional rich embed) to a Discord incoming webhook."""
    content = f"<@{user_id}> {message}" if user_id else message
    payload: dict = {
        "username": username,
        "content": content,
    }

    if title:
        payload["embeds"] = [
            {
                "title": title,
                "description": message,
                "color": 0x5865F2,  # Discord Blurple
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

    # ?wait=true asks Discord to return the created message object (200) instead of 204 No Content.
    response = requests.post(
        webhook_url,
        params={"wait": "true"},
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    print(f"Sent notification id={data.get('id')} at {data.get('timestamp')}")


def main() -> None:
    """Parse CLI arguments and send a Discord webhook notification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-m",
        "--message",
        default="Hello from snippets! Check your Apple Watch.",
        help="notification body text",
    )
    parser.add_argument(
        "-t",
        "--title",
        default=None,
        help="optional embed title (adds a rich embed card)",
    )
    args = parser.parse_args()

    settings = get_settings()
    send_notification(
        webhook_url=settings.webhook_url,
        message=args.message,
        title=args.title,
        user_id=settings.user_id,
    )


if __name__ == "__main__":
    main()
