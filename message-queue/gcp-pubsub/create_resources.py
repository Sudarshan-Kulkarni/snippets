"""Idempotently create the Pub/Sub topic and subscription."""
from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1

from config import get_settings


def main() -> None:
    """Create the topic, then the subscription attached to it, skipping any that exist."""
    settings = get_settings()
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    topic_path = settings.topic_path()
    sub_path = settings.subscription_path()

    try:
        publisher.create_topic(request={"name": topic_path})
        print(f"Created topic: {topic_path}")
    except AlreadyExists:
        print(f"Topic already exists: {topic_path}")

    try:
        subscriber.create_subscription(
            request={"name": sub_path, "topic": topic_path, "ack_deadline_seconds": 30}
        )
        print(f"Created subscription: {sub_path}")
    except AlreadyExists:
        print(f"Subscription already exists: {sub_path}")


if __name__ == "__main__":
    main()
