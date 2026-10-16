"""Shared configuration loaded from environment variables / a local .env file."""
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    webhook_url: str
    user_id: Optional[str]


def get_settings() -> Settings:
    """Read Discord webhook settings from the environment."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        raise SystemExit(
            "DISCORD_WEBHOOK_URL is not set. Copy .env.example to .env and fill it in."
        )
    user_id = os.environ.get("DISCORD_USER_ID", "").strip() or None
    return Settings(webhook_url=webhook_url, user_id=user_id)
