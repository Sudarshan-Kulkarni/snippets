# Message Queue: GCP Pub/Sub

Basic publish and consume using Google Cloud Pub/Sub

## Setup
```bash
cd message-queue/gcp-pubsub
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

gcloud auth application-default login      # credentials used by the client library
cp .env.example .env                        # then set GCP_PROJECT_ID
gcloud services enable pubsub.googleapis.com --project <your-project-id>

python create_resources.py                          # creates topic + subscription (idempotent)
```

## Run
```bash
python producer.py -n 5      # publish 5 messages
python consumer.py -t 15     # listen for 15s, ack each message
```

## Concepts
- **Topic**: where producers publish.
- **Subscription**: a queue-like view of a topic. Consumers sharing one subscription split the messages between them.
- **Ack**: the consumer confirms processing. Un-acked messages are redelivered after the ack deadline (30s here).


## Not covered yet
Dead-letter queues, retries and backoff, ordering, and exactly-once delivery.
