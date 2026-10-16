# Push Notifications

Snippets showing how to send push notifications to mobile devices and wearables (such as an
Apple Watch via iPhone notification mirroring).

## Core ideas
- **Webhook / HTTP push**: a stateless HTTP `POST` from your application to a provider endpoint,
  which handles delivery to Apple Push Notification service (APNs) or Firebase Cloud Messaging (FCM).
## Implementations
| Folder | Provider | Mechanism | Status |
|---|---|---|---|
| [discord-webhook](discord-webhook/) | Discord | Incoming Webhook (`POST` JSON) | Working |
