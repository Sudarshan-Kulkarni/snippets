"""Shared configuration, loaded from environment variables / a local .env file."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_id: str
    topic_id: str
    subscription_id: str

    def topic_path(self) -> str:
        """Fully qualified topic name: projects/<project>/topics/<topic>."""
        return f"projects/{self.project_id}/topics/{self.topic_id}"

    def subscription_path(self) -> str:
        """Fully qualified subscription name: projects/<project>/subscriptions/<sub>."""
        return f"projects/{self.project_id}/subscriptions/{self.subscription_id}"


def get_settings() -> Settings:
    """Read settings from the environment, exiting with a clear message if misconfigured."""
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        raise SystemExit("GCP_PROJECT_ID is not set. Copy .env.example to .env and fill it in.")
    return Settings(
        project_id=project_id,
        topic_id=os.environ.get("PUBSUB_TOPIC_ID", "snippets-demo-topic"),
        subscription_id=os.environ.get("PUBSUB_SUBSCRIPTION_ID", "snippets-demo-sub"),
    )
