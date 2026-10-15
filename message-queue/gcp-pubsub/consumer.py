"""Pull messages from the Pub/Sub subscription, process them, and ack."""
import argparse
import json
# Before Python 3.11 this is a distinct class from the builtin TimeoutError,
# and it is what StreamingPullFuture.result(timeout=...) raises.
from concurrent.futures import TimeoutError

from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from config import get_settings


def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    """Process one message: ack on success, nack on failure so it is redelivered."""
    try:
        payload = json.loads(message.data.decode("utf-8"))
        print(f"Received {message.message_id}: {payload} attrs={dict(message.attributes)}")
    except ValueError as exc:  # malformed JSON / bad encoding
        print(f"Failed to process {message.message_id}: {exc}")
        message.nack()
        return
    # Ack only after successful processing; un-acked messages are redelivered.
    message.ack()


def main() -> None:
    """Listen on the subscription until the timeout elapses or the user hits Ctrl+C."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--timeout", type=float, default=15.0,
                        help="seconds to listen before exiting (default: 15)")
    args = parser.parse_args()

    settings = get_settings()
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = settings.subscription_path()

    streaming_pull = subscriber.subscribe(sub_path, callback=callback)
    print(f"Listening on {sub_path} for {args.timeout}s (Ctrl+C to stop)...")

    with subscriber:
        try:
            streaming_pull.result(timeout=args.timeout)
        except (TimeoutError, KeyboardInterrupt):
            streaming_pull.cancel()
            streaming_pull.result()  # wait for shutdown to complete
        except NotFound:
            raise SystemExit(f"Subscription not found: {sub_path}. Run create_resources.py first.")


if __name__ == "__main__":
    main()
