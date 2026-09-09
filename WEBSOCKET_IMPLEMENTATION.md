# WhatsAppAPI WebSocket Implementation

## Implemented

### Chat read/unread persistence
- Added `Message.read_at` for dashboard/operator read state.
- Added migration `0002_message_read_at.py`.
- Conversation unread count now uses `read_at IS NULL` for inbound messages.
- Added `POST /api/whatsapp/conversations/<conversation_id>/read/`.
- The read endpoint persists the state and broadcasts `conversation.updated` with `unread_count`.
- React calls the endpoint when a conversation is opened and when an inbound message arrives in the currently open conversation.

### Realtime outbound message lifecycle
- Outbound queued messages broadcast `message.created`.
- `queued -> sending -> sent -> failed` changes broadcast `message.updated`.
- Existing Meta webhook processing continues to broadcast `sent -> delivered -> read`.
- WebSocket payloads include `read_at` without confusing it with WhatsApp delivery `status`.

### Reliability hardening
- Meta message status updates are protected against lifecycle regression caused by stale/out-of-order webhooks.
- Duplicate `extract_whatsapp_error()` definition was removed.

## Architecture

REST is used for initial state and explicit user actions. WebSocket is used to distribute realtime state changes to all connected dashboard clients. The database remains the source of truth.

Campaign pages currently retain their existing REST polling because campaign backend events have not yet been standardized into the dashboard event contract. This can be migrated to WebSocket in a separate step without changing the chat architecture.
