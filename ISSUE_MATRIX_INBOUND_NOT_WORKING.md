Title: Matrix gateway can send messages but doesn't receive/respond to incoming messages (mautrix client started incorrectly)

Summary
The Matrix gateway can successfully authenticate and send messages, and logs show initial sync + joined rooms, but it never processes incoming room messages (no replies). Root cause appears to be that the adapter runs manual `client.sync()` calls without starting the mautrix client's event dispatcher, so `add_event_handler(...)` callbacks are never invoked.

Environment
- Hermes Agent gateway Matrix adapter
- mautrix installed (`mautrix[encryption]`)
- Using access token auth
- Non-encrypted rooms (also reproduces in DM)

Reproduction
1. Configure Matrix env vars:
   - MATRIX_HOMESERVER=https://<homeserver>
   - MATRIX_USER_ID=@<bot>:<server>
   - MATRIX_ACCESS_TOKEN=<token>
2. Start gateway
3. Send a message to the bot in a DM / room where the bot is joined

Observed
- Bot can send messages (e.g., gateway-initiated notices succeed)
- Logs show e.g.:
  - "Matrix: using access token for ..."
  - "Matrix: initial sync complete, joined N rooms"
- But bot never replies to user messages
- No handler logs such as `_on_room_message` / `handle_message` are triggered

Expected
- Incoming Matrix `m.room.message` events should invoke registered handlers and feed the gateway message pipeline.

Root cause (hypothesis)
The adapter registers event handlers with `client.add_event_handler(...)`, but only runs `await client.sync(...)` in a custom loop.
In mautrix, event handlers are dispatched by the client's internal syncer started via `client.start(...)` (and stopped via `client.stop()`). Manual `client.sync()` does not dispatch the event handlers.

Proposed fix (minimal)
In `gateway/platforms/matrix.py`:
- After successful auth and handler registration, start the client syncer:
  - `self._client.start(None)`
- On disconnect, stop it:
  - `self._client.stop()`
- Keep the existing periodic loop only for lightweight maintenance (refresh joined room IDs, crypto key share, retry decryptions), but do not rely on it for event dispatch.

Impact
Without this, Matrix gateway appears "connected" but is effectively one-way (outbound only), which blocks DM / room interaction.

Notes
I verified on a real homeserver that adding `client.start(None)` immediately enables replies; the bot began receiving and responding to DM messages.
