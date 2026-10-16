"""Shared configuration, loaded from environment variables / a local .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

# Debezium names topics <topic.prefix>.<schema>.<table> (see conf/application.properties).
TOPIC_ID = "snippets.public.customers"
SUBSCRIPTION_ID = "snippets-public-customers-sub"


def require(name: str) -> str:
    """Return a required environment variable or exit with a clear message."""
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def topic_path() -> str:
    return f"projects/{require('GCP_PROJECT_ID')}/topics/{TOPIC_ID}"


def subscription_path() -> str:
    return f"projects/{require('GCP_PROJECT_ID')}/subscriptions/{SUBSCRIPTION_ID}"


def db_connect_kwargs() -> dict:
    """psycopg2 connection settings for Neon (direct, unpooled endpoint)."""
    return {
        "host": require("NEON_HOST"),
        "dbname": require("NEON_DBNAME"),
        "user": require("NEON_USER"),
        "password": require("NEON_PASSWORD"),
        "sslmode": "require",
    }
