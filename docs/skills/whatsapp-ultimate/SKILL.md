---
name: whatsapp-ultimate
description: Full-featured WhatsApp integration for Hermes Agent — local SQLite storage, full-text search, group management, polls, reactions, stickers, backfill, and more.
version: 1.0.0
author: Pratik Golechha ( NousResearch/hermes-agent#12605 )
tags: [whatsapp, messaging, groups, polls, reactions, search, local-storage]
hermes:
  platform: whatsapp
  features:
    - local_storage
    - full_text_search
    - backfill
    - group_management
    - polls
    - reactions
    - stickers
    - voice_notes
    - unsend
---

# WhatsApp Ultimate

A comprehensive WhatsApp platform integration for Hermes Agent. Extends the base WhatsApp bridge with **local SQLite storage**, **full-text search**, **group management**, **polls**, **reactions**, **stickers**, and more.

## Features

### Local Message Storage
Every incoming/outgoing WhatsApp message is automatically persisted to a local SQLite database (`~/.hermes/whatsapp/messages.db`) with FTS5 full-text search indexing.

### Full-Text Search
Search all WhatsApp message history instantly using FTS5. Filter by chat or search across all chats.

### Message Backfill
On-demand history sync — fetch any amount of historical messages from WhatsApp servers and store them locally for offline search.

### Group Management (Full)
- Create groups with name and participants
- Rename groups (change subject)
- Set/update group description
- Add/remove participants
- Promote participants to admin
- Get invite links
- Revoke invite links
- Leave groups

### Advanced Messaging
- **Polls**: Send interactive polls to groups or DMs — members vote directly in WhatsApp
- **Reactions**: Send emoji reactions to any message
- **Stickers**: Send .webp sticker files
- **Unsend**: Delete sent messages for everyone

## Prerequisites

- Hermes Agent with WhatsApp bridge enabled
- WhatsApp connected via QR code scan (one-time)
- Node.js 18+ for the bridge
- `better-sqlite3` npm package (auto-installed)

## Configuration

In your `config.yaml`:

```yaml
platforms:
  whatsapp:
    enabled: true
    bridge_port: 3000          # default
    session_path: ~/.hermes/whatsapp/session
    mode: self-chat            # or "bot" for a separate bot number
    reply_prefix: "⚙ *Hermes Agent*\n────────────\n"  # optional
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHATSAPP_ENABLED` | `false` | Enable WhatsApp platform |
| `WHATSAPP_MODE` | `self-chat` | `self-chat` (your number) or `bot` (separate number) |
| `WHATSAPP_BRIDGE_PORT` | `3000` | Bridge HTTP server port |
| `WHATSAPP_ALLOWED_USERS` | `*` | Comma-separated list of allowed phone numbers |
| `WHATSAPP_REPLY_PREFIX` | (none) | Prefix added to outgoing messages |
| `WHATSAPP_REQUIRE_MENTION` | `false` | Require @mention in groups to respond |

## Connecting WhatsApp

1. Enable WhatsApp in `config.yaml`
2. Start/restart the gateway: `hermes restart`
3. Watch the gateway log: `journalctl -u hermes-gateway -f`
4. Scan the QR code shown in the logs with WhatsApp on your phone
5. Done — WhatsApp is now connected

## Available Tools

### Search & Storage

#### `whatsapp_search`
Search message history using full-text search.

```
whatsapp_search(query="project update", chat_id=None, limit=50)
```

#### `whatsapp_backfill`
Fetch historical messages from WhatsApp into local storage.

```
whatsapp_backfill(chat_id="123456789@g.us", limit=100)
```

### Group Management

#### `whatsapp_list_groups`
List all WhatsApp groups with metadata.

```
whatsapp_list_groups()
→ { groups: [{ jid, name, description, size, owner, ... }] }
```

#### `whatsapp_create_group`
Create a new WhatsApp group.

```
whatsapp_create_group(name="Project Team", participants=["+1234567890"])
→ { success: true, groupJid: "..." }
```

#### `whatsapp_group_rename`
Rename a group (change subject).

```
whatsapp_group_rename(chat_id="123456789@g.us", name="New Name")
```

#### `whatsapp_group_description`
Set the group description.

```
whatsapp_group_description(chat_id="123456789@g.us", description="Team discussions")
```

#### `whatsapp_group_participants_add`
Add participants to a group.

```
whatsapp_group_participants_add(chat_id="123456789@g.us", participants=["+1987654321"])
```

#### `whatsapp_group_participants_remove`
Remove participants from a group.

```
whatsapp_group_participants_remove(chat_id="123456789@g.us", participants=["+1987654321"])
```

#### `whatsapp_group_participants_promote`
Promote participants to admin.

```
whatsapp_group_participants_promote(chat_id="123456789@g.us", participants=["+1987654321"])
```

#### `whatsapp_group_invite_link`
Get the group invite link.

```
whatsapp_group_invite_link(chat_id="123456789@g.us")
→ { invite_link: "https://chat.whatsapp.com/..." }
```

#### `whatsapp_group_invite_link_revoke`
Revoke current invite link and generate a new one.

```
whatsapp_group_invite_link_revoke(chat_id="123456789@g.us")
→ { invite_link: "https://chat.whatsapp.com/..." }
```

#### `whatsapp_group_leave`
Leave a group.

```
whatsapp_group_leave(chat_id="123456789@g.us")
```

### Advanced Messaging

#### `whatsapp_send_reaction`
React to a message with an emoji.

```
whatsapp_send_reaction(chat_id="123456789@g.us", message_id="xyz", emoji="👍")
```

#### `whatsapp_send_poll`
Send a poll. Members vote directly in WhatsApp.

```
whatsapp_send_poll(
    chat_id="123456789@g.us",
    question="Which day works best for the meeting?",
    options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    multiple_answers=False
)
```

#### `whatsapp_send_sticker`
Send a .webp sticker file.

```
whatsapp_send_sticker(chat_id="123456789@s.whatsapp.net", file_path="/path/to/sticker.webp")
```

#### `whatsapp_unsend_message`
Delete a sent message for everyone (within 24h limit).

```
whatsapp_unsend_message(chat_id="123456789@s.whatsapp.net", message_id="xyz")
```

## Example Agent Prompts

**Search history:**
> "Search my WhatsApp chats for mentions of the project deadline"

**Create a group:**
> "Create a WhatsApp group called 'Weekend Plans' with +1234567890 and +0987654321"

**Send a poll:**
> "Create a poll in the family group asking 'What's for dinner?' with options Pizza, Tacos, Sushi"

**React to a message:**
> "React 👍 to the last message in the team group"

**Get group invite:**
> "Get the invite link for the project team group"

## Architecture

```
WhatsApp → Baileys (Node.js bridge.js) → Python adapter (whatsapp.py) → Hermes Agent
                    ↓
              SQLite + FTS5
           (~/.hermes/whatsapp/messages.db)
```

### Bridge Endpoints (Node.js)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | GET | FTS5 full-text search |
| `/backfill` | POST | Fetch and store history |
| `/groups` | GET | List all groups |
| `/group/create` | POST | Create group |
| `/group/rename` | POST | Change subject |
| `/group/description` | POST | Set description |
| `/group/participants/add` | POST | Add participants |
| `/group/participants/remove` | POST | Remove participants |
| `/group/participants/promote` | POST | Promote to admin |
| `/group/invite-link` | GET | Get invite link |
| `/group/invite-link/revoke` | POST | Revoke link |
| `/group/leave` | POST | Leave group |
| `/react` | POST | Emoji reaction |
| `/poll` | POST | Create poll |
| `/sticker` | POST | Send sticker |
| `/message` | DELETE | Unsend message |

## Troubleshooting

### QR code not showing
Check the bridge log: `tail -f ~/.hermes/whatsapp/bridge.log`

### "Not connected to WhatsApp"
The bridge process may have crashed. Restart the gateway: `hermes restart`

### Search returns no results
Make sure messages have been received since the upgrade. Use `whatsapp_backfill` to populate old messages.

### better-sqlite3 build errors
```bash
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge
npm install --build-from-source better-sqlite3
```

## Contributing

This feature is part of [PR #12605](https://github.com/NousResearch/hermes-agent/pull/12605) — "feat(whatsapp): WhatsApp Ultimate". See the plan in `docs/plans/whatsapp-ultimate-hermes.md` for full implementation details.
