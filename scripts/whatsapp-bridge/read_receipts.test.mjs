import test from 'node:test';
import assert from 'node:assert/strict';

import { shouldSendReadReceipt } from './read_receipts.js';

const inboundMsg = { key: { id: 'abc', remoteJid: '19175395595@s.whatsapp.net', fromMe: false } };
const outboundMsg = { key: { id: 'xyz', remoteJid: '19175395595@s.whatsapp.net', fromMe: true } };

test('shouldSendReadReceipt returns true for inbound messages when enabled', () => {
  assert.equal(shouldSendReadReceipt(inboundMsg, { enabled: true }), true);
});

test('shouldSendReadReceipt returns false when feature is disabled', () => {
  assert.equal(shouldSendReadReceipt(inboundMsg, { enabled: false }), false);
});

test('shouldSendReadReceipt returns false for fromMe messages regardless of enabled flag', () => {
  assert.equal(shouldSendReadReceipt(outboundMsg, { enabled: true }), false);
});

test('shouldSendReadReceipt returns false for malformed messages without a key', () => {
  assert.equal(shouldSendReadReceipt({}, { enabled: true }), false);
  assert.equal(shouldSendReadReceipt(null, { enabled: true }), false);
});
