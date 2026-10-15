"""Publish N JSON messages to the Pub/Sub topic."""
import argparse
import json
import time

from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from config import get_settings


def main() -> None:
    """Publish the requested number of messages and print each server-assigned message ID."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--count", type=int, default=5, help="messages to publish")
    args = parser.parse_args()

    settings = get_settings()
    publisher = pubsub_v1.PublisherClient()
    topic_path = settings.topic_path()

    futures = []
    for i in range(args.count):
        payload = {"id": i, "text": f"hello #{i}", "sent_at": time.time()}
        data = json.dumps(payload).encode("utf-8")
        # Extra keyword args become string message attributes.
        futures.append(publisher.publish(topic_path, data, source="producer.py"))

    try:
        for future in futures:
            print(f"Published message id: {future.result()}")  # blocks until the server acks
    except NotFound:
        raise SystemExit(f"Topic not found: {topic_path}. Run create_resources.py first.")


if __name__ == "__main__":
    main()
