#!/usr/bin/env node
/**
 * Hermes Agent WhatsApp Bridge
 *
 * Standalone Node.js process that connects to WhatsApp via Baileys
 * and exposes HTTP endpoints for the Python gateway adapter.
 *
 * Endpoints (matches gateway/platforms/whatsapp.py expectations):
 *   GET  /messages       - Long-poll for new incoming messages
 *   POST /send           - Send a message { chatId, message, replyTo? }
 *   POST /edit           - Edit a sent message { chatId, messageId, message }
 *   POST /send-media     - Send media natively { chatId, filePath, mediaType?, caption?, fileName? }
 *   POST /typing         - Send typing indicator { chatId }
 *   GET  /chat/:id       - Get chat info
 *   GET  /health         - Health check
 *
 * Usage:
 *   node bridge.js --port 3000 --session ~/.hermes/whatsapp/session
 */

import { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, downloadMediaMessage, generateMessageIDV2, jidNormalizedUser } from '@whiskeysockets/baileys';
import express from 'express';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import path from 'path';
import { mkdirSync, readFileSync, writeFileSync, existsSync, readdirSync } from 'fs';
import { randomBytes } from 'crypto';
import qrcode from 'qrcode-terminal';
import QRCode from 'qrcode';
import { matchesAllowedUser, parseAllowedUsers } from './allowlist.js';

import Database from 'better-sqlite3';

// SQLite storage directory
const DB_DIR = path.join(process.env.HOME || '~', '.hermes', 'whatsapp');
mkdirSync(DB_DIR, { recursive: true });
const DB_PATH = path.join(DB_DIR, 'messages.db');

let db = null;

function initDb() {
  db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  
  db.exec(`
    CREATE TABLE IF NOT EXISTS messages (
      id TEXT PRIMARY KEY,
      chat_id TEXT NOT NULL,
      sender_id TEXT,
      sender_name TEXT,
      chat_name TEXT,
      is_group INTEGER DEFAULT 0,
      body TEXT,
      has_media INTEGER DEFAULT 0,
      media_type TEXT,
      media_urls TEXT,
      timestamp INTEGER NOT NULL,
      stored_at INTEGER DEFAULT (unixepoch())
    );
    
    CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
    CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
    
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
      body,
      content='messages',
      content_rowid='rowid'
    );
    
    CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
      INSERT INTO messages_fts(rowid, body) VALUES (new.rowid, new.body);
    END;
    
    CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
      INSERT INTO messages_fts(messages_fts, rowid, body) VALUES('delete', old.rowid, old.body);
    END;
    
    CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
      INSERT INTO messages_fts(messages_fts, rowid, body) VALUES('delete', old.rowid, old.body);
      INSERT INTO messages_fts(rowid, body) VALUES (new.rowid, new.body);
    END;
  `);
  
  console.log('[bridge] SQLite initialized at', DB_PATH);
}

function storeMessage(event) {
  if (!db || !event.messageId) return;
  try {
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO messages 
      (id, chat_id, sender_id, sender_name, chat_name, is_group, body, has_media, media_type, media_urls, timestamp)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      event.messageId,
      event.chatId,
      event.senderId || null,
      event.senderName || null,
      event.chatName || null,
      event.isGroup ? 1 : 0,
      event.body || null,
      event.hasMedia ? 1 : 0,
      event.mediaType || null,
      JSON.stringify(event.mediaUrls || []),
      event.timestamp || Math.floor(Date.now() / 1000)
    );
  } catch (err) {
    console.error('[bridge] DB store error:', err.message);
  }
}

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name, defaultVal) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : defaultVal;
}

const WHATSAPP_DEBUG =
  typeof process !== 'undefined' &&
  process.env &&
  typeof process.env.WHATSAPP_DEBUG === 'string' &&
  ['1', 'true', 'yes', 'on'].includes(process.env.WHATSAPP_DEBUG.toLowerCase());

// When true: SQLite storage, FTS5 search, group mgmt, polls, reactions, stickers
const WHATSAPP_ULTIMATE =
  typeof process !== 'undefined' &&
  process.env &&
  ['1', 'true', 'yes', 'on'].includes(String(process.env.WHATSAPP_ULTIMATE || '').toLowerCase());

const PORT = parseInt(getArg('port', '3000'), 10);
const SESSION_DIR = getArg('session', path.join(process.env.HOME || '~', '.hermes', 'whatsapp', 'session'));
const IMAGE_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'image_cache');
const DOCUMENT_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'document_cache');
const AUDIO_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'audio_cache');
const PAIR_ONLY = args.includes('--pair-only');
const WHATSAPP_MODE = getArg('mode', process.env.WHATSAPP_MODE || 'self-chat'); // "bot" or "self-chat"
const ALLOWED_USERS = parseAllowedUsers(process.env.WHATSAPP_ALLOWED_USERS || '');
const DEFAULT_REPLY_PREFIX = '⚕ *Hermes Agent*\n────────────\n';
const REPLY_PREFIX = process.env.WHATSAPP_REPLY_PREFIX === undefined
  ? DEFAULT_REPLY_PREFIX
  : process.env.WHATSAPP_REPLY_PREFIX.replace(/\\n/g, '\n');

function formatOutgoingMessage(message) {
  // In bot mode, messages come from a different number so the prefix is
  // redundant — the sender identity is already clear.  Only prepend in
  // self-chat mode where bot and user share the same number.
  if (WHATSAPP_MODE !== 'self-chat') return message;
  return REPLY_PREFIX ? `${REPLY_PREFIX}${message}` : message;
}

function normalizeWhatsAppId(value) {
  if (!value) return '';
  return String(value).replace(':', '@');
}

function getMessageContent(msg) {
  const content = msg?.message || {};
  if (content.ephemeralMessage?.message) return content.ephemeralMessage.message;
  if (content.viewOnceMessage?.message) return content.viewOnceMessage.message;
  if (content.viewOnceMessageV2?.message) return content.viewOnceMessageV2.message;
  if (content.documentWithCaptionMessage?.message) return content.documentWithCaptionMessage.message;
  if (content.templateMessage?.hydratedTemplate) return content.templateMessage.hydratedTemplate;
  if (content.buttonsMessage) return content.buttonsMessage;
  if (content.listMessage) return content.listMessage;
  return content;
}

function getContextInfo(messageContent) {
  if (!messageContent || typeof messageContent !== 'object') return {};
  for (const value of Object.values(messageContent)) {
    if (value && typeof value === 'object' && value.contextInfo) {
      return value.contextInfo;
    }
  }
  return {};
}

mkdirSync(SESSION_DIR, { recursive: true });

// Build LID → phone reverse map from session files (lid-mapping-{phone}.json)
function buildLidMap() {
  const map = {};
  try {
    for (const f of readdirSync(SESSION_DIR)) {
      const m = f.match(/^lid-mapping-(\d+)\.json$/);
      if (!m) continue;
      const phone = m[1];
      const lid = JSON.parse(readFileSync(path.join(SESSION_DIR, f), 'utf8'));
      if (lid) map[String(lid)] = phone;
    }
  } catch {}
  return map;
}
let lidToPhone = buildLidMap();

const logger = pino({ level: 'warn' });

// Message queue for polling
const messageQueue = [];
const MAX_QUEUE_SIZE = 100;

// Track recently sent message IDs to prevent echo-back loops with media
const recentlySentIds = new Set();
const MAX_RECENT_IDS = 50;

let sock = null;
let connectionState = 'disconnected';
let lastQrData = null; // raw QR string for /qr-image endpoint
if (WHATSAPP_ULTIMATE) {
  initDb();
}

async function startSocket() {
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    browser: ['Hermes Agent', 'Chrome', '120.0'],
    syncFullHistory: false,
    markOnlineOnConnect: false,
    // Required for Baileys 7.x: without this, incoming messages that need
    // E2EE session re-establishment are silently dropped (msg.message === null)
    getMessage: async (key) => {
      // We don't maintain a message store, so return a placeholder.
      // This is enough for Baileys to complete the retry handshake.
      return { conversation: '' };
    },
  });

  sock.ev.on('creds.update', () => { saveCreds(); lidToPhone = buildLidMap(); });

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      lastQrData = qr;
      console.log('\n📱 Scan this QR code with WhatsApp on your phone:\n');
      qrcode.generate(qr, { small: true });
      console.log('\nWaiting for scan...\n');
    }

    if (connection === 'close') {
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      connectionState = 'disconnected';

      if (reason === DisconnectReason.loggedOut) {
        console.log('❌ Logged out. Delete session and restart to re-authenticate.');
        process.exit(1);
      } else {
        // 515 = restart requested (common after pairing). Always reconnect.
        if (reason === 515) {
          console.log('↻ WhatsApp requested restart (code 515). Reconnecting...');
        } else {
          console.log(`⚠️  Connection closed (reason: ${reason}). Reconnecting in 3s...`);
        }
        setTimeout(startSocket, reason === 515 ? 1000 : 3000);
      }
    } else if (connection === 'open') {
      connectionState = 'connected';
      console.log('✅ WhatsApp connected!');
      if (PAIR_ONLY) {
        console.log('✅ Pairing complete. Credentials saved.');
        // Give Baileys a moment to flush creds, then exit cleanly
        setTimeout(() => process.exit(0), 2000);
      }
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    // In self-chat mode, your own messages commonly arrive as 'append' rather
    // than 'notify'. Accept both and filter agent echo-backs below.
    if (type !== 'notify' && type !== 'append') return;

    const botIds = Array.from(new Set([
      normalizeWhatsAppId(sock.user?.id),
      normalizeWhatsAppId(sock.user?.lid),
    ].filter(Boolean)));

    for (const msg of messages) {
      if (!msg.message) continue;

      const chatId = msg.key.remoteJid;
      if (WHATSAPP_DEBUG) {
        try {
          console.log(JSON.stringify({
            event: 'upsert', type,
            fromMe: !!msg.key.fromMe, chatId,
            senderId: msg.key.participant || chatId,
            messageKeys: Object.keys(msg.message || {}),
          }));
        } catch {}
      }
      const senderId = msg.key.participant || chatId;
      const isGroup = chatId.endsWith('@g.us');
      const senderNumber = senderId.replace(/@.*/, '');

      // Handle fromMe messages based on mode
      if (msg.key.fromMe) {
        if (isGroup || chatId.includes('status')) continue;

        if (WHATSAPP_MODE === 'bot') {
          // Bot mode: separate number. ALL fromMe are echo-backs of our own replies — skip.
          continue;
        }

        // Self-chat mode: only allow messages in the user's own self-chat
        // WhatsApp now uses LID (Linked Identity Device) format: 67427329167522@lid
        // AND classic format: 34652029134@s.whatsapp.net
        // sock.user has both: { id: "number:10@s.whatsapp.net", lid: "lid_number:10@lid" }
        const myNumber = (sock.user?.id || '').replace(/:.*@/, '@').replace(/@.*/, '');
        const myLid = (sock.user?.lid || '').replace(/:.*@/, '@').replace(/@.*/, '');
        const chatNumber = chatId.replace(/@.*/, '');
        const isSelfChat = (myNumber && chatNumber === myNumber) || (myLid && chatNumber === myLid);
        if (!isSelfChat) continue;
      }

      // Check allowlist for messages from others (resolve LID ↔ phone aliases)
      if (!msg.key.fromMe && !matchesAllowedUser(senderId, ALLOWED_USERS, SESSION_DIR)) {
        try {
          console.log(JSON.stringify({
            event: 'ignored',
            reason: 'allowlist_mismatch',
            chatId,
            senderId,
          }));
        } catch {}
        continue;
      }

      const messageContent = getMessageContent(msg);
      const contextInfo = getContextInfo(messageContent);
      const mentionedIds = Array.from(new Set((contextInfo?.mentionedJid || []).map(normalizeWhatsAppId).filter(Boolean)));
      const quotedParticipant = normalizeWhatsAppId(contextInfo?.participant || contextInfo?.remoteJid || '');

      // Extract message body
      let body = '';
      let hasMedia = false;
      let mediaType = '';
      const mediaUrls = [];

      if (messageContent.conversation) {
        body = messageContent.conversation;
      } else if (messageContent.extendedTextMessage?.text) {
        body = messageContent.extendedTextMessage.text;
      } else if (messageContent.imageMessage) {
        body = messageContent.imageMessage.caption || '';
        hasMedia = true;
        mediaType = 'image';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = messageContent.imageMessage.mimetype || 'image/jpeg';
          const extMap = { 'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif' };
          const ext = extMap[mime] || '.jpg';
          mkdirSync(IMAGE_CACHE_DIR, { recursive: true });
          const filePath = path.join(IMAGE_CACHE_DIR, `img_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download image:', err.message);
        }
      } else if (messageContent.videoMessage) {
        body = messageContent.videoMessage.caption || '';
        hasMedia = true;
        mediaType = 'video';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = messageContent.videoMessage.mimetype || 'video/mp4';
          const ext = mime.includes('mp4') ? '.mp4' : '.mkv';
          mkdirSync(DOCUMENT_CACHE_DIR, { recursive: true });
          const filePath = path.join(DOCUMENT_CACHE_DIR, `vid_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download video:', err.message);
        }
      } else if (messageContent.audioMessage || messageContent.pttMessage) {
        hasMedia = true;
        mediaType = messageContent.pttMessage ? 'ptt' : 'audio';
        try {
          const audioMsg = messageContent.pttMessage || messageContent.audioMessage;
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = audioMsg.mimetype || 'audio/ogg';
          const ext = mime.includes('ogg') ? '.ogg' : mime.includes('mp4') ? '.m4a' : '.ogg';
          mkdirSync(AUDIO_CACHE_DIR, { recursive: true });
          const filePath = path.join(AUDIO_CACHE_DIR, `aud_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download audio:', err.message);
        }
      } else if (messageContent.documentMessage) {
        body = messageContent.documentMessage.caption || '';
        hasMedia = true;
        mediaType = 'document';
        const fileName = messageContent.documentMessage.fileName || 'document';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          mkdirSync(DOCUMENT_CACHE_DIR, { recursive: true });
          const safeFileName = path.basename(fileName).replace(/[^a-zA-Z0-9._-]/g, '_');
          const filePath = path.join(DOCUMENT_CACHE_DIR, `doc_${randomBytes(6).toString('hex')}_${safeFileName}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download document:', err.message);
        }
      }

      // For media without caption, use a placeholder so the API message is never empty
      if (hasMedia && !body) {
        body = `[${mediaType} received]`;
      }

      // Ignore Hermes' own reply messages in self-chat mode to avoid loops.
      if (msg.key.fromMe && ((REPLY_PREFIX && body.startsWith(REPLY_PREFIX)) || recentlySentIds.has(msg.key.id))) {
        if (WHATSAPP_DEBUG) {
          try { console.log(JSON.stringify({ event: 'ignored', reason: 'agent_echo', chatId, messageId: msg.key.id })); } catch {}
        }
        continue;
      }

      // Skip empty messages
      if (!body && !hasMedia) {
        if (WHATSAPP_DEBUG) {
          try { 
            console.log(JSON.stringify({ event: 'ignored', reason: 'empty', chatId, messageKeys: Object.keys(msg.message || {}) })); 
          } catch (err) {
            console.error('Failed to log empty message event:', err);
          }
        }
        continue;
      }

      const event = {
        messageId: msg.key.id,
        chatId,
        senderId,
        senderName: msg.pushName || senderNumber,
        chatName: isGroup ? (chatId.split('@')[0]) : (msg.pushName || senderNumber),
        isGroup,
        body,
        hasMedia,
        mediaType,
        mediaUrls,
        mentionedIds,
        quotedParticipant,
        botIds,
        timestamp: msg.messageTimestamp,
      };

      messageQueue.push(event);
      storeMessage(event);
      if (messageQueue.length > MAX_QUEUE_SIZE) {
        messageQueue.shift();
      }
    }
  });
}

// HTTP server
const app = express();
app.use(express.json());

// Poll for new messages (long-poll style)
app.get('/messages', (req, res) => {
  const msgs = messageQueue.splice(0, messageQueue.length);
  res.json(msgs);
});

// Send a message
app.post('/send', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, message, replyTo } = req.body;
  if (!chatId || !message) {
    return res.status(400).json({ error: 'chatId and message are required' });
  }

  try {
    const sent = await sock.sendMessage(chatId, { text: formatOutgoingMessage(message) });

    // Track sent message ID to prevent echo-back loops
    if (sent?.key?.id) {
      recentlySentIds.add(sent.key.id);
      if (recentlySentIds.size > MAX_RECENT_IDS) {
        recentlySentIds.delete(recentlySentIds.values().next().value);
      }
    }

    res.json({ success: true, messageId: sent?.key?.id });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Edit a previously sent message
app.post('/edit', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, messageId, message } = req.body;
  if (!chatId || !messageId || !message) {
    return res.status(400).json({ error: 'chatId, messageId, and message are required' });
  }

  try {
    const key = { id: messageId, fromMe: true, remoteJid: chatId };
    await sock.sendMessage(chatId, { text: formatOutgoingMessage(message), edit: key });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// MIME type map and media type inference for /send-media
const MIME_MAP = {
  jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
  webp: 'image/webp', gif: 'image/gif',
  mp4: 'video/mp4', mov: 'video/quicktime', avi: 'video/x-msvideo',
  mkv: 'video/x-matroska', '3gp': 'video/3gpp',
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
};

function inferMediaType(ext) {
  if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext)) return 'image';
  if (['mp4', 'mov', 'avi', 'mkv', '3gp'].includes(ext)) return 'video';
  if (['ogg', 'opus', 'mp3', 'wav', 'm4a'].includes(ext)) return 'audio';
  return 'document';
}

// Send media (image, video, document) natively
app.post('/send-media', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, filePath, mediaType, caption, fileName } = req.body;
  if (!chatId || !filePath) {
    return res.status(400).json({ error: 'chatId and filePath are required' });
  }

  try {
    if (!existsSync(filePath)) {
      return res.status(404).json({ error: `File not found: ${filePath}` });
    }

    const buffer = readFileSync(filePath);
    const ext = filePath.toLowerCase().split('.').pop();
    const type = mediaType || inferMediaType(ext);
    let msgPayload;

    switch (type) {
      case 'image':
        msgPayload = { image: buffer, caption: caption || undefined, mimetype: MIME_MAP[ext] || 'image/jpeg' };
        break;
      case 'video':
        msgPayload = { video: buffer, caption: caption || undefined, mimetype: MIME_MAP[ext] || 'video/mp4' };
        break;
      case 'audio': {
        const audioMime = (ext === 'ogg' || ext === 'opus') ? 'audio/ogg; codecs=opus' : 'audio/mpeg';
        msgPayload = { audio: buffer, mimetype: audioMime, ptt: ext === 'ogg' || ext === 'opus' };
        break;
      }
      case 'document':
      default:
        msgPayload = {
          document: buffer,
          fileName: fileName || path.basename(filePath),
          caption: caption || undefined,
          mimetype: MIME_MAP[ext] || 'application/octet-stream',
        };
        break;
    }

    const sent = await sock.sendMessage(chatId, msgPayload);

    // Track sent message ID to prevent echo-back loops
    if (sent?.key?.id) {
      recentlySentIds.add(sent.key.id);
      if (recentlySentIds.size > MAX_RECENT_IDS) {
        recentlySentIds.delete(recentlySentIds.values().next().value);
      }
    }

    res.json({ success: true, messageId: sent?.key?.id });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Search endpoint ───────────────────────────────────────────────
app.get('/search', (req, res) => {
  if (!WHATSAPP_ULTIMATE) {
    return res.status(403).json({ error: 'Search requires WHATSAPP_ULTIMATE=true. Run "hermes setup" to enable.' });
  }
  const { q, chat_id, limit = 50 } = req.query;
  if (!q) return res.status(400).json({ error: 'q is required' });
  if (!db) return res.status(503).json({ error: 'Database not initialized. Is WHATSAPP_ULTIMATE=true?' });
  
  try {
    let rows;
    if (chat_id) {
      const stmt = db.prepare(`
        SELECT m.* FROM messages m
        JOIN messages_fts fts ON m.rowid = fts.rowid
        WHERE messages_fts MATCH ? AND m.chat_id = ?
        ORDER BY m.timestamp DESC LIMIT ?
      `);
      rows = stmt.all(q, chat_id, parseInt(limit));
    } else {
      const stmt = db.prepare(`
        SELECT m.* FROM messages m
        JOIN messages_fts fts ON m.rowid = fts.rowid
        WHERE messages_fts MATCH ?
        ORDER BY m.timestamp DESC LIMIT ?
      `);
      rows = stmt.all(q, parseInt(limit));
    }
    
    const results = rows.map(r => ({
      messageId: r.id,
      chatId: r.chat_id,
      senderId: r.sender_id,
      senderName: r.sender_name,
      chatName: r.chat_name,
      isGroup: !!r.is_group,
      body: r.body,
      hasMedia: !!r.has_media,
      mediaType: r.media_type,
      mediaUrls: JSON.parse(r.media_urls || '[]'),
      timestamp: r.timestamp,
    }));
    
    res.json({ results, count: results.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Backfill endpoint ──────────────────────────────────────────────
// Baileys v7 uses fetchMessageHistory(count, oldestMsgKey, oldestMsgTimestamp)
// which requires a starting message. We use the oldest stored message as anchor.
app.post('/backfill', async (req, res) => {
  if (!WHATSAPP_ULTIMATE) {
    return res.status(403).json({ error: 'Backfill requires WHATSAPP_ULTIMATE=true. Run "hermes setup" to enable.' });
  }
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chat_id, limit = 50 } = req.body;
  if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

  if (!db) return res.status(503).json({ error: 'SQLite not available' });

  try {
    // Find oldest stored message for this chat to use as anchor
    const oldest = db.prepare(
      'SELECT id, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp ASC LIMIT 1'
    ).get(chat_id);

    let oldestMsgKey = null;
    let oldestMsgTimestamp = Math.floor(Date.now() / 1000); // default: now

    if (oldest) {
      oldestMsgKey = { remoteJid: chat_id, id: oldest.id, fromMe: false };
      oldestMsgTimestamp = oldest.timestamp;
    }

    // Baileys v7: fetchMessageHistory(count, oldestMsgKey, oldestMsgTimestamp)
    // Requires a valid oldestMsgKey — crashes if null is passed.
    // If no anchor exists, skip backfill and tell user to receive messages first.
    if (!oldest) {
      return res.json({
        success: false,
        error: 'No anchor message found. Receive some messages first in this chat, then try backfill again.',
        stored: 0,
      });
    }

    // Baileys v7: fetchMessageHistory(count, oldestMsgKey, oldestMsgTimestamp)
    // Requests older messages from the phone relative to the anchor
    const fetchedMessages = await sock.fetchMessageHistory(
      parseInt(limit),
      { remoteJid: chat_id, id: oldest.id, fromMe: false },
      oldest.timestamp
    );

    let stored = 0;
    for (const msg of fetchedMessages || []) {
      if (!msg?.key?.id) continue;
      const chatId = msg.key.remoteJid;
      if (!chatId) continue;

      const isGroup = chatId.endsWith('@g.us');
      const senderId = msg.key.participant || chatId;
      const senderNumber = senderId.replace(/@.*/, '');
      const messageContent = getMessageContent(msg);

      let body = '';
      let hasMedia = false;
      let mediaType = '';
      const mediaUrls = [];

      if (messageContent.conversation) body = messageContent.conversation;
      else if (messageContent.extendedTextMessage?.text) body = messageContent.extendedTextMessage.text;
      else if (messageContent.imageMessage) {
        body = messageContent.imageMessage.caption || '';
        hasMedia = true; mediaType = 'image';
      } else if (messageContent.videoMessage) {
        body = messageContent.videoMessage.caption || '';
        hasMedia = true; mediaType = 'video';
      } else if (messageContent.audioMessage || messageContent.pttMessage) {
        hasMedia = true; mediaType = messageContent.pttMessage ? 'ptt' : 'audio';
      } else if (messageContent.documentMessage) {
        body = messageContent.documentMessage.caption || '';
        hasMedia = true; mediaType = 'document';
      }

      if (hasMedia && !body) body = `[${mediaType} received]`;
      if (!body && !hasMedia) continue;

      const event = {
        messageId: msg.key.id,
        chatId,
        senderId,
        senderName: msg.pushName || senderNumber,
        chatName: isGroup ? chatId.split('@')[0] : (msg.pushName || senderNumber),
        isGroup,
        body,
        hasMedia,
        mediaType,
        mediaUrls,
        mentionedIds: [],
        quotedParticipant: '',
        botIds: [],
        timestamp: msg.messageTimestamp,
      };

      storeMessage(event);
      stored++;
    }

    res.json({ success: true, stored, total: fetchedMessages?.length || 0, anchor: oldestMsgKey ? 'used oldest stored message as anchor' : 'no anchor (no stored messages)' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Group management endpoints ─────────────────────────────────────
// All group operations use sock.query() directly — Baileys v7 separates
// group methods into makeGroupsSocket which is NOT part of makeWASocket chain.

// Low-level group IQ query helper
async function groupQuery(jid, type, content) {
  return sock.query({
    tag: 'iq',
    attrs: { type, xmlns: 'w:g2', to: jid },
    content,
  });
}

// Parse group metadata from WhatsApp binary response
function parseGroupMetadata(result) {
  const groupNode = result?.content?.[0];
  if (!groupNode) return null;

  // content can be an Array, Map, or have numeric keys — normalize to array
  const contentArr = Array.isArray(groupNode.content)
    ? groupNode.content
    : (groupNode.content instanceof Map
      ? Array.from(groupNode.content.values())
      : []);

  const getChild = (tag) => {
    const found = contentArr.find(n => n && n.tag === tag);
    if (found) return found;
    // also check attrs (some values stored directly in attrs)
    return groupNode.attrs?.[tag] ? { attrs: groupNode.attrs, tag } : null;
  };
  const getText = (tag) => {
    const n = getChild(tag);
    if (!n) return '';
    // content can be Buffer, string, or nested node
    if (n.content) {
      const c = Array.isArray(n.content) ? n.content[0] : n.content;
      if (Buffer.isBuffer(c)) return c.toString('utf-8');
      if (typeof c === 'string') return c;
      if (c && typeof c === 'object' && c.toString) return c.toString();
    }
    return n.attrs?.value || '';
  };
  const participants = contentArr
    .filter(n => n && n.tag === 'participant')
    .map(n => ({ id: String(n.attrs?.jid || ''), admin: n.attrs?.type === 'admin' ? 'admin' : null }));

  return {
    id: groupNode.attrs?.id ? `${groupNode.attrs.id}@g.us` : jid,
    subject: groupNode.attrs?.subject || getText('subject'),
    subjectOwner: groupNode.attrs?.s_o,
    subjectTime: Number(groupNode.attrs?.s_t || 0),
    description: getText('description'),
    size: participants.length,
    creation: Number(groupNode.attrs?.creation || 0),
    owner: groupNode.attrs?.creator ? jidNormalizedUser(groupNode.attrs.creator) : undefined,
    restrict: !!getChild('locked'),
    announce: !!getChild('announcement'),
    participants,
    ephemeralExpiration: getChild('ephemeral')?.attrs?.expiration,
  };
}

app.post('/group/create', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { name, participants = [] } = req.body;
  if (!name) return res.status(400).json({ error: 'name is required' });

  try {
    const key = generateMessageIDV2();
    const result = await groupQuery('@g.us', 'set', [
      {
        tag: 'create',
        attrs: { subject: name, key },
        content: participants.map(jid => ({
          tag: 'participant',
          attrs: { jid }
        }))
      }
    ]);
    const meta = parseGroupMetadata(result);
    res.json({ success: true, groupJid: meta?.id || result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/groups', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const result = await sock.query({
      tag: 'iq',
      attrs: { to: '@g.us', xmlns: 'w:g2', type: 'get' },
      content: [{ tag: 'participating', attrs: {}, content: [{ tag: 'participants', attrs: {} }, { tag: 'description', attrs: {} }] }]
    });
    const data = {};
    const groupsChild = result?.content?.find(n => n.tag === 'groups');
    if (groupsChild) {
      for (const groupNode of groupsChild.content || []) {
        if (groupNode.tag === 'group') {
          const meta = parseGroupMetadata({ content: [groupNode] });
          if (meta) data[meta.id] = meta;
        }
      }
    }
    const groupsList = Object.entries(data).map(([jid, meta]) => ({
      jid: String(jid || ''),
      name: String(meta.subject || jid || ''),
      description: String(meta.description || ''),
      size: Number(meta.size || 0),
      created: Number(meta.creation || 0),
      owner: meta.owner ? String(meta.owner) : null,
      restrict: Boolean(meta.restrict),
      announce: Boolean(meta.announce),
    }));
    try {
      res.json({ groups: groupsList });
    } catch (e) {
      res.status(500).json({ error: 'Serialization failed: ' + e.message });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/rename', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, name } = req.body;
  if (!chat_id || !name) return res.status(400).json({ error: 'chat_id and name are required' });

  try {
    await groupQuery(chat_id, 'set', [
      { tag: 'subject', attrs: {}, content: Buffer.from(name, 'utf-8') }
    ]);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/description', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, description } = req.body;
  if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

  try {
    const content = description
      ? [{ tag: 'description', attrs: { id: generateMessageIDV2().slice(0, 12) }, content: [{ tag: 'body', attrs: {}, content: Buffer.from(description, 'utf-8') }] }]
      : [{ tag: 'description', attrs: { delete: 'true' } }];
    await groupQuery(chat_id, 'set', content);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/participants/add', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, participants } = req.body;
  if (!chat_id || !participants?.length) {
    return res.status(400).json({ error: 'chat_id and participants[] are required' });
  }

  try {
    await groupQuery(chat_id, 'set', [
      {
        tag: 'add',
        attrs: {},
        content: participants.map(jid => ({ tag: 'participant', attrs: { jid } }))
      }
    ]);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/participants/remove', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, participants } = req.body;
  if (!chat_id || !participants?.length) {
    return res.status(400).json({ error: 'chat_id and participants[] are required' });
  }

  try {
    await groupQuery(chat_id, 'set', [
      {
        tag: 'remove',
        attrs: {},
        content: participants.map(jid => ({ tag: 'participant', attrs: { jid } }))
      }
    ]);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/participants/promote', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, participants } = req.body;
  if (!chat_id || !participants?.length) {
    return res.status(400).json({ error: 'chat_id and participants[] are required' });
  }

  try {
    await groupQuery(chat_id, 'set', [
      {
        tag: 'promote',
        attrs: {},
        content: participants.map(jid => ({ tag: 'participant', attrs: { jid } }))
      }
    ]);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/group/invite-link', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id } = req.query;
  if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

  try {
    const result = await groupQuery(chat_id, 'get', [{ tag: 'invite', attrs: {} }]);
    const inviteNode = result?.content?.find(n => n.tag === 'invite');
    const code = inviteNode?.attrs?.code;
    if (!code) return res.status(404).json({ error: 'No invite code found' });
    res.json({ invite_link: `https://chat.whatsapp.com/${code}` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/invite-link/revoke', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id } = req.body;
  if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

  try {
    const result = await groupQuery(chat_id, 'set', [{ tag: 'revoke', attrs: {}, content: [{ tag: 'invite', attrs: {} }] }]);
    const inviteNode = result?.content?.find(n => n.tag === 'invite') || result?.content?.[0];
    const code = inviteNode?.attrs?.code;
    res.json({ success: true, invite_link: code ? `https://chat.whatsapp.com/${code}` : null });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/group/leave', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id } = req.body;
  if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

  try {
    await groupQuery('@g.us', 'set', [
      { tag: 'leave', attrs: {}, content: [{ tag: 'group', attrs: { id: chat_id.replace('@g.us', '') } }] }
    ]);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Reaction endpoint ──────────────────────────────────────────────
app.post('/react', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, message_id, emoji } = req.body;
  if (!chat_id || !message_id || !emoji) {
    return res.status(400).json({ error: 'chat_id, message_id, and emoji are required' });
  }

  try {
    // Baileys v7: sendMessage with react uses { react: { text, key } }
    // The key must match the target message
    const key = { remoteJid: chat_id, id: message_id, fromMe: false };
    await sock.sendMessage(chat_id, { react: { text: emoji, key } });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Poll endpoint ─────────────────────────────────────────────────
app.post('/poll', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, question, options, multiple_answers = false } = req.body;
  if (!chat_id || !question || !options?.length || options.length < 2) {
    return res.status(400).json({ error: 'chat_id, question, and at least 2 options are required' });
  }

  try {
    // Baileys v7: sendMessage with poll uses high-level { poll: { name, values, selectableCount } }
    // normalizeMessage converts this to the correct proto format
    await sock.sendMessage(chat_id, {
      poll: {
        name: question,
        values: options,
        selectableCount: multiple_answers ? options.length : 1,
      }
    });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Sticker endpoint ──────────────────────────────────────────────
app.post('/sticker', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, file_path } = req.body;
  if (!chat_id || !file_path) {
    return res.status(400).json({ error: 'chat_id and file_path are required' });
  }
  
  try {
    if (!existsSync(file_path)) {
      return res.status(404).json({ error: `File not found: ${file_path}` });
    }
    
    const buffer = readFileSync(file_path);
    const ext = file_path.toLowerCase().split('.').pop();
    
    let sticker;
    if (ext === 'webp') {
      sticker = { sticker: buffer };
    } else {
      return res.status(400).json({ error: 'Only .webp files are supported for stickers. Convert image to .webp first.' });
    }
    
    sticker.sticker.mimetype = 'image/webp';
    const sent = await sock.sendMessage(chat_id, sticker);
    res.json({ success: true, messageId: sent?.key?.id });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─── Unsend (delete for everyone) endpoint ─────────────────────────
app.delete('/message', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, message_id } = req.body;
  if (!chat_id || !message_id) {
    return res.status(400).json({ error: 'chat_id and message_id are required' });
  }
  
  try {
    const key = { remoteJid: chat_id, id: message_id };
    await sock.sendMessage(chat_id, { delete: key });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Typing indicator
app.post('/typing', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  const { chat_id, is_typing } = req.body;
  if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });
  
  try {
    await sock.sendMessage(chat_id, {
      presence: is_typing !== false ? 'composing' : 'paused'
    });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Chat info
app.get('/chat/:id', async (req, res) => {
  const chatId = req.params.id;
  const isGroup = chatId.endsWith('@g.us');

  if (isGroup && sock) {
    try {
      const metadata = await sock.groupMetadata(chatId);
      return res.json({
        name: metadata.subject,
        isGroup: true,
        participants: metadata.participants.map(p => p.id),
      });
    } catch {
      // Fall through to default
    }
  }

  res.json({
    name: chatId.replace(/@.*/, ''),
    isGroup,
    participants: [],
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: connectionState,
    queueLength: messageQueue.length,
    uptime: process.uptime(),
  });
});

// QR code as PNG image (for scanning when bridge is run in background)
app.get('/qr-image', async (req, res) => {
  if (!lastQrData) {
    return res.status(404).json({ error: 'No QR code available. Bridge may already be connected or QR expired.' });
  }
  try {
    const png = await QRCode.toBuffer(lastQrData, { type: 'png', width: 400, margin: 2 });
    res.set('Content-Type', 'image/png');
    res.set('Cache-Control', 'no-store');
    res.send(png);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Debug: list available socket methods
app.get('/debug/methods', (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Not connected' });
  const proto = Object.getPrototypeOf(sock);
  const ownMethods = Object.getOwnPropertyNames(proto).filter(m => !m.startsWith('_') && typeof sock[m] === 'function');
  res.json({ methods: ownMethods.sort() });
});

// Start
if (PAIR_ONLY) {
  // Pair-only mode: just connect, show QR, save creds, exit. No HTTP server.
  console.log('📱 WhatsApp pairing mode');
  console.log(`📁 Session: ${SESSION_DIR}`);
  console.log();
  startSocket();
} else {
  app.listen(PORT, '127.0.0.1', () => {
    const ultimateTag = WHATSAPP_ULTIMATE ? ' 🌟 Ultimate' : '';
    console.log(`🌉 WhatsApp bridge listening on port ${PORT} (mode: ${WHATSAPP_MODE}${ultimateTag})`);
    console.log(`📁 Session stored in: ${SESSION_DIR}`);
    if (ALLOWED_USERS.size > 0) {
      console.log(`🔒 Allowed users: ${Array.from(ALLOWED_USERS).join(', ')}`);
    } else {
      console.log(`⚠️  No WHATSAPP_ALLOWED_USERS set — all messages will be processed`);
    }
    console.log();
    startSocket();
  });
}
