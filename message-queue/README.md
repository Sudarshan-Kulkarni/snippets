# Message Queue

Snippets showing how to push messages to and read them from a message queue/broker.
Each subfolder is a self-contained implementation with its own dependencies and README.

## Core ideas
- **Producer** publishes messages. **Consumer** reads them.
- The broker decouples the two, so they can run at different times and speeds.
- **Ack/nack**: the consumer confirms processing, and un-acked messages are redelivered.

## Implementations
| Folder | Broker | Where it runs | Status |
|---|---|---|---|
| [gcp-pubsub](gcp-pubsub/) | Google Cloud Pub/Sub | Cloud (free tier) | Basic publish and consume |
| `kafka-local` | Apache Kafka | Local container | Planned |
| `aws-sqs` | Amazon SQS | Cloud (free tier) | Planned |
