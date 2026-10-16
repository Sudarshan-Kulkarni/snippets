# CDC (Change Data Capture)

Snippets showing how to capture row-level changes (insert, update, delete) from a database
and stream them to other systems.

## Core ideas
- **Log-based CDC** reads the database's transaction log (the Postgres WAL), so it sees every
  committed change, including deletes, without polling or triggers.
- Each change becomes an event with an operation type and the `before` and `after` row.
- The events are published to a broker, so downstream consumers can react to them
  (cache invalidation, search indexing, audit logs, replication).

## Implementations
| Folder | Source | Capture tool | Destination | Status |
|---|---|---|---|---|
| [debezium-pubsub](debezium-pubsub/) | Neon Postgres | Debezium Server (Docker) | GCP Pub/Sub | Working |
| `postgres-wal-python` | Postgres | DIY Python reader | GCP Pub/Sub | Idea |
