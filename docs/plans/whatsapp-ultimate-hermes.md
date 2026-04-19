# WhatsApp Ultimate — Hermes Integration Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a fully-featured WhatsApp platform adapter for Hermes combining: Hermes's existing Baileys bridge + wacli's local SQLite/FTS5 storage + OpenClaw's whatsapp-ultimate features (polls, reactions, group management, voice notes, stickers).

**Architecture:**

```
WhatsApp Servers
       ↕ (Baileys Web WebSocket)
Node.js Bridge (bridge.js)
  - Full Baileys API (group management, polls, reactions, etc.)
  - SQLite + FTS5 local message storage (like wacli)
  - HTTP endpoints for Python adapter
       ↕ (HTTP REST)
Python Adapter (whatsapp.py)
  - All WhatsApp features exposed as Python methods
  - Connects to Hermes gateway like any other platform
       ↕
Hermes Gateway → Agent tools → User
```

**Tech Stack:**
- Baileys v7 (existing, already installed)
- better-sqlite3 (Node.js SQLite + FTS5)
- Python adapter (existing, extending)
- Hermes gateway platform adapter (existing, extending)

**Key Files:**
- `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js` — Node.js bridge (ENHANCE)
- `~/.hermes/hermes-agent/gateway/platforms/whatsapp.py` — Python adapter (ENHANCE)
- `~/.hermes/hermes-agent/scripts/whatsapp-bridge/package.json` — Add better-sqlite3 dependency

---

## Phase 1: Bridge Enhancements (bridge.js)

### Task 1: Add SQLite + FTS5 local storage to bridge

**Objective:** Store all messages in local SQLite for search and history

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Step 1: Add better-sqlite3 import at top of bridge.js**
```javascript
import Database from 'better-sqlite3';
import path from 'path';
import { mkdirSync, existsSync } from 'fs';
```

**Step 2: Add DB initialization after socket creation**
```javascript
const DB_DIR = path.join(process.env.HOME || '~', '.hermes', 'whatsapp');
mkdirSync(DB_DIR, { recursive: true });
const db = new Database(path.join(DB_DIR, 'messages.db'));

// Enable FTS5
db.exec(`
  CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id TEXT UNIQUE,
    chat_jid TEXT,
    sender_jid TEXT,
    from_me INTEGER,
    text TEXT,
    media_type TEXT,
    media_caption TEXT,
    timestamp INTEGER,
    raw_json TEXT
  );
  CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text, media_caption, chat_jid, sender_jid,
    content='messages', content_rowid='id'
  );
  CREATE TABLE IF NOT EXISTS chats (
    jid TEXT PRIMARY KEY,
    name TEXT,
    kind TEXT,
    last_message_ts INTEGER
  );
  CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, text, media_caption, chat_jid, sender_jid)
    VALUES (new.id, new.text, new.media_caption, new.chat_jid, new.sender_jid);
  END;
`);

// Prepared statements
const insertMsg = db.prepare(`
  INSERT OR IGNORE INTO messages (msg_id, chat_jid, sender_jid, from_me, text, media_type, media_caption, timestamp, raw_json)
  VALUES (@msg_id, @chat_jid, @sender_jid, @from_me, @text, @media_type, @media_caption, @timestamp, @raw_json)
`);
const insertChat = db.prepare(`
  INSERT OR IGNORE INTO chats (jid, name, kind, last_message_ts) VALUES (@jid, @name, @kind, @last_message_ts)
`);
const updateChatTs = db.prepare(`UPDATE chats SET last_message_ts = ? WHERE jid = ?`);
```

**Step 3: Save every incoming/outgoing message to DB**
In the `sock.ev.on('messages.upsert')` handler, after pushing to `messageQueue`, also:
```javascript
// Save to SQLite
try {
  insertMsg.run({
    msg_id: msg.key.id,
    chat_jid: chatId,
    sender_jid: senderId,
    from_me: msg.key.fromMe ? 1 : 0,
    text: textContent || '',
    media_type: msg.message?.imageMessage ? 'image' : msg.message?.videoMessage ? 'video' : msg.message?.documentMessage ? 'document' : msg.message?.audioMessage ? 'audio' : null,
    media_caption: msg.message?.imageMessage?.caption || msg.message?.videoMessage?.caption || null,
    timestamp: msg.messageTimestamp,
    raw_json: JSON.stringify(msg),
  });
  insertChat.run({ jid: chatId, name: chatId.replace(/@.*/, ''), kind: isGroup ? 'group' : 'dm', last_message_ts: msg.messageTimestamp });
} catch (e) {
  // Ignore dupes (UNIQUE constraint)
}
```

**Step 4: Verify**
Run: `curl http://127.0.0.1:<bridge_port>/messages` after receiving a message
Run: SQLite browser — `SELECT COUNT(*) FROM messages` should increase

---

### Task 2: Add FTS5 search endpoint to bridge

**Objective:** Enable fast full-text search of message history

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Add new endpoint after `/chat/:id`:**
```javascript
// Search messages (full-text)
app.get('/search', (req, res) => {
  const { q, chat, limit = 50 } = req.query;
  if (!q) return res.status(400).json({ error: 'q (query) required' });

  let sql = `
    SELECT m.*, snippets(messages_fts, 0, '[', ']', '...', 15) as snippet
    FROM messages_fts f
    JOIN messages m ON m.id = f.rowid
    WHERE messages_fts MATCH ?
  `;
  const params = [q];

  if (chat) {
    sql += ` AND m.chat_jid = ?`;
    params.push(chat);
  }

  sql += ` ORDER BY rank LIMIT ?`;
  params.push(parseInt(limit));

  try {
    const rows = db.prepare(sql).all(...params);
    res.json({ results: rows, count: rows.length });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

**Verify:** `curl "http://127.0.0.1:<port>/search?q=hello&limit=5"`

---

### Task 3: Add backfill endpoint to bridge

**Objective:** Allow Hermes to trigger history backfill on demand

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Add new endpoint:**
```javascript
// Trigger history backfill for a specific chat
app.post('/backfill', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected' });
  }
  const { chatJid, count = 50 } = req.body;
  if (!chatJid) return res.status(400).json({ error: 'chatJid required' });

  try {
    // Baileys sends history sync events automatically on cold start
    // For on-demand backfill, we request sync from the primary device
    const result = await sock.requestHistoryForChat(chatJid, count);
    res.json({ success: true, requested: count });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

**Note:** If `requestHistoryForChat` doesn't exist in Baileys v7, fall back to:
```javascript
// Alternative: just reconnect to trigger full history sync
await sock柜.reconnect();
res.json({ success: true, note: 'reconnected to trigger history sync' });
```

---

### Task 4: Add group management endpoints to bridge

**Objective:** Expose full Baileys group API via HTTP

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Add all these endpoints after `/backfill`:**

```javascript
// Create group
app.post('/group/create', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { name, participants = [] } = req.body;
  if (!name) return res.status(400).json({ error: 'name required' });
  try {
    const meta = await sock.groupCreate(name, participants);
    res.json({ success: true, groupJid: meta.id, metadata: meta });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Rename group
app.post('/group/rename', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, name } = req.body;
  try {
    await sock.groupUpdateSubject(groupJid, name);
    res.json({ success: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Set group description
app.post('/group/description', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, description } = req.body;
  try {
    await sock.groupUpdateDescription(groupJid, description || '');
    res.json({ success: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Add participants
app.post('/group/participants/add', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, participants } = req.body;
  try {
    const result = await sock.groupParticipantsUpdate(groupJid, participants, 'add');
    res.json({ success: true, result });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Remove participants
app.post('/group/participants/remove', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, participants } = req.body;
  try {
    const result = await sock.groupParticipantsUpdate(groupJid, participants, 'remove');
    res.json({ success: true, result });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Promote participants (to admin)
app.post('/group/participants/promote', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, participants } = req.body;
  try {
    const result = await sock.groupParticipantsUpdate(groupJid, participants, 'promote');
    res.json({ success: true, result });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Demote participants (remove admin)
app.post('/group/participants/demote', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, participants } = req.body;
  try {
    const result = await sock.groupParticipantsUpdate(groupJid, participants, 'demote');
    res.json({ success: true, result });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Get invite link
app.get('/group/invite/:jid', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  try {
    const code = await sock.groupInviteCode(req.params.jid);
    res.json({ success: true, code, link: `https://chat.whatsapp.com/${code}` });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Revoke invite link
app.post('/group/invite/revoke', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid } = req.body;
  try {
    const code = await sock.groupRevokeInvite(groupJid);
    res.json({ success: true, code, link: `https://chat.whatsapp.com/${code}` });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Leave group
app.post('/group/leave', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid } = req.body;
  try {
    await sock.groupLeave(groupJid);
    res.json({ success: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Get group info
app.get('/group/info/:jid', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  try {
    const meta = await sock.groupMetadata(req.params.jid);
    res.json(meta);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// List all groups
app.get('/groups', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  try {
    const groups = await sock.groupFetchAllParticipating();
    res.json({ groups: Object.values(groups) });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Set group icon
app.post('/group/icon', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const { groupJid, filePath } = req.body;
  try {
    if (!existsSync(filePath)) return res.status(404).json({ error: 'File not found' });
    const buffer = readFileSync(filePath);
    await sock.updateProfilePicture(groupJid, buffer);
    res.json({ success: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});
```

---

### Task 5: Add reactions endpoint to bridge

**Objective:** Send and receive message reactions

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Add after `/edit`:**
```javascript
// Send reaction
app.post('/react', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chatId, messageId, emoji } = req.body;
  if (!chatId || !messageId || !emoji) {
    return res.status(400).json({ error: 'chatId, messageId, and emoji are required' });
  }
  try {
    const key = { remoteJid: chatId, id: messageId, fromMe: false };
    await sock.sendMessage(chatId, { text: emoji }, { quoted: key });
    res.json({ success: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

**Note:** Baileys v7 reactions use `sendMessage` with a reaction payload. If `text: emoji` with `quoted: key` doesn't work, try:
```javascript
await sock.sendMessage(chatId, {
  reactionMessage: { key, text: emoji }
});
```

---

### Task 6: Add poll endpoint to bridge

**Objective:** Create WhatsApp polls

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Add after `/react`:**
```javascript
// Send poll
app.post('/poll', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chatId, question, options, selectableCount = 1 } = req.body;
  if (!chatId || !question || !options || options.length < 2) {
    return res.status(400).json({ error: 'chatId, question, and at least 2 options required' });
  }
  try {
    const sent = await sock.sendMessage(chatId, {
      poll: {
        name: question,
        selectableCount: selectableCount,
        values: options,
      }
    });
    res.json({ success: true, messageId: sent?.key?.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

---

### Task 7: Add voice note and sticker support to bridge

**Objective:** Send voice notes (OGG/Opus) and stickers (WebP)

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`

**Add to `/send-media` switch case for audio handling (already exists but ensure ptt support):**

The existing `/send-media` already handles audio with `ptt: true` for ogg/opus. Ensure the voice note path works:

**Add sticker send** (new endpoint after `/poll`):
```javascript
// Send sticker
app.post('/sticker', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chatId, filePath } = req.body;
  if (!chatId || !filePath) {
    return res.status(400).json({ error: 'chatId and filePath required' });
  }
  try {
    if (!existsSync(filePath)) {
      return res.status(404).json({ error: `File not found: ${filePath}` });
    }
    const buffer = readFileSync(filePath);
    await sock.sendMessage(chatId, { sticker: buffer, mimetype: 'image/webp' });
    res.json({ success: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

---

### Task 8: Install better-sqlite3 in bridge

**Objective:** Add SQLite dependency to the bridge's node_modules

**File:** `~/.hermes/hermes-agent/scripts/whatsapp-bridge/package.json`

**Add dependency:**
```json
"better-sqlite3": "^11.0.0"
```

**Run:**
```bash
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge && npm install better-sqlite3
```

**Verify:** `ls node_modules/better-sqlite3`

---

## Phase 2: Python Adapter Enhancements (whatsapp.py)

### Task 9: Add all new Python methods to WhatsApp adapter

**Objective:** Expose bridge features as Python async methods

**File:** `~/.hermes/hermes-agent/gateway/platforms/whatsapp.py`

**Add after the existing `send` method:**

```python
async def search_messages(self, query: str, chat_jid: str = None, limit: int = 50) -> Dict[str, Any]:
    """Full-text search of local WhatsApp message history."""
    params = {"q": query, "limit": str(limit)}
    if chat_jid:
        params["chat"] = chat_jid
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{self._bridge_url}/search", params=params) as resp:
            return await resp.json()

async def backfill_chat(self, chat_jid: str, count: int = 50) -> Dict[str, Any]:
    """Request history backfill for a specific chat."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/backfill", json={"chatJid": chat_jid, "count": count}) as resp:
            return await resp.json()

async def create_group(self, name: str, participants: List[str]) -> Dict[str, Any]:
    """Create a WhatsApp group."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/create", json={"name": name, "participants": participants}) as resp:
            return await resp.json()

async def rename_group(self, group_jid: str, name: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/rename", json={"groupJid": group_jid, "name": name}) as resp:
            return await resp.json()

async def set_group_description(self, group_jid: str, description: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/description", json={"groupJid": group_jid, "description": description}) as resp:
            return await resp.json()

async def add_group_participants(self, group_jid: str, participants: List[str]) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/participants/add", json={"groupJid": group_jid, "participants": participants}) as resp:
            return await resp.json()

async def remove_group_participants(self, group_jid: str, participants: List[str]) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/participants/remove", json={"groupJid": group_jid, "participants": participants}) as resp:
            return await resp.json()

async def promote_group_participants(self, group_jid: str, participants: List[str]) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/participants/promote", json={"groupJid": group_jid, "participants": participants}) as resp:
            return await resp.json()

async def demote_group_participants(self, group_jid: str, participants: List[str]) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/participants/demote", json={"groupJid": group_jid, "participants": participants}) as resp:
            return await resp.json()

async def get_group_invite_link(self, group_jid: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{self._bridge_url}/group/invite/{group_jid}") as resp:
            return await resp.json()

async def revoke_group_invite_link(self, group_jid: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/invite/revoke", json={"groupJid": group_jid}) as resp:
            return await resp.json()

async def leave_group(self, group_jid: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/leave", json={"groupJid": group_jid}) as resp:
            return await resp.json()

async def get_group_info(self, group_jid: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{self._bridge_url}/group/info/{group_jid}") as resp:
            return await resp.json()

async def list_groups(self) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{self._bridge_url}/groups") as resp:
            return await resp.json()

async def set_group_icon(self, group_jid: str, file_path: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/group/icon", json={"groupJid": group_jid, "filePath": file_path}) as resp:
            return await resp.json()

async def send_reaction(self, chat_jid: str, message_id: str, emoji: str) -> Dict[str, Any]:
    """Send a reaction emoji to a specific message."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/react", json={"chatId": chat_jid, "messageId": message_id, "emoji": emoji}) as resp:
            return await resp.json()

async def send_poll(self, chat_jid: str, question: str, options: List[str], selectable_count: int = 1) -> Dict[str, Any]:
    """Send a poll to a chat."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/poll", json={
            "chatId": chat_jid, "question": question, "options": options, "selectableCount": selectable_count
        }) as resp:
            return await resp.json()

async def send_sticker(self, chat_jid: str, file_path: str) -> Dict[str, Any]:
    """Send a WebP sticker to a chat."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{self._bridge_url}/sticker", json={"chatId": chat_jid, "filePath": file_path}) as resp:
            return await resp.json()
```

**Note:** Ensure `aiohttp` is imported at the top of `whatsapp.py`. If not:
```python
import aiohttp
```

---

### Task 10: Expose WhatsApp tools to the agent

**Objective:** Register WhatsApp-specific methods as Hermes tools so the agent can call them

**File:** `~/.hermes/hermes-agent/gateway/platforms/whatsapp.py`

**In the `WhatsAppPlatform.__init__` or after the existing tool registration, add:**

```python
# Register WhatsApp-specific tools
self._register_tool("whatsapp_search", self.search_messages, {
    "query": {"type": "string", "description": "Search query"},
    "chat_jid": {"type": "string", "description": "Optional: filter to specific chat JID"},
    "limit": {"type": "integer", "description": "Max results (default 50)"}
})

self._register_tool("whatsapp_backfill", self.backfill_chat, {
    "chat_jid": {"type": "string", "description": "Chat JID to backfill"},
    "count": {"type": "integer", "description": "Number of messages to request"}
})

self._register_tool("whatsapp_create_group", self.create_group, {
    "name": {"type": "string", "description": "Group name"},
    "participants": {"type": "array", "items": {"type": "string"}, "description": "Participant JIDs"}
})

self._register_tool("whatsapp_rename_group", self.rename_group, {
    "group_jid": {"type": "string"},
    "name": {"type": "string"}
})

self._register_tool("whatsapp_set_description", self.set_group_description, {
    "group_jid": {"type": "string"},
    "description": {"type": "string"}
})

self._register_tool("whatsapp_add_participants", self.add_group_participants, {
    "group_jid": {"type": "string"},
    "participants": {"type": "array", "items": {"type": "string"}}
})

self._register_tool("whatsapp_remove_participants", self.remove_group_participants, {
    "group_jid": {"type": "string"},
    "participants": {"type": "array", "items": {"type": "string"}}
})

self._register_tool("whatsapp_promote_participants", self.promote_group_participants, {
    "group_jid": {"type": "string"},
    "participants": {"type": "array", "items": {"type": "string"}}
})

self._register_tool("whatsapp_get_invite_link", self.get_group_invite_link, {
    "group_jid": {"type": "string"}
})

self._register_tool("whatsapp_revoke_invite", self.revoke_group_invite_link, {
    "group_jid": {"type": "string"}
})

self._register_tool("whatsapp_leave_group", self.leave_group, {
    "group_jid": {"type": "string"}
})

self._register_tool("whatsapp_get_group_info", self.get_group_info, {
    "group_jid": {"type": "string"}
})

self._register_tool("whatsapp_list_groups", self.list_groups, {})

self._register_tool("whatsapp_send_reaction", self.send_reaction, {
    "chat_jid": {"type": "string"},
    "message_id": {"type": "string"},
    "emoji": {"type": "string"}
})

self._register_tool("whatsapp_send_poll", self.send_poll, {
    "chat_jid": {"type": "string"},
    "question": {"type": "string"},
    "options": {"type": "array", "items": {"type": "string"}},
    "selectable_count": {"type": "integer"}
})

self._register_tool("whatsapp_send_sticker", self.send_sticker, {
    "chat_jid": {"type": "string"},
    "file_path": {"type": "string"}
})
```

**Note:** The `_register_tool` pattern should match how other tools are registered in the adapter. If the existing adapter doesn't have a `_register_tool` method, add tools to the gateway's tool registry via the standard Hermes tool registration mechanism.

---

### Task 11: Add a WhatsAppUltimate skill document

**Objective:** Document all the new WhatsApp features for the agent

**File:** `~/.hermes/skills/social-media/whatsapp-ultimate/SKILL.md`

**Create skill directory and file:**
```bash
mkdir -p ~/.hermes/skills/social-media/whatsapp-ultimate
```

**Content should include:**
- All features (group management, polls, reactions, search, etc.)
- JID format reference
- Example tool calls
- Tips (voice notes = OGG/Opus, stickers = WebP 512x512, etc.)

---

## Phase 3: Testing & Integration

### Task 12: Restart gateway and verify all endpoints work

**Step 1: Restart the bridge (restart the gateway)**
```bash
sudo systemctl restart hermes-gateway
sleep 5
journalctl -u hermes-gateway -f
```

**Step 2: Test health**
```bash
curl http://127.0.0.1:<bridge_port>/health
```

**Step 3: Test search**
```bash
curl "http://127.0.0.1:<bridge_port>/search?q=hello"
```

**Step 4: Test group creation (from Hermes chat)**
```
Create a WhatsApp group called "AI Agents Test" with myself
```

### Task 13: Test full workflow

From Hermes chat (Telegram or web dashboard):
1. "Search my WhatsApp messages for 'meeting'"
2. "Create a group called X with +91XXXXXXXXX"
3. "Send a poll to that group: 'Which time? Options: 3pm, 4pm, 5pm'"
4. "Add +91XXXXXXXXX to the group"
5. "What's the invite link for the group?"
6. "Search for messages with attachments"

---

## Implementation Order

1. **Task 8** — Install better-sqlite3 (dependency, needed first)
2. **Task 1** — Add SQLite + FTS5 to bridge (foundation)
3. **Task 2** — Add search endpoint
4. **Task 3** — Add backfill endpoint
5. **Task 4** — Add group management endpoints
6. **Task 5** — Add reactions endpoint
7. **Task 6** — Add poll endpoint
8. **Task 7** — Add sticker endpoint
9. **Task 9** — Add Python methods
10. **Task 10** — Register tools with agent
11. **Task 11** — Write skill doc
12. **Task 12-13** — Test everything

---

## Verification Checklist

After implementation:
- [ ] `curl /health` returns connected
- [ ] Messages stored in SQLite (`sqlite3 ~/.hermes/whatsapp/messages.db "SELECT COUNT(*) FROM messages"`)
- [ ] Search returns results: `curl "/search?q=hello"`
- [ ] Group creation works from Hermes chat
- [ ] Poll creation works from Hermes chat
- [ ] Reactions work
- [ ] Voice notes send (as OGG)
- [ ] Stickers send (as WebP)
- [ ] Backfill triggers history sync
- [ ] All groups listed: `curl /groups`
- [ ] Invite link generated
- [ ] Agent can use all tools via natural language
