"""Idempotently create the Pub/Sub topic Debezium publishes to, and a subscription to read it."""
from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1

from config import subscription_path, topic_path


def main() -> None:
    """Create the topic, then a subscription on it, skipping any that already exist."""
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    topic, sub = topic_path(), subscription_path()

    try:
        publisher.create_topic(request={"name": topic})
        print(f"Created topic: {topic}")
    except AlreadyExists:
        print(f"Topic already exists: {topic}")

    try:
        subscriber.create_subscription(
            request={"name": sub, "topic": topic, "ack_deadline_seconds": 30}
        )
        print(f"Created subscription: {sub}")
    except AlreadyExists:
        print(f"Subscription already exists: {sub}")


if __name__ == "__main__":
    main()
