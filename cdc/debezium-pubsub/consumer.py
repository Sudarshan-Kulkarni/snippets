"""Read Debezium change events from Pub/Sub and print them in a readable form."""
import argparse
import json
from concurrent.futures import TimeoutError

from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from config import subscription_path

OPS = {"c": "INSERT", "u": "UPDATE", "d": "DELETE", "r": "SNAPSHOT"}


def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    """Decode one Debezium event: ack on success, nack if it can't be parsed."""
    try:
        event = json.loads(message.data.decode("utf-8"))
        # With schemas disabled the payload is the envelope itself; tolerate both shapes.
        payload = event.get("payload", event)
        op = OPS.get(payload.get("op"), payload.get("op"))
        source = payload.get("source", {})
        print(f"{op:<8} {source.get('schema')}.{source.get('table')} lsn={source.get('lsn')}")
        print(f"  before: {payload.get('before')}")
        print(f"  after:  {payload.get('after')}")
    except (ValueError, AttributeError) as exc:
        print(f"Failed to process {message.message_id}: {exc}")
        message.nack()
        return
    message.ack()


def main() -> None:
    """Listen on the subscription until the timeout elapses or the user hits Ctrl+C."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-t", "--timeout", type=float, default=30.0,
                        help="seconds to listen before exiting (default: 30)")
    args = parser.parse_args()

    subscriber = pubsub_v1.SubscriberClient()
    sub = subscription_path()
    streaming_pull = subscriber.subscribe(sub, callback=callback)
    print(f"Listening on {sub} for {args.timeout}s (Ctrl+C to stop)...")

    with subscriber:
        try:
            streaming_pull.result(timeout=args.timeout)
        except (TimeoutError, KeyboardInterrupt):
            streaming_pull.cancel()
            streaming_pull.result()
        except NotFound:
            raise SystemExit(f"Subscription not found: {sub}. Run create_resources.py first.")


if __name__ == "__main__":
    main()
