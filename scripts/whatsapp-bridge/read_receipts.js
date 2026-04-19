export function shouldSendReadReceipt(msg, { enabled }) {
  if (!enabled) return false;
  if (!msg?.key) return false;
  if (msg.key.fromMe) return false;
  return true;
}
